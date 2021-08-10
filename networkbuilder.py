'''
Created on 5.4.2019, modified 4.3.2020, 18.11.2020, 2.1.2021
# coding: utf-8
@author: petrileskinen
'''

import logging
import multiprocessing
import networkx as nx
import numpy as np
import sys
import time
from typing import Dict, List, Set, Tuple, Type, Union

import networkfunctions as fnx
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from sklearn.preprocessing import MinMaxScaler

LOGGER  = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(levelname)-8s [%(filename)s: line %(lineno)d]:\t%(message)s', datefmt='%m-%d %H:%M'))
out_hdlr.setLevel(logging.DEBUG)

IDSET: str = '<ID_SET>'


class NetworkBuilder:
    CYTOSCAPE: str   = 'cytoscape'
    GRAPHML: str     = 'graphml'

    DEPTH_MAX: int   = 30

    def query(self, opts: Dict) -> Dict:
        if opts.log_level:
            LOGGER.setLevel(opts.log_level)

        t0 = time.time()
        
        if opts.id:
            #   if opts.id is provided, query a egocentric network
            nodes, links = self.egocentric(opts)
        else:
            #   otherwise a sampled, sociocentric network
            nodes, links = self.sociocentric(opts)
        # LOGGER.debug('1: {} sec.'.format(time.time()-t0))

        G = self.generateGraph([{'id': n} for n in nodes], links, opts)
        # LOGGER.debug('2: {} sec.'.format(time.time()-t0))

        # self.__debugGraph(G)
        self.densifyGraph(G, opts.limit)
        # LOGGER.debug('3: {} sec.'.format(time.time()-t0))

        # self.__debugGraph(G)
        node_data, metrics = self.getGraphDetails(G, opts)
        # LOGGER.debug('4: {} sec.'.format(time.time()-t0))

        #   if optimize>1, removed nodes causing trouble
        try:
            #   attach calculated data to network nodes
            for ob in node_data:
                n = ob.get('id')
                if n:
                    for k,v in ob.items():
                        if k!='id':
                            G.nodes[n][k] = v
                else:
                    LOGGER.debug("No 'id' found for {}".format(ob))
        except Exception as e:
            LOGGER.error("{} occured".format(e))
            LOGGER.error("{}".format(node_data))
            raise e
        
        '''
        Check if coordinates need adjusting based on ?_x or ?_y result value
        '''
        for _,v in G.nodes(data=True):
            if ('_x' in v.keys() or '_y' in v.keys()):
                LOGGER.debug("self.adjustPositions")
                self.adjustPositions(G)
                break

        if opts.format == NetworkBuilder.GRAPHML:
            # Choose graphml as the return format
            res = '\n'.join(nx.generate_graphml(G, prettyprint=True))
        else:
            # JSON for cytoscape as the return format
            res = nx.readwrite.json_graph.cytoscape_data(G)
            res['metrics'] = metrics
        
        return res

    def egocentric(self, opts: Dict) -> Tuple[Union[List, Set], Dict]:
        """
        Construct the network by sequential BFSearches
        """
        #   start node(s)
        nodes = opts.id.split(' ')

        limit = int(opts.optimize*opts.limit)
        LOGGER.debug("Limit set to {}".format(limit))

        t0 = time.time()
        # no more than DEPTH_MAX steps:
        for i in range(self.DEPTH_MAX):

            node_list = ' '.join(["<{}>".format(n) for n in nodes])
            query = opts.links.replace('<ID>', node_list)

            #if not 'LIMIT' in query:
            #    query += " LIMIT {}".format(self.__optimizedLimit(opts))
            
            links = self.makeSparqlQuery(opts.prefixes+' '+query, opts.endpoint, opts.customHttpHeaders)
            LOGGER.debug("Queried {} links".format(len(links)))
            #   grow source nodes with the previous result
            n0 = len(nodes)
            nodes = self.__uniqueNodesFromLinks(links)
            LOGGER.debug('Depth: {}, links {}, nodes {}, {:.4f} sec.'.format(i+1, len(links), len(nodes), time.time()-t0))
            
            #   make at least 2 queries to received nodes further
            if len(nodes)>=limit or len(nodes)==n0:
                LOGGER.debug('Breaking.')
                break

        #   no resulting links, show the center node itself
        if len(nodes)==0:
            nodes = [opts.id]

        return nodes, links


    def sociocentric(self, opts: Dict) -> Tuple[Set, Dict]:

        limit = self.__optimizedLimit(opts)
        query = "{} {} LIMIT {}".format(opts.prefixes, opts.links, limit)
        links = self.makeSparqlQuery(query, opts.endpoint, opts.customHttpHeaders)

        if len(links)<1:
            LOGGER.debug("No links found")
            return [], []

        LOGGER.debug("{} links found".format(len(links)))

        return self.__uniqueNodesFromLinks(links), links

    def generateGraph(self, nodes: Dict, links: Dict, opts: Dict) -> (nx.Graph):

        G = nx.DiGraph()

        #    get all other fields except 'id' in nodes,
        #    e.g. queried parameters in SELECT ?label ?gender ...:
        node_keys = set([key for ob in nodes for key in ob.keys()]) - set(['id'])

        for ob in nodes:
            _id = ob['id']
            G.add_node(_id)
            for key in node_keys:
                v = ob.get(key)
                if v:
                    G.nodes[_id][key] = v

        #    get all other fields except 'source' and 'target' in nodes,
        #    e.g. queried parameters in SELECT ?x ?y ...:
        edge_keys = set([key for ob in links for key in ob.keys()]) - set(['source', 'target'])

        for ob in links:
            src, trg = ob['source'], ob['target']

            if G.has_edge(trg, src) and opts.removeMultipleLinks:
                continue
            
            G.add_edge(src, trg)

            #   add query results:
            for key in edge_keys:
                v = ob.get(key)
                if v:
                    G.edges[src, trg][key] = v

        return G


    def getGraphDetails(self, G: (nx.Graph), opts: Dict) -> List[Dict]:
        '''
        1) Fetch the node metadata by the opts.nodes query
        2) Calculate the network metrics, 
            - in/out_degrees for nodes
            - pagerank for nodes
            - diameter, number_of_edges, number_connected_components, average_degree', number_of_nodes, number_of_nodes for the entire graph
        '''

        manager, lock = multiprocessing.Manager(), multiprocessing.Lock()

        node_values = manager.dict([(n, manager.dict(id=n)) for n in G.nodes()])
        #for n in G.nodes():
        #    node_values[n] = manager.dict()
        #    node_values[n]['id'] = n

        metrics = manager.dict()

        ids = ' '.join(['<{}>'.format(x) for x in G.nodes()])
        processes = [
            multiprocessing.Process(target=self.getNodesForPeople,
                                     args=(opts.prefixes+opts.nodes,
                                           opts.endpoint, ids, node_values,
                                           opts.customHttpHeaders, lock)),
            multiprocessing.Process(target=self.pagerankGraph,
                                     args=(G, node_values, 0.85, lock)),
            multiprocessing.Process(target=self.degreesGraph,
                                     args=(G, node_values, lock)),
            multiprocessing.Process(target=self.graphMetrics,
                                     args=(G, metrics, lock))
            ]
        
        if opts.id:
            #    distances in egocentric network
            processes.append(multiprocessing.Process(target=self.distancesGraph,
                                     args=(G, opts.id, node_values, lock)))
        
        for p in processes:
            p.start()

        for p in processes:
            p.join()

        return [dict(v) for _,v in node_values.items()], dict([ (k,v) for k,v in metrics.items() ] )



    def densifyGraph(self, G: (nx.Graph), limit: int) -> None:
        '''
        Densify the graph by removing
        - small connected components
        - low-degree nodes at the edge of network 
        '''
        #    remove small connected components
        wcc = sorted(nx.weakly_connected_components(G),
                     key=len, reverse=True)
        count = 0
        for c in wcc:
            if count<limit:
                count += len(c)
            else:
                G.remove_nodes_from(c)

        #    trim low degree nodes
        n = G.number_of_nodes()
        iters = 0
        
        while n > limit and iters<20:
            # Remove low degree nodes in a couple of batches:
            arr = sorted([(k,v) for k,v in G.degree(weight=None)], key = lambda x: x[1])
            
            m = min(n-limit, limit)
            arr = [k for k,_ in arr[:m]]
            
            G.remove_nodes_from(arr)
            n = G.number_of_nodes()
            iters += 1
            LOGGER.debug("Currently {} nodes at step {}.".format(n, iters))
            # self.printGraph(G)


    def __uniqueNodesFromLinks(self, links: Dict) -> Set:
        '''
        returns an unique set of nodes as sources and targets of links
        '''
        return set([n['source'] for n in links]) | set([n['target'] for n in links])


    def pagerankGraph(self, G: (nx.Graph), dct, alpha: float=0.85, lock=None) -> None:
        '''
        Calculates pagerank metric for each node
        '''
        t0 = time.time()
        ans = nx.pagerank(G, alpha=alpha)
        self.__writeProperty(dct, ans.items(), 'pagerank', lock)
        # LOGGER.debug('pagerankGraph: {} sec.'.format(time.time()-t0))



    def distancesGraph(self, G: (nx.Graph), source: str, dct: Dict, lock=None) -> None:
        '''
        Calculates paths lengths from 'ego' to each 'alter' node in an egocentric network
        '''
        if source in G:
            ans = fnx.distances(G, source) # ans = nx.shortest_path_length(G.to_undirected(), source=source)
            self.__writeProperty(dct, ans.items(), 'distance', lock)
        else:
            LOGGER.debug("Source node '{}' not in graph, check the queries".format(source))


    def degreesGraph(self, G: (nx.Graph), dct: Dict, lock=None) -> None:
        '''
        Calculates node degree values, (degree, in and out degree, all both weighted and unweighted)
        '''
        t0 =time.time()
        self.__writeProperty(dct, fnx.degree(G, weight=None), 'degree', lock)
        self.__writeProperty(dct, fnx.in_degree(G, weight=None), 'in_degree', lock)
        self.__writeProperty(dct, fnx.out_degree(G, weight=None), 'out_degree', lock)

        self.__writeProperty(dct, fnx.degree(G, weight='weight'), 'degree_weighted', lock)
        self.__writeProperty(dct, fnx.in_degree(G, weight='weight'), 'in_degree_weighted', lock)
        self.__writeProperty(dct, fnx.out_degree(G, weight='weight'), 'out_degree_weighted', lock)
        # LOGGER.debug('degreesGraph: {} sec.'.format(time.time()-t0))


    def graphMetrics(self, G: (nx.Graph), metrics: Dict, lock=None) -> None:
        '''
        Calculate general network metrics, e.g. diameter, number_of_edges, number_connected_components, average_degree', number_of_nodes, number_of_nodes 
        '''
        t0 = time.time()
        if len(G.nodes())==0 or len(G.edges)==0:
            return

        avd = 2*len(G.edges())/len(G.nodes())

        #    connected components
        Gu = G.to_undirected()
        cc = list(nx.connected_components(Gu))
        ncc = len(cc)

        #    largest connected component
        Gcc = Gu.subgraph(max(cc, key=len)).copy()

        d = nx.diameter(Gcc)

        lock.acquire()
        m = metrics
        m['diameter'] = d
        m['number_connected_components'] = ncc
        m['average_degree'] = avd
        m['number_of_nodes'] = G.number_of_nodes()
        m['number_of_edges'] = G.number_of_edges()
        
        metrics = m
        lock.release()

        # LOGGER.debug('graphMetrics: {} sec.'.format(time.time()-t0))

    def __debugGraph(self, G) -> None:
        LOGGER.debug('nodes {}'.format(len(G.nodes())))
        LOGGER.debug('edges {}'.format(len(G.edges())))


    def getNodesForPeople(self, query, endpoint, ids, dct, customHttpHeaders=None, lock=None) -> None:

        t0= time.time()
        q = query.replace("<ID_SET>", ids)
        
        arr = self.makeSparqlQuery(q, endpoint, customHttpHeaders)
        # LOGGER.debug('1. getNodesForPeople: {} sec.'.format(time.time()-t0))
        lock.acquire()
        for ob in arr:
            n = ob['id']
            dct[n] = {**dct[n], **ob} # nn
        lock.release()
        # LOGGER.debug('2. getNodesForPeople: {} sec.'.format(time.time()-t0))
    '''
    DEBUG    [networkbuilder.py: line 350]:	1. getNodesForPeople: 0.8707551956176758 sec.
    DEBUG    [networkbuilder.py: line 359]:	2. getNodesForPeople: 2.7612321376800537 sec.
    '''

    def __writeProperty(self, dct, ans, prop, lock) -> None:
        '''
        Write values to multiprocessing result
        '''
        lock.acquire()
        for k,v in ans:
            dd = dct[k]
            dd[prop] = v
            dct[k] = dd
        lock.release()

    def __init__(self) -> None:
        pass

        
    def adjustPositions(self, G: (nx.Graph), pos: Dict = None, iters: Tuple[int,int] = (10,10)) -> Dict:
        '''
        Adjust x and y coordinates of the nodes if ?x or ?y are found in the sparql query result set.
        '''
        for coord, newcoord in [('_x', 'x'), ('_y', 'y')]:
            dct = dict([(k, v.get(coord)) for k,v in G.nodes(data=True) if v.get(coord)])
            if len(dct):
                coord_scaler = MinMaxScaler(feature_range=(-1,1))
            
                data = list(dct.values())
                sdata = coord_scaler.fit_transform(np.reshape(np.array(data), (-1, 1)))
                for k,s in zip(dct.keys(), sdata):
                    G.nodes[k][newcoord] = s[0]

        for _ in range(iters[0]):
            #   adjust layout
            pos = nx.drawing.layout.fruchterman_reingold_layout(G, iterations=iters[1], pos = pos)
            
            #   force fixed points
            for k,v in G.nodes(data=True):
                pos[k][0] = v.get('x', pos[k][0])
                pos[k][1] = v.get('y', pos[k][1])

        for k,_ in G.nodes(data=True):
            G.nodes[k]['x'] = pos[k][0]
            G.nodes[k]['y'] = pos[k][1]
        
        return pos

    def __optimizedLimit(self, opts: Dict) -> int:
        return int(opts.optimize*opts.limit)
    
    def makeSparqlQuery(self, query: str, endpoint: str, customHttpHeaders: Dict = None) -> List[Dict]:
        sparql = SPARQLWrapper(endpoint)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)
        
        if customHttpHeaders:
            for k,v in customHttpHeaders.items():
                sparql.addCustomHttpHeader(k,v)
        
        try:
            results = sparql.query().convert()
        except Exception as e:
            raise e
        
        data = []
        for result in results["results"]["bindings"]:
            ob = {}
            for k,v in result.items():
                #   convert common datatypes:
                if v.get('datatype') == 'http://www.w3.org/2001/XMLSchema#decimal':
                    ob[k] = float(v['value'])
                elif v.get('datatype') == 'http://www.w3.org/2001/XMLSchema#integer':
                    ob[k] = int(v['value'])
                # NB. this does not export correctly to cytoscape format:
                # elif v.get('datatype') == 'http://www.w3.org/2001/XMLSchema#date':
                #    ob[k] = datetime.datetime.strptime(v['value'], '%Y-%m-%d').date()
                else:
                    ob[k] = str(v['value'])
            data.append(ob)

        return data

'''
class QueryParams():
    def __init__(self, endpoint, nodes, links,
                prefixes=' ',
                limit=1000,
                id = None,
                optimize = 1.0,
                format = NetworkBuilder.CYTOSCAPE,
                log_level = 10, # "DEBUG"
                removeMultipleLinks = True,
                customHttpHeaders = None):
        self.endpoint: str = endpoint
        self.prefixes: str = prefixes
        self.nodes: str = nodes
        self.links: str = links
        self.limit:int = int(limit)
        self.id:str = id
        self.optimize:float = float(optimize)
        self.format:str = format
        self.removeMultipleLinks:bool = removeMultipleLinks
        self.customHttpHeaders = customHttpHeaders
        self.log_level:Union(int, str) = log_level
        self.adjust_layout:bool = False
'''

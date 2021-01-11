'''
Created on 5.4.2019, modified 4.3.2020, 18.11.2020, 2.1.2021
# coding: utf-8
@author: petrileskinen
'''

import  logging
import  multiprocessing
import  networkx as nx
import numpy as np
import sys

import networkfunctions as fnx
from SPARQLWrapper import SPARQLWrapper, JSON, POST
from sklearn.preprocessing import MinMaxScaler

LOGGER  = logging.getLogger(__name__)
out_hdlr = logging.StreamHandler(sys.stdout)
out_hdlr.setFormatter(logging.Formatter('%(levelname)-8s [%(filename)s: line %(lineno)d]:\t%(message)s', datefmt='%m-%d %H:%M'))
out_hdlr.setLevel(logging.DEBUG)

IDSET = '<ID_SET>'


class NetworkBuilder:
    CYTOSCAPE   = 'cytoscape'
    GRAPHML     = 'graphml'

    def query(self, opts):
        if opts.log_level:
            LOGGER.setLevel(opts.log_level)

        if opts.id:
            #   if opts.id is provided, query a egocentric network
            nodes, links = self.egocentric(opts)
        else:
            #   otherwise a sampled network
            nodes, links = self.sociocentric(opts)

        G = self.generateGraph([{'id': n} for n in nodes], links, opts)

        self.__debugGraph(G)
        self.densifyGraph(G, opts.limit)

        self.__debugGraph(G)
        node_data, metrics = self.getGraphDetails(G, opts)

        #   if optimize>1, removed nodes causing trouble
        try:
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

            res = '\n'.join(nx.generate_graphml(G, prettyprint=True))

        else:

            res = nx.readwrite.json_graph.cytoscape_data(G)
            res['metrics'] = metrics

        return res

    """
    Find the network by sequential BFSearches
    """
    def egocentric(self, opts):

        #   start node(s)
        nodes = opts.id.split(' ')

        limit = int(opts.optimize*opts.limit)
        LOGGER.debug("Limit set to {}".format(limit))

        for i in range(30):
            node_list = ' '.join(["<{}>".format(n) for n in nodes])
            query = opts.links.replace('<ID>', node_list)

            links = self.makeSparqlQuery(opts.prefixes+' '+query, opts.endpoint, opts.customHttpHeaders)

            #   grow source nodes with the previous result
            n0 = len(nodes)
            nodes = self.__uniqueNodesFromLinks(links)
            LOGGER.debug('Depth: {}, nodes {}, limit {}.'.format(i+1, len(nodes), limit))
            
            #   make at least 2 queries to received nodes further
            if len(nodes)>=limit or len(nodes)==n0:
                LOGGER.debug('Breaking.')
                break

        #   no resulting links, show the center node itself
        if len(nodes)==0:
            nodes = [opts.id]

        return nodes, links


    def sociocentric(self, opts):

        limit = int(opts.optimize*opts.limit)
        # query = opts.prefixes +' '+ opts.links + " LIMIT {}".format(limit)
        query = "{} {} LIMIT {}".format(opts.prefixes, opts.links, limit)
        links = self.makeSparqlQuery(query, opts.endpoint, opts.customHttpHeaders)

        if len(links)<1:
            LOGGER.debug("No links found")
            return [], []

        LOGGER.debug("{} links found".format(len(links)))

        return self.__uniqueNodesFromLinks(links), links


    def generateGraph(self, nodes, links, opts):

        G = nx.DiGraph()

        #    get all other fields except 'id' in nodes,
        #    e.g. queried parameters in SELECT ?label ?gender ...:
        node_keys = set([key for ob in nodes for key in ob.keys()]) - set(['id'])

        for ob in nodes:
            _id = ob['id']
            G.add_node(_id)
            for key in node_keys:
                if key in ob:
                    G.nodes[_id][key] = ob[key]

        #    get all other fields except 'source' and 'target' in nodes,
        #    e.g. queried parameters in SELECT ?x ?y ...:
        edge_keys = set([key for ob in links for key in ob.keys()]) - set(['source', 'target'])


        for ob in links:
            src = ob['source']
            trg = ob['target']
            if G.has_edge(trg, src) and opts.removeMultipleLinks:
                continue

            G.add_edge(src, trg)
            for key in edge_keys:
                if key in ob:
                    G.edges[src, trg][key] = ob[key]

        return G

    def getGraphDetails(self, G, opts):
        ids = ' '.join(['<{}>'.format(x) for x in G.nodes()])

        manager = multiprocessing.Manager()
        lock = multiprocessing.Lock()

        node_values = manager.dict()
        for n in G.nodes():
            node_values[n] = manager.dict()
            node_values[n]['id'] = n

        metrics = manager.dict()


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
        '''
        
        '''
        if opts.id:
            #    distances in egocentric network
            processes.append(multiprocessing.Process(target=self.distancesGraph,
                                     args=(G, opts.id, node_values, lock)))
        
        for p in processes:
            p.start()

        for p in processes:
            p.join()

        return [dict(v) for _,v in node_values.items()], dict([ (k,v) for k,v in metrics.items() ] )



    def densifyGraph(self, G, limit):
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
            arr = sorted([(k,v) for k,v in G.degree(weight='weight')], key = lambda x: x[1])
            
            m = min(n-limit, limit)
            arr = [k for k,_ in arr[:m]]
            
            G.remove_nodes_from(arr)
            n = G.number_of_nodes()
            iters += 1
            LOGGER.debug("Currently {} nodes at step {}.".format(n, iters))
            # self.printGraph(G)


    #   return an unique set of nodes as sources and targets of links
    def __uniqueNodesFromLinks(self, links):
        return set([n['source'] for n in links]) | set([n['target'] for n in links])

    def pagerankGraph(self, G, dct, alpha=0.85, lock=None):
        ans = nx.pagerank(G, alpha=alpha)
        self.__writeProperty(dct, ans.items(), 'pagerank', lock)

    def distancesGraph(self, G, source, dct, lock=None):
        if source in G:
            ans = fnx.distances(G, source) # ans = nx.shortest_path_length(G.to_undirected(), source=source)
            self.__writeProperty(dct, ans.items(), 'distance', lock)
        else:
            LOGGER.debug("Source node '{}' not in graph, check the queries".format(source))

    def degreesGraph(self, G, dct, lock=None):
        self.__writeProperty(dct, fnx.degree(G), 'degree', lock)
        self.__writeProperty(dct, fnx.in_degree(G), 'in_degree', lock)
        self.__writeProperty(dct, fnx.out_degree(G), 'out_degree', lock)
    
    def __writeProperty(self, dct, ans, prop, lock):
        lock.acquire()
        for k,v in ans:
            dd = dct[k]
            dd[prop] = v
            dct[k] = dd
        lock.release()


    def graphMetrics(self, G, metrics, lock=None):

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

    def __debugGraph(self, G):
        LOGGER.debug('nodes {}'.format(len(G.nodes())))
        LOGGER.debug('edges {}'.format(len(G.edges())))


    def getNodesForPeople(self, query, endpoint, ids, dct, customHttpHeaders=None, lock=None):

        q = query.replace("<ID_SET>", ids)
        # LOGGER.debug(q)

        arr = self.makeSparqlQuery(q, endpoint, customHttpHeaders)

        for ob in arr:
            n = ob['id']
            lock.acquire()
            nn = dct[n]
            for k,v in ob.items():
                nn[k] = v

            dct[n] = nn
            lock.release()


    def __init__(self):
        pass

        
    def adjustPositions(self, G, pos = None, iters = (10,10)):
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


    def makeSparqlQuery(self, query, endpoint, customHttpHeaders=None):
        sparql = SPARQLWrapper(endpoint)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)
        # LOGGER.debug(query)
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
                if v.get('datatype') == 'http://www.w3.org/2001/XMLSchema#decimal':
                    ob[k] = float(v['value'])
                elif v.get('datatype') == 'http://www.w3.org/2001/XMLSchema#integer':
                    ob[k] = int(v['value'])

                # this does not export correctly to cytoscape format:
                #elif v.get('datatype') == 'http://www.w3.org/2001/XMLSchema#date':
                #    ob[k] = datetime.datetime.strptime(v['value'], '%Y-%m-%d').date()

                else:
                    ob[k] = str(v['value'])
            data.append(ob)
        return data


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
        self.endpoint = endpoint
        self.prefixes = prefixes
        self.nodes = nodes
        self.links = links
        self.limit = int(limit)
        self.id = id
        self.optimize = float(optimize)
        self.format = format
        self.removeMultipleLinks = removeMultipleLinks
        self.customHttpHeaders = customHttpHeaders
        self.log_level = log_level
        self.adjust_layout = False

'''
Created on 5.4.2019, modified 6.11.2019
# coding: utf-8
@author: petrileskinen
'''

import  logging
import  multiprocessing 
import  networkx as nx

from SPARQLWrapper import SPARQLWrapper, JSON, POST


LOGGER  = logging.getLogger(__name__)
IDSET   = '<ID_SET>'


class NetworkBuilder:
    CYTOSCAPE = 'cytoscape'
    GRAPHML = 'graphml'
    
    def query(self, opts):
        if opts.id:
            nodes, links = self.egocentric(opts)
        else:
            nodes, links = self.sociocentric(opts)
        
        G = self.generateGraph([{'id': n} for n in nodes], links)
        
        self.__debugGraph(G)
        self.densifyGraph(G, opts.limit)
        
        self.__debugGraph(G)
        node_data, metrics = self.getGraphDetails(G, opts)
        
        for ob in node_data:
            n = ob['id']
            for k,v in ob.items():
                if k!='id':
                    G.nodes[n][k] = v
        
        
        if opts.format == NetworkBuilder.GRAPHML:
            
            res = '\n'.join(nx.generate_graphml(G, prettyprint=True))
            
        else:
            
            res = nx.readwrite.json_graph.cytoscape_data(G) 
            res['metrics'] = metrics
            
        return res
    
    
    def egocentric(self, opts):
        
        nodes = [opts.id]
        limit = int(opts.optimize*opts.limit)
        LOGGER.debug("Limit set to {}".format(limit))
        
        for i in range(30):
            node_list = ' '.join(["<{}>".format(n) for n in nodes])
            query = opts.links.replace('<ID>', node_list)
            
            links = self.makeSparqlQuery(opts.prefixes+query, opts.endpoint)
            
            n0 = len(nodes)
            nodes = self.__uniqueNodesFromLinks(links)
            LOGGER.debug('depth: {}, nodes {}'.format(i+1, len(nodes)))
            
            if len(nodes)>=limit or len(nodes)==n0:
                break
        
        return nodes, links
        
    
    
    def sociocentric(self, opts):
        
        limit = int(opts.optimize*opts.limit)
        query = opts.prefixes + opts.links + " LIMIT {}".format(limit)
        
        links = self.makeSparqlQuery(query, opts.endpoint)
        
        if len(links)<1:
            LOGGER.debug("No links found")
            return
        LOGGER.debug("{} links found".format(len(links)))
        
        nodes = self.__uniqueNodesFromLinks(links)
        
        return nodes, links
    
        
    
    def generateGraph(self, nodes, links):
    
        G = nx.DiGraph()
        
        #    get all other fields except 'id' in nodes,
        #    e.g. queried parameters in SELECT ?x ?y ...:
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
            node_values[n]=manager.dict()
            node_values[n]['id'] = n
        
        metrics = manager.dict()
        
        
        processes = [
            multiprocessing.Process(target=self.__getNodesForPeople, 
                                     args=(opts.prefixes+opts.nodes, 
                                           opts.endpoint, ids, node_values, lock)),
            multiprocessing.Process(target=self.pagerankGraph, 
                                     args=(G, node_values, 0.85, lock)),
            multiprocessing.Process(target=self.degreesGraph, 
                                     args=(G, node_values, lock)),
            multiprocessing.Process(target=self.graphMetrics, 
                                     args=(G, metrics, lock))
            #multiprocessing.Process(target=self.layoutGraph, 
            #                         args=(G, node_values, 500, lock)),
                    ]
        
        if opts.id is not None:
            #    distances in egocentric network
            processes.append(multiprocessing.Process(target=self.distancesGraph, 
                                     args=(G, opts.id, node_values, lock)))
        
        
        for p in processes:
            p.start()
        
        for p in processes:
            p.join()
        
        
        return [dict(v) for _,v in node_values.items()], dict([ (k,v) for k,v in metrics.items() ] )
    
    """
    def createGraph(self, nodes, links):
        G = nx.DiGraph()
        G.add_nodes_from(nodes)
        G.add_edges_from(links)
        return G
    """
    
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
        n = len(G.nodes())
        iters = 0
        while n > limit and iters<30:
            
            mindeg = min(dict(G.degree()).values())
            arr = [node for node,degree in dict(G.degree()).items() if degree==mindeg]
            
            arr = arr[:n-limit]
            G.remove_nodes_from(arr)
            n = len(G.nodes())
            iters += 1
            # self.printGraph(G)
    
    
    def __uniqueNodesFromLinks(self, links):
        return set([n['source'] for n in links]) | set([n['target'] for n in links])
    
    
    """
    def __getNodeInfo(self, nodes, opts, N=2500):
        if len(nodes)>N:
            return self.__getNodeInfo(list(nodes)[:N], opts) + self.__getNodeInfo(list(nodes)[N:], opts)
        
        node_ids    = ' '.join(["<{}>".format(n) for n in nodes])
        node_query  = opts.nodes.replace(IDSET, node_ids)
        
        nodes = self.makeSparqlQuery(opts.prefixes+node_query, opts.endpoint)
        LOGGER.debug("{} nodes queried".format(len(nodes)))
        return nodes 

    def layoutGraph(self, G, dct, iterations=500, lock=None):
        
        ans = nx.kamada_kawai_layout(G)
        
        scale = 80*(G.number_of_nodes()**0.6)
        lock.acquire()
        
        for k,[x,y] in ans.items():
            dct[k]['x'] = scale*x
            dct[k]['y'] = scale*y
        lock.release()
        # print("Layout process ready")
    """
    
    def pagerankGraph(self, G, dct, alpha=0.85, lock=None):
        ans = nx.pagerank(G, alpha=alpha)
        lock.acquire()
        for k,v in ans.items():
            dct[k]['pagerank'] = v
        lock.release()
        
    
    def distancesGraph(self, G, source, dct, lock=None):
        ans = nx.shortest_path_length(G, source=source)
        lock.acquire()
        for k,v in ans.items():
            dct[k]['distance'] = v
        lock.release()
    
    
    def degreesGraph(self, G, dct, lock=None):
        lock.acquire()
        for k,v in G.in_degree():
            dct[k]['in_degree'] = v
        lock.release()
    
        lock.acquire()
        for k,v in G.out_degree():
            dct[k]['out_degree'] = v
        lock.release()
        # print("degreesGraph process ready")
    
    def graphMetrics(self, G, metrics, lock=None):
        
        avd = 2*len(G.edges())/len(G.nodes())
        
        #    connected components
        Gu = G.to_undirected()
        cc = list(nx.connected_components(Gu))
        ncc = len(cc)

        #    largest connected component
        Gcc = Gu.subgraph(max(cc, key=len)).copy()
        
        d = nx.diameter(Gcc)
        
        lock.acquire()
        metrics['diameter'] = d
        metrics['number_connected_components']  = ncc
        metrics['average_degree']      = avd
        lock.release()
    
    
    def __debugGraph(self, G):
        LOGGER.debug('nodes {}'.format(len(G.nodes())))
        LOGGER.debug('edges {}'.format(len(G.edges())))
        
    def __printGraph(self, G):
        print('nodes',len(G.nodes()))
        print('edges',len(G.edges()))
    
    
    def __getNodesForPeople(self, query, endpoint, ids, dct, lock):
        q = query.replace("<ID_SET>", ids)
        arr = self.makeSparqlQuery(q, endpoint)
        
        lock.acquire()
        for ob in arr:
            n = ob['id']
            for k,v in ob.items():
                if k!='id':
                    dct[n][k] = v
        lock.release()
    
    def __init__(self):
        pass
    
    
    def makeSparqlQuery(self, query, endpoint):
        sparql = SPARQLWrapper(endpoint)
        sparql.setQuery(query)
        sparql.setMethod(POST)
        sparql.setReturnFormat(JSON)
        sparql.addCustomHttpHeader("Authorization", "Basic c2Vjbzpsb2dvczAz")
        #    'User-Agent': 'OpenAnything/1.0 +http://diveintopython.org/http_web_services/'
        sparql.addCustomHttpHeader("User-Agent", "OpenAnything/1.0 +http://diveintopython.org/http_web_services/")
        
        results = sparql.query().convert()
        
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
    def __init__(self, endpoint, nodes, links, prefixes=" ", limit=1000, id = None, 
                 optimize = 1.0, format = NetworkBuilder.CYTOSCAPE):
        self.endpoint = endpoint
        self.prefixes = prefixes
        self.nodes = nodes
        self.links = links
        self.limit = int(limit)
        self.id = id 
        self.optimize = float(optimize)
        self.format = format
        

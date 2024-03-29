'''
Created 23.8.2020
# coding: utf-8
@author: petrileskinen
'''
import networkx as nx
from typing import Dict

def degree(G, weight: str='weight') -> Dict:
    ''' return degrees of nodes in graph G. '''
    return G.degree(weight=weight)

def in_degree(G, weight: str='weight') -> Dict:
    ''' return in-degrees of nodes in graph G. '''
    return G.in_degree(weight=weight)

def out_degree(G, weight: str='weight') -> Dict:
    ''' return out-degrees of nodes in graph G. '''
    return G.out_degree(weight=weight)

def distances(G, source: str) -> Dict:
    ''' return distances from source to all other nodes in graph G. '''
    return nx.shortest_path_length(G.to_undirected(), source=source)

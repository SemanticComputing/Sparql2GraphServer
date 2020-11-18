'''
Created on 18.11.2020
# coding: utf-8
@author: petrileskinen
'''

import logging
# import  multiprocessing
# import  networkx as nx

from networkbuilder import QueryParams
import networkfunctions as fnx
from SPARQLWrapper import SPARQLWrapper, JSON, POST

LOGGER  = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(levelname)-8s [%(filename)s: line %(lineno)d]:\t%(message)s',
                    datefmt='%m-%d %H:%M')

# IDSET = '<ID_SET>'


class NetworkSignature:
    # CYTOSCAPE   = 'cytoscape'
    # GRAPHML     = 'graphml'

    def query(self, opts):
        return dict(series=self.__dummyresult())

    def __dummyresult(self):
        return [{'data': [(1, '0.312'), (2, '0.229'), (3, '0.125'), (4, '0.042'), (5, '0.042'), (6, '0.021'), (7, '0.021'), (8, '0.021'), (9, '0.021'), (10, '0.021'), (11, '0.021'), (12, '0.021'), (13, '0.021'), (14, '0.021'), (15, '0.021'), (16, '0.021'), (17, '0.021')], 'name': '1593–1604'}, {'data': [(1, '0.361'), (2, '0.109'), (3, '0.059'), (4, '0.059'), (5, '0.054'), (6, '0.050'), (7, '0.035'), (8, '0.030'), (9, '0.025'), (10, '0.025'), (11, '0.025'), (12, '0.015'), (13, '0.015'), (14, '0.010'), (15, '0.010'), (16, '0.010'), (17, '0.010'), (18, '0.010'), (19, '0.010'), (20, '0.005')], 'name': '1604–1614'}, {'data': [(1, '0.209'), (2, '0.170'), (3, '0.130'), (4, '0.102'), (5, '0.040'), (6, '0.040'), (7, '0.025'), (8, '0.020'), (9, '0.017'), (10, '0.012'), (11, '0.012'), (12, '0.012'), (13, '0.010'), (14, '0.010'), (15, '0.010'), (16, '0.010'), (17, '0.010'), (18, '0.007'), (19, '0.007'), (20, '0.005')], 'name': '1614–1624'}, {'data': [(1, '0.322'), (2, '0.227'), (3, '0.047'), (4, '0.041'), (5, '0.041'), (6, '0.024'), (7, '0.020'), (8, '0.019'), (9, '0.018'), (10, '0.018'), (11, '0.015'), (12, '0.014'), (13, '0.012'), (14, '0.012'), (15, '0.011'), (16, '0.011'), (17, '0.009'), (18, '0.009'), (19, '0.008'), (20, '0.007')], 'name': '1624–1635'}, {'data': [(1, '0.199'), (2, '0.175'), (3, '0.128'), (4, '0.106'), (5, '0.037'), (6, '0.033'), (7, '0.032'), (8, '0.030'), (9, '0.025'), (10, '0.023'), (11, '0.016'), (12, '0.012'), (13, '0.012'), (14, '0.012'), (15, '0.012'), (16, '0.009'), (17, '0.007'), (18, '0.007'), (19, '0.006'), (20, '0.006')], 'name': '1635–1645'}]


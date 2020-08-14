'''
Created on 6 Nov 2019
@author: petrileskinen
'''

import logging
import sys
from networkbuilder import *
from testQueries import *
from authorization import AUTHORIZATION_HEADER

ENDPOINT = "https://ldf.fi/yoma/sparql"
NBFENDPOINT = "http://ldf.fi/nbf/sparql"
WIKIENDPOINT = "https://query.wikidata.org/sparql"

LOGGER  = logging.getLogger(__name__)
logging.basicConfig(level='DEBUG',
                    format='%(levelname)-8s [%(filename)s: line %(lineno)d]:\t%(message)s')


def main(args):
    
    nb = NetworkBuilder()
    
    q = QueryParams(endpoint = ENDPOINT,
              prefixes = getprefixes(),
              nodes = getNodeInfo(),
              links = getRelativeLinks(),
              limit = 100,
              optimize = 1.5,
              customHttpHeaders = AUTHORIZATION_HEADER,
              id = "http://ldf.fi/yoma/people/p660")
    LOGGER.info("Test quering an egocentric network")
    _ = nb.query(q)
    
    
    q = QueryParams(endpoint = ENDPOINT,
              prefixes = getprefixes(),
              nodes = getNodeInfo(),
              links = getSociolinks(),
              limit = 100,
              customHttpHeaders = AUTHORIZATION_HEADER,
              optimize = 2.5)
    LOGGER.info("Test quering a sociocentric network")
    res = nb.query(q)
    print()
    print(res)
    
    q = QueryParams(endpoint = ENDPOINT,
              prefixes = getprefixes(),
              nodes = getNodeInfo(),
              links = getSociolinks(),
              limit = 20,
              customHttpHeaders = AUTHORIZATION_HEADER,
              optimize = 1.5,
              format = "graphml")
    LOGGER.info("Test quering graphml")
    res = nb.query(q)
    print()
    print(res)

def testWikidata(args):
    nb = NetworkBuilder()
    
    q = QueryParams(endpoint = WIKIENDPOINT,
              prefixes = wikiprefixes,
              nodes = wikinodes,
              links = wikilinks,
              limit = 50,
              optimize = 1.5)
    LOGGER.info("Test quering a sociocentric network")
    res = nb.query(q)
    print()
    print(res)


if __name__ == '__main__':
    main(sys.argv)
    
    
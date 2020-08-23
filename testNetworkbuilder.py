'''
Created on 6 Nov 2019, 23 Aug 2020
@author: petrileskinen
'''

import argparse
import json
import logging
import requests
import sys

from networkbuilder import *
from testQueries import *
from authorization import AUTHORIZATION_HEADER

ENDPOINT = "https://ldf.fi/yoma/sparql"
NBFENDPOINT = "http://ldf.fi/nbf/sparql"
WIKIENDPOINT = "https://query.wikidata.org/sparql"



def main(args):

    parser = argparse.ArgumentParser()
    
    parser.add_argument('-l', '--links', type=str, required = True,
                        help='Sparql query for link information')
    
    parser.add_argument('-n', '--nodes', type=str, required = True,
                        help='Sparql query for node information')
    
    parser.add_argument('-p', '--prefices', type=str, required = True,
                        help='Sparql query for prefices')
    
    parser.add_argument('-e', '--endpoint', type=str,
                        default="http://ldf.fi/emlo/sparql", help='Sparql query endpoint')
    
    parser.add_argument('-i', '--id', type=str, required = False,
                        help='Id for egocentric network')
    
    parser.add_argument('--limit', type=int, 
                        default=1000, help='Max. number of results')
    
    parser.add_argument('--optimize', type=float, 
                        default=1.5, help='Optimize')
    
    parser.add_argument('--nosave', nargs='?', type=bool, 
                    help="Don't save output files, for faster testing",
                    const=True, default=False)

    parser.add_argument('--log-level',
                    default='INFO',
                    dest='log_level',
                    type=log_level_string_to_int,
                    nargs='?',
                    help='Set the logging output level. {0}'.format(LOG_LEVEL_STRINGS))
    

    opts = parser.parse_args()

    LOGGER.setLevel(opts.log_level)
    logging.basicConfig(level=opts.log_level,
                    format='%(levelname)-8s [%(filename)s: line %(lineno)d]:\t%(message)s')
    
    LOGGER.debug("Test quering an egocentric network")

    nb = NetworkBuilder()
    
    q = QueryParams(endpoint = opts.endpoint,
              prefixes = loadQuery(opts.prefices),
              nodes = loadQuery(opts.nodes),
              links = loadQuery(opts.links),
              limit = opts.limit,
              optimize = opts.optimize,
              customHttpHeaders = AUTHORIZATION_HEADER,
              log_level = opts.log_level,
              id = opts.id)
    
    res = nb.query(q)
    
    LOGGER.info(json.dumps(res, indent=4, sort_keys=True))


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

def loadQuery(file):
    f = open(file, 'r')
    res = f.readlines()
    f.close()
    LOGGER.debug("Query loaded from {}".format(file))
    return ''.join(res)

#    source; https://www.fun4jimmy.com/2015/09/15/configuring-pythons-logging-module-with-argparse.html
LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']

def log_level_string_to_int(log_level_string):
    log_level_string = log_level_string.upper()
    if not log_level_string in LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(log_level_string, LOG_LEVEL_STRINGS)
        raise argparse.ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)
    # check the logging log_level_choices have not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


if __name__ == '__main__':
    main(sys.argv)
    
    
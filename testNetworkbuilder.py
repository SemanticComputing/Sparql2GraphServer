'''
Created on 6 Nov 2019

@author: petrileskinen
'''

import logging
import sys
from networkbuilder import *

ENDPOINT = "https://ldf.fi/yoma/sparql"
NBFENDPOINT = "http://ldf.fi/nbf/sparql"

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
              id = "http://ldf.fi/yoma/p660")
    LOGGER.info("Test quering an egocentric network")
    _ = nb.query(q)
    
    
    q = QueryParams(endpoint = ENDPOINT,
              prefixes = getprefixes(),
              nodes = getNodeInfo(),
              links = getSociolinks(),
              limit = 100,
              optimize = 2.5)
    LOGGER.info("Test quering a sociocentric network")
    res = nb.query(q)
    print()
    print(res)






def getprefixes():
    return """
PREFIX bioc: <http://ldf.fi/schema/bioc/>
PREFIX dct: <http://purl.org/dc/terms/> 
PREFIX foaf: <http://xmlns.com/foaf/0.1/>
PREFIX gvp: <http://vocab.getty.edu/ontology#> 
PREFIX label: <http://ldf.fi/yoma/label/> 
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> 
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
PREFIX rels:  <http://ldf.fi/yoma/relations/> 
PREFIX skos: <http://www.w3.org/2004/02/skos/core#> 
PREFIX schema: <http://schema.org/>
PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#>
PREFIX : <http://ldf.fi/yoma/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX ammo: <http://ldf.fi/ammo/> """

def getRelativeLinks():
    return """SELECT DISTINCT ?source ?target ?label (1 as ?weight) WHERE {
  VALUES ?id { <ID> }
  
  { ?id bioc:has_family_relation [ bioc:inheres_in ?target ; a ?rel ] . BIND(?id AS ?source) }
  UNION
  { ?source bioc:has_family_relation [ bioc:inheres_in ?id ; a ?rel ] . BIND(?id AS ?target) }
  
  OPTIONAL { ?rel skos:prefLabel ?label . FILTER(LANG(?label)='en') }
} """

def getNodeInfo():
    return """SELECT DISTINCT ?id ?name ?cls ?gender ?birthdate WHERE {
  VALUES ?cls { foaf:Person :ReferencedPerson }
    VALUES ?id { <ID_SET> }
    ?id a ?cls ; skos:prefLabel ?name . 
    
    OPTIONAL { ?id schema:gender/skos:prefLabel ?gender . FILTER (lang(?gender)="fi") }
  OPTIONAL { ?id :has_birth/schema:date/gvp:estStart ?birthdate . BIND (year(?birthdate) AS ?birthyear) }
} """


def getSociolinks():
    return """
SELECT DISTINCT ?source ?target ?name (1 as ?weight) WHERE {
  
  ?source bioc:has_family_relation [ bioc:inheres_in ?target ; a ?rel ] ;
          :has_title/:related_occupation ammo:kappalainen .
  ?target :has_title/:related_occupation ammo:kappalainen .
  OPTIONAL { ?rel skos:prefLabel ?name . FILTER(LANG(?name)='fi') }
}  """

if __name__ == '__main__':
    
    main(sys.argv)
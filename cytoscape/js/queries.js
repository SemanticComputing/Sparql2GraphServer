var id_url = "http://ldf.fi/yoma/p660";

var endpoint = "https://ldf.fi/yoma/sparql";

var prefixes= "PREFIX bioc: <http://ldf.fi/schema/bioc/> \
	PREFIX dct: <http://purl.org/dc/terms/> \
	PREFIX foaf: <http://xmlns.com/foaf/0.1/> \
	PREFIX gvp: <http://vocab.getty.edu/ontology\#> \
	PREFIX label: <http://ldf.fi/yoma/label/> \
	PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> \
	PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> \
	PREFIX rels:  <http://ldf.fi/yoma/relations/> \
	PREFIX skos: <http://www.w3.org/2004/02/skos/core#> \
	PREFIX schema: <http://schema.org/> \
	PREFIX skosxl: <http://www.w3.org/2008/05/skos-xl#> \
	PREFIX : <http://ldf.fi/yoma/> \
	PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> \
	PREFIX ammo: <http://ldf.fi/ammo/> ";

var link_query = "SELECT DISTINCT ?source ?target ?label (1 as ?weight) WHERE {\
			  VALUES ?id { <ID> } \
			  { ?id bioc:has_family_relation [ bioc:inheres_in ?target ; a ?rel ] . BIND(?id AS ?source) }\
			  UNION\
			  { ?source bioc:has_family_relation [ bioc:inheres_in ?id ; a ?rel ] . BIND(?id AS ?target) }\
			  OPTIONAL { ?rel skos:prefLabel ?label . FILTER(LANG(?label)='en') }\
			} ";

var node_query = "SELECT DISTINCT ?id ?name ?cls ?gender ?birthdate WHERE {\
		  VALUES ?cls { foaf:Person :ReferencedPerson }\
		    VALUES ?id { <ID_SET> }\
		    ?id a ?cls ; skos:prefLabel ?name . \
		    \
		    OPTIONAL { ?id schema:gender/skos:prefLabel ?gender . FILTER (lang(?gender)='fi') } \
		    OPTIONAL { ?id :has_birth/schema:date/gvp:estStart ?birthdate . BIND (year(?birthdate) AS ?birthyear) }} ";

var limit = 100;
var optimize = 2.0;


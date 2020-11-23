# Sparql2GraphServer
Server code for performing a SPARQL query for social network, and output it in a JSON format suitable for [cytoscape.js](https://js.cytoscape.org/)

start localhost http://127.0.0.1:5000/ with:
```sh
export FLASK_APP=app/routes.py
flask run
```
Required POST (or GET) query parameters:

| parameter | description | |
| ------ | ------ | ------ |
| links | SPARQL query, [example](https://version.aalto.fi/gitlab/seco/hy-matrikkeli/raw/master/queries/relation_links1640.sparql), has to return values **?source** and **?target** | required |
| nodes | SPARQL query, [example](https://version.aalto.fi/gitlab/seco/hy-matrikkeli/raw/master/queries/relation_nodes.sparql), <ID_SET> is filled automatically, has to return value **?id** | required |
| endpoint | Server endpoint | required |
| id | Resource url, if provided, returns a egocentric network | optional, default None |
| prefixes | SPARQL prefixes, for shortening the nodes and links parameters | optional, default "" |
| limit | Limit the number of links | optional, default 1000 |
| format | Output format: 'cytoscape' or 'graphml' | default 'cytoscape'|
| optimize | First performs a query with optimize*limit results, and then densifies the network. | optional, default 1.0 |
| removeMultipleLinks | show only one link between nodes | optional, default True |
| customHttpHeaders | Headers, e.g. 'Authorization', of the query | optional, default None |

Returns JSON with fields *elements* for input to cytoscape.js, and *metrics* currently containing network metrics of average degree, diameter, and number of connected components.

Simple HTML demo with plain javascript in folder *cytoscape*.

Python 3.8.0
requirements.txt

## Docker

Build:

`docker build -t sparql2graphserver .`

Run:

`docker run -it --rm -p 5000:5000 sparql2graphserver`

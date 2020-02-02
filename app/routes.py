from app    import app
from flask  import jsonify, request, Response
from flask_cors import CORS, cross_origin
# import  logging

from networkbuilder import *
nb = NetworkBuilder()

# LOGGER = logging.getLogger(__name__)

@app.route('/')
@app.route('/query', methods=['GET', 'POST'])
def queryGraph():
    
    if request.method == "POST":
        data = request.json
    else:
        data = request.args.to_dict(flat=False)
    
    try:
        res = nb.query(QueryParams(**data))
    
    except Exception as e:
        # LOGGER.info("Error '{}' occured".format(e))
        return Response({'error: {}'.format(str(e))}, status=403, mimetype='application/json')
    
    response = jsonify(res)
    
    return response

@app.route('/')
@app.route('/graphml', methods=['GET', 'POST'])
def queryGraphML():
    
    if request.method == "POST":
        data = request.json
    else:
        data = request.args.to_dict(flat=False)
    
    try:
        dct = {**data, **{'format':NetworkBuilder.GRAPHML}}
        LOGGER.debug("{}".format(dct))
        res = nb.query(QueryParams(**dct))
    
    except Exception as e: #    mimetype='text/xml')
        return Response({'error: {}'.format(str(e))}, status=403, mimetype='text/xml')
    
    response = Response(res, mimetype='text/xml')
    
    return response



@app.after_request
def add_cors_headers(response):

    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Headers', 'Cache-Control')
    response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')
    response.headers.add('Access-Control-Allow-Headers', 'Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
    
    return response

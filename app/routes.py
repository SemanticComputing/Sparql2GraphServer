from app    import app
from flask  import jsonify, request, Response
from flask_cors import CORS, cross_origin

from networkbuilder import NetworkBuilder, LOGGER
from queryParams import QueryParams
nb = NetworkBuilder()

from networkSignature import NetworkSignature
ns = NetworkSignature()


@app.route('/')
@app.route('/query', methods=['GET', 'POST'])
def queryGraph():
    if request.method == "POST":
        data = request.json
    else:
        data = request.args.to_dict(flat=False)
    
    res = None

    try:
        res = nb.query(QueryParams(**data))
    
    except Exception as e:
        return Response({'error: {}'.format(str(e))}, status=403, mimetype='application/json')
    
    response = jsonify(res)
    
    return response

@app.route('/')
@app.route('/query_ego', methods=['GET', 'POST'])
def queryGraphEgo():
    if request.method == "POST":
        data = request.json
    else:
        data = request.args.to_dict(flat=False)
    
    res = None

    try:
        res = nb.query_ego(QueryParams(**data))
    
    except Exception as e:
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


@app.route('/')
@app.route('/signature', methods=['GET', 'POST'])
def querySignature():
    if request.method == "POST":
        data = request.json
    else:
        data = request.args.to_dict(flat=False)

    try:
        res = ns.query(QueryParams(**data))
    except Exception as e:
        return Response({'error: {}'.format(str(e))}, status=403, mimetype='text/xml')
    
    return jsonify(res)

@app.route('/health')
def health_check():
    return 'OK', 200

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

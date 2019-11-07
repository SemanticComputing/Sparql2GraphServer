from app    import app
from flask  import jsonify, request, Response
from flask_cors import CORS, cross_origin

from networkbuilder import *
nb = NetworkBuilder()


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
        return Response({'error: {}'.format(str(e))}, status=403, mimetype='application/json')
    
    response = jsonify(res)
    
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

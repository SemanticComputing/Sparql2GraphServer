from flask import Flask
from flask_cors import CORS, cross_origin


app = Flask(__name__)
cors = CORS(app)

from app import routes



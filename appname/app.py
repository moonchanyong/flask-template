from appname import monkey_patch
# monkeypatch library
monkey_patch.patch_all()

from flask import Flask, jsonify
from flask_restful_swagger_2 import Api
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
from mongoengine import connect
from appname import auth, error, config, \
        kakao, facebook, apitools, example-aws-s3, example-aws-ses, example-aws-iot
import os
from flask_restful.reqparse import Argument

app = Flask(__name__)
# cors ploblem
cors = CORS(app, supports_credentials=True)
api = Api(app, api_version='0.1', api_spec_url='/api/swagger')

# set app.config
app.config.from_object(config.DefaultConfig)

if 'CI' in os.environ:
    app.config.from_object(config.CiConfig)
elif 'TEST' in os.environ:
    app.config.from_object(config.TestConfig)
elif 'DEV_SERVER' in os.environ:
    app.config.from_object(config.DevServerConfig)

# set mongoDB
if 'MONGO_USERNAME' in app.config:
    connect(
        db=app.config['MONGO_DBNAME'],
        host=app.config['MONGO_HOST'],
        port=app.config['MONGO_PORT'],
        username=app.config['MONGO_USERNAME'],
        password=app.config['MONGO_PWD'])
else:
    connect(
        app.config['MONGO_DBNAME'],
        host=app.config['MONGO_HOST'],
        port=app.config['MONGO_PORT'])

# set swagger
swaggerui_bp = get_swaggerui_blueprint(
    '/api/docs',
    '/api/swagger.json',
    config={
        'app_name': 'appname'
    }
)
app.register_blueprint(swaggerui_bp, url_prefix='/api/docs')

#set custom errorhandler
@app.errorhandler(error.InvalidUsage)
def handle_invalid_usage(err):
    response = jsonify(err.to_dict())
    response.status_code = err.status_code
    return response

apitools.init(app)
apitools.add_resources(api)

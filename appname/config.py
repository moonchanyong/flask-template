import os
from datetime import timedelta

# define configset

class DefaultConfig(object):
    DEBUG = True
    TESTING = True
    # using jwt token you have to set this key
    SECRET_KEY = os.urandom(32)
    # set mongodb
    MONGO_DBNAME = 'example_dbname'
    MONGO_HOST = 'mongodb://exampleUrl'
    MONGO_PORT = 27017
    # set kakao
    KAKAO_API_SERVER = "https://kapi.kakao.com/v1"
    # set facebook
    FACEBOOK_API_SERVER = "https://graph.facebook.com"
    FACEBOOK_APP_ID = "example_id"
    FACEBOOK_APP_SECRET = "example_code"
    # set aws service
    S3_URL = "https://s3.ap-northeast-2.amazonaws.com"
    ATTACHMENT_S3_BUCKET = 'example_bucketname'
    CONTACT_EMAIL = 'example@example.com'
    AWS_SES_REGION = 'us-west-2'

    PASSWORD_RESET_EXPIRE_DURATION = timedelta(minutes=10)

class TestConfig(DefaultConfig):
    TESTING = True
    SECRET_KEY = os.urandom(32)
    MONGO_HOST = 'mongodb://exampleUrl'

class CiConfig(TestConfig):
    DEBUG = False
    TESTING = True
    MONGO_HOST = 'mongodb://exampleUrl'


class DevServerConfig(DefaultConfig):
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', DefaultConfig.SECRET_KEY)
    MONGO_DBNAME = 'example_dbname'
    MONGO_HOST = os.environ.get('MONGO_HOST', None)
    MONGO_PORT = 27017
    MONGO_USERNAME = os.environ.get('MONGO_USERNAME', None)
    MONGO_PWD = os.environ.get('MONGO_PWD', None)


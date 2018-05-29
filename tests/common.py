import unittest
import json
from appname.app import app
from flask.testing import  FlaskClient
from flask import Response as BaseResponse
from werkzeug.utils import cached_property

class Response(BaseResponse):
    @cached_property
    def json(self):
        return json.loads(self.data)

class TestClient(FlaskClient):
    def open(self, *args, **kwargs):
        if 'json' in kwargs:
            kwargs['data'] = json.dumps(kwargs.pop('json'))
            kwargs['content_type'] = 'application/json'
        return super().open(*args, **kwargs)

app.response_class = Response
app.test_client_class = TestClient

class BaseTest(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.client = self.app

    def signup_login(self, email):
        pw = 'asdfsaf'
        rv = self.client.post('/auth/signup',
                json=dict(email=email, pwd=pw))
        self.assertEqual(rv.status_code, 200)
        rv = self.client.post('/auth/login', json=dict(email=email, pwd=pw))
        self.assertEqual(rv.status_code, 200)

        return rv.json


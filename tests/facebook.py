from tests.common import BaseTest
from unittest.mock import Mock, patch
from flask import json
from deepscent.db import UserModel

class FacebookTest(BaseTest):
    def tearDown(self):
        try:
            UserModel.objects.get(email='abcfacebook@abcmart.com').delete()
        except UserModel.DoesNotExist:
            return None

    def test_facebook_login_fail(self):
        with patch('deepscent.facebook.FacebookApi.debug_token') as mock:
            mock.return_value = dict(error=dict(message='error'))
            token = '1idlfawfi'
            rv = self.app.post('/facebook/login', data=dict(facebook_auth_token=token))
            self.assertEqual(rv.status_code, 403)
            mock.return_value = dict(data=dict(
                user_id='1234', is_valid=True, app_id='187908931794227'))
            rv = self.app.post('/facebook/login', data=dict(facebook_auth_token=token))
            self.assertEqual(rv.status_code, 404)

    def test_facebook_login_success(self):
        with patch('deepscent.facebook.FacebookApi.debug_token') as mock:
            mock.return_value = dict(data=dict(
                user_id='12345678', is_valid=True, app_id='187908931794227'))
            UserModel(
                user_id='qwer1234-poiu0987',
                facebook_id='12345678',
                email='abcfacebook@abcmart.com',
                password='abc123!@#'
            ).save()
            token = '1idlfawfi'
            rv = self.app.post('/facebook/login', data=dict(facebook_auth_token=token))
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(rv.json['result'])

    def test_facebook_signup(self):
        facebook_id = '12345678'
        with patch('deepscent.facebook.FacebookApi.debug_token') as mock:
            mock.return_value = dict(data=dict(
                user_id=facebook_id, is_valid=True, app_id='187908931794227'))
            token = '1idlfawfi'
            email = 'abcfacebook@abcmart.com'
            rv = self.app.post("/facebook/signup", data=dict(
                facebook_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 200)

            rv = self.app.post('/facebook/login', data=dict(facebook_auth_token=token))
            self.assertEqual(rv.status_code, 200)

    def test_facebook_signup_duplicated_error(self):
        facebook_id = '12345678'
        token = '1idlfawfi'
        email = 'abcfacebook@abcmart.com'
        with patch('deepscent.facebook.FacebookApi.debug_token') as mock:
            mock.return_value = dict(data=dict(
                user_id=facebook_id, is_valid=True, app_id='187908931794227'))
            rv = self.app.post("/facebook/signup", data=dict(
                facebook_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 200)

            rv = self.app.post("/facebook/signup", data=dict(
                facebook_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 403)

    def test_facebook_signup_authorization_error(self):
        facebook_id = '12345678'
        token = '1idlfawfi'
        email = 'abcfacebook@abcmart.com'
        with patch('deepscent.facebook.FacebookApi.debug_token') as mock:
            mock.return_value = dict(data=dict(
                user_id=facebook_id, is_valid=True, app_id='12345678'))
            rv = self.app.post("/facebook/signup", data=dict(
                facebook_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 403)

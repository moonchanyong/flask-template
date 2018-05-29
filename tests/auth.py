from unittest.mock import patch
from tests.common import BaseTest
from deepscent.db import UserModel, drop_all_collection
from flask import json
from datetime import datetime

class AuthTest(BaseTest):
    def setUp(self):
        super().setUp()
        try:
            UserModel.objects.get(email='abc1@abcmart.com').delete()
            UserModel.objects.get(email='abc2@abcmart.com').delete()
        except UserModel.DoesNotExist:
            pass

    def test_signup_success(self):
        rv = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv.status_code, 200)
        self.assertIsNotNone(UserModel.objects.get(email='abc1@abcmart.com'))

    def test_signup_fail(self):
        rv1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv1.status_code, 200)

        rv2 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='1234567'))
        self.assertEqual(rv2.status_code, 403)

    def test_signup_fail2(self):
        rv1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd=''))
        self.assertEqual(rv1.status_code, 400)

    def test_login_success(self):
        rv_prev = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev.status_code, 200)

        rv = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv.status_code, 200)

    def test_login_fail1(self):
        rv_prev = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev.status_code, 200)

        rv = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefh'))
        self.assertEqual(rv.status_code, 400)

    def test_login_fail2(self):
        rv_prev = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev.status_code, 200)

        rv = self.app.post('/auth/login', data=dict(email='abc2@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv.status_code, 403)

    def test_logout(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        auth_token = json.loads(rv_prev2.data)['auth_token']
        rv = self.app.post('/auth/logout',
                           headers={'Authorization': '{}'.format(auth_token)})
        self.assertEqual(rv.status_code, 200)

        rv_next = self.app.post('/auth/logout',
                                headers={'Authorization': '{}'.format(auth_token)})
        self.assertEqual(rv_next.status_code, 401)

    def test_user_info(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        rv = self.app.get('/auth/user_info',
                          headers={'Authorization': '{}'.format(json.loads(rv_prev2.data)['auth_token'])})
        self.assertEqual(rv.status_code, 200)

        rv_res = json.loads(rv.data)
        self.assertEqual(rv_res['user_info']['email'], 'abc1@abcmart.com')

    def test_other_user_info(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev1 = self.app.post('/auth/signup', data=dict(
            email='abc2@abcmart.com', pwd='abcdefg', name='TestAuthor'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc2@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        rv = self.app.put('/auth/user_info',
                          headers={'Authorization': '{}'.format(json.loads(rv_prev2.data)['auth_token'])},
                          data=dict(picture='profile_image'))
        self.assertEqual(rv.status_code, 200)

        rv = self.app.get('/auth/user_info',
                          headers={'Authorization': '{}'.format(json.loads(rv_prev2.data)['auth_token'])})
        self.assertEqual(rv.status_code, 200)
        other_user_info = json.loads(rv.data)['user_info']
        self.assertEqual(other_user_info['email'], 'abc2@abcmart.com')
        self.assertEqual(other_user_info['name'], 'TestAuthor')
        self.assertEqual(other_user_info['picture'], 'profile_image')
        other_user_id = other_user_info['user_id']

        rv_prev3 = self.app.post('/auth/logout',
                                 headers={'Authorization': '{}'.format(json.loads(rv_prev2.data)['auth_token'])})
        self.assertEqual(rv_prev3.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        rv = self.app.get('/auth/user_info',
                          headers={'Authorization': '{}'.format(json.loads(rv_prev2.data)['auth_token'])},
                          data=dict(user_id=other_user_id))
        self.assertEqual(rv.status_code, 200)

        rv_res = json.loads(rv.data)
        self.assertEqual(rv_res['user_info']['name'], 'TestAuthor')
        self.assertEqual(rv_res['user_info']['picture'], 'profile_image')

    def test_user_info_update(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        headers = {'Authorization': '{}'.format(json.loads(rv_prev2.data)['auth_token'])}
        rv = self.app.put(
                '/auth/user_info',
                headers=headers,
                data=dict(pwd='1234'))
        self.assertEqual(rv.status_code, 200)

        rv = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='1234'))
        self.assertEqual(rv.status_code, 200)

    def test_refresh_token_success(self):
        rv_prev = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev.status_code, 200)

        rv = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv.status_code, 200)

        rv_res = json.loads(rv.data)
        rv_next = self.app.post('/auth/refresh_token',
                                headers={'Authorization': '{}'.format(rv_res['auth_token'])},
                                data=dict(refresh_token=rv_res['refresh_token']))
        self.assertEqual(rv_next.status_code, 200)

        rv_next_res = json.loads(rv_next.data)
        rv_logout = self.app.post('/auth/logout',
                                  headers={'Authorization': '{}'.format(rv_next_res['auth_token'])})
        self.assertEqual(rv_logout.status_code, 200)

    def test_refresh_token_fail(self):
        rv_prev = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev.status_code, 200)

        rv = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv.status_code, 200)

        rv_prev2 = self.app.post('/auth/signup', data=dict(email='abc2@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        rv2 = self.app.post('/auth/login', data=dict(email='abc2@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv2.status_code, 200)

        rv_res = json.loads(rv.data)
        rv2_res = json.loads(rv2.data)

        rv_next = self.app.post('/auth/refresh_token',
                                headers={'Authorization': '{}'.format(rv_res['auth_token'])},
                                data=dict(refresh_token=rv2_res['refresh_token']))

        UserModel.objects.get(email='abc2@abcmart.com').delete()
        self.assertEqual(rv_next.status_code, 401)

    def test_reset_password_not_exists_user(self):
        url = '/auth/reset_password'

        rv = self.app.post(url, data=dict(email='dsfasd@adfds.com'))

        self.assertEqual(rv.status_code, 404)

    def test_reset_password_email_error(self):
        email = 'abc1@abcmart.com'
        rv = self.app.post('/auth/signup', data=dict(email=email, pwd='abcdefg'))
        self.assertEqual(rv.status_code, 200)

        with patch('deepscent.apitools.email_client.send_email') as mock:
            mock.side_effect = Exception()
            rv = self.app.post('/auth/reset_password', data=dict(email=email))
            self.assertEqual(rv.status_code, 500)

    def test_reset_password_succeed(self):
        email = 'abc1@abcmart.com'
        rv = self.app.post('/auth/signup', data=dict(email=email, pwd='abcdefg'))
        self.assertEqual(rv.status_code, 200)

        with patch('deepscent.apitools.email_client.send_email') as mock,\
                patch('deepscent.auth.render_template') as template_mock:
            mock.return_value = None
            rv = self.app.post('/auth/reset_password', data=dict(email=email))
            self.assertEqual(rv.status_code, 200)

            user = UserModel.objects(email=email).get()
            self.assertIsNotNone(user.tmp_password)
            self.assertIsNotNone(user.tmp_password_valid_period)
            self.assertLess(datetime.now(), user.tmp_password_valid_period)

            tmp_pwd = template_mock.call_args[1]['password']

            rv = self.app.post('/auth/login', data=dict(email=email, pwd=tmp_pwd))

            self.assertEqual(rv.status_code, 200)
            self.assertTrue(rv.json['used_tmp_pwd'])

    def test_user_exists(self):
        rv = self.app.get('/user/exists', data=dict(email="abc1@abcmart.com"))
        self.assertEqual(rv.json['exists'], False)


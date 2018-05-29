from tests.common import BaseTest
from unittest.mock import Mock, patch
from flask import json
from deepscent.db import UserModel

class KakaoTest(BaseTest):
    def tearDown(self):
        try:
            UserModel.objects.get(email='abc1@abcmart.com').delete()
        except UserModel.DoesNotExist:
            return None


    def test_kakao_login_failed(self):
        with patch('deepscent.kakao.KakaoApi.access_token_info') as mock:
            mock.return_value = dict(code=400)
            token = '1idlfawfi'
            rv = self.app.post('/kakao/login', data=dict(kakao_auth_token=token))
            self.assertEqual(rv.status_code, 403)
            mock.return_value = dict(id=3143)
            rv = self.app.post('/kakao/login', data=dict(kakao_auth_token=token))
            self.assertEqual(rv.status_code, 404)

    def test_kakao_signup(self):
        kakao_id = '123213'
        with patch('deepscent.kakao.KakaoApi.user_info') as mock:
            mock.return_value = dict(code=400)
            token = '1idlfawfi'
            email = 'abc1@abcmart.com'
            rv = self.app.post("/kakao/signup", data=dict(
                kakao_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 403)
            mock.return_value = dict(
                    id=kakao_id,
                    properties=dict(
                        profile_image="http://dsfdsf",
                        nickname="dsafdsf",
                        thumbnail_image="dsfaf")
                    )
            rv = self.app.post("/kakao/signup", data=dict(
                kakao_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 200)


        with patch('deepscent.kakao.KakaoApi.access_token_info') as mock:
            mock.return_value = dict(id=kakao_id)
            rv = self.app.post('/kakao/login', data=dict(kakao_auth_token=token))
            self.assertEqual(rv.status_code, 200)

    def test_kakao_signup_duplicated_error(self):
        kakao_id = '123123'
        token = '1idlfawfi'
        email = 'abc1@abcmart.com'
        with patch('deepscent.kakao.KakaoApi.user_info') as mock:
            mock.return_value = dict(
                    id=kakao_id,
                    properties=dict(
                        profile_image="http://dsfdsf",
                        nickname="dsafdsf",
                        thumbnail_image="dsfaf")
                    )
            rv = self.app.post("/kakao/signup", data=dict(
                kakao_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 200)

            rv = self.app.post("/kakao/signup", data=dict(
                kakao_auth_token=token,
                email=email))
            self.assertEqual(rv.status_code, 403)

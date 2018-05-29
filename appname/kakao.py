import requests
from flask_restful import Resource
from flask import current_app as app
from appname.error import InvalidUsage
from appname.db import UserModel
from appname.auth import User, signup, signup_responses
from appname.apitools import get_args, spec, ApiParam, \
    ApiResponse, EnumConstraint, Swagger

class KakaoLogin(Resource):
    @spec('/kakao/login', 'Kakao User Login',
            body_params=[
                ApiParam('kakao_auth_token', 'auth token from kakao open sdk',
                    required=True)
            ],
            responses=[
                ApiResponse(200, 'Login Succeed',
                    {
                        'result': True,
                        'auth_token': 'Auth Token',
                        'refresh_token': 'Refresh Token',
                        'exp_time': '2017-12-31T23:59:59'
                    }
                ),
                ApiResponse(404,
                    'User Not Found. Kakao token is valid but no user.',
                    { 'message': 'User Not Found' }),
                ApiResponse(403,
                    'Authorization Failed (from kakao server)',
                    { 'message': 'Authorization Failed' }),
            ]
        )
    def post(self):
        args = get_args()
        kauth_token = args['kakao_auth_token']

        resp = KakaoApi.access_token_info(kauth_token)
        if 'code' in resp:
            raise InvalidUsage("Authroization Failed", 403)
        kakao_id = str(resp['id'])
        try:
            user_model = UserModel.objects.get(kakao_id=kakao_id)
        except UserModel.DoesNotExist:
            raise InvalidUsage("User Not Found", 404)

        user = User()
        user.user_db = user_model
        auth_token, refresh_token, exp_time = user.generate_auth_token()
        user.authenticated = True

        return {
            'result': True,
            'auth_token': auth_token,
            'refresh_token': refresh_token,
            'exp_time': exp_time
        }

class KakaoSignup(Resource):
    @spec('/kakao/signup', 'New User Signup With Kakao',
        body_params=[
            ApiParam('kakao_auth_token',
                'auth token from kakao open sdk',
                required=True),
            ApiParam('email',
                'user email',
                required=True),
            ApiParam('pwd',
                'user password'),
            ApiParam('name',
                'real name'),
            ApiParam('birthday',
                'birthday',
                type='date'),
            ApiParam('gender',
                'gender (male/female)',
                default='',
                constraints=[EnumConstraint(['', 'male', 'female'])]),
            ApiParam('place', 'office or home'),
            ApiParam('space', 'Where Arom will be installed'),
            ApiParam('purpose', 'Why use Arom'),
            ApiParam('prefer_scents', 'Prefer Scents',
                type='array',
                item=ApiParam("item", "item", type="string"))
        ],
        responses=[
            ApiResponse(200, 'User Signup Succeed', dict(result=True)),
            ApiResponse(500, 'User Signup Fail because of DB Issue', {
                    'message': 'ex@example.com signup failed. Try again.'
            }),
            ApiResponse.error(403, 'Authorization Failed (from kakao server)'),
            ApiResponse.error(403, 'Already existing kakao user'),
            *signup_responses,
        ]
    )
    def post(self):
        args = get_args()
        kauth_token = args['kakao_auth_token']

        resp = KakaoApi.user_info(kauth_token)

        if 'code' in resp:
            raise InvalidUsage("Authorization Failed", 403)

        kakao_id = str(resp['id'])
        properties = resp['properties']
        profile_image = properties['profile_image']
        nickname = properties['nickname']
        thumbnail_image = properties['thumbnail_image']

        if UserModel.objects(kakao_id=kakao_id).first() is not None:
            raise InvalidUsage("Already existing kakao user", 403)

        signup(args, random_pw=True, validate_pw=False, kakao_id=kakao_id)

        return {'result': True}
    


class KakaoApi(object):
    @classmethod
    def access_token_info(cls, kauth_token):
        server = app.config['KAKAO_API_SERVER']
        url = "{}/user/access_token_info".format(server)
        headers = {
                "Authorization": "Bearer {}".format(kauth_token)
            }

        resp = requests.get(url, headers=headers).json()
        return resp

    @classmethod
    def user_info(cls, kauth_token):
        server = app.config['KAKAO_API_SERVER']
        url = "{}/user/me".format(server)
        headers = {
                "Authorization": "Bearer {}".format(kauth_token)
            }

        resp = requests.get(url, headers=headers).json()
        return resp


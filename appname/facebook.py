import requests
from flask_restful import Resource
from flask import current_app as app
from appname.error import InvalidUsage
from appname.db import UserModel
from appname.auth import User, signup, signup_responses
from appname.apitools import get_args, spec, ApiParam, \
    ApiResponse, EnumConstraint, Swagger


class FacebookLogin(Resource):
    @spec('/facebook/login', 'Facebook User Login',
        body_params=[
            ApiParam('facebook_auth_token', 'auth token from facebook open sdk',
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
                        'User Not Found. Facebook token is valid but no user.',
                        {'message': 'User Not Found'}),
            ApiResponse(403,
                        'Authorization Failed (from facebook server)',
                        {'message': 'Authorization Failed'}),
        ]
    )
    def post(self):
        args = get_args()
        fbauth_token = args['facebook_auth_token']

        resp = FacebookApi.debug_token(fbauth_token)
        if 'error' in resp or not resp['data']['is_valid'] or \
                resp['data']['app_id'] != app.config['FACEBOOK_APP_ID']:
            raise InvalidUsage("Authroization Failed", 403)
        facebook_id = str(resp['data']['user_id'])
        try:
            user_model = UserModel.objects.get(facebook_id=facebook_id)
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


class FacebookSignup(Resource):
    @spec('/facebook/signup', 'New User Signup With Facebook',
        body_params=[
            ApiParam('facebook_auth_token',
                    'auth token from facebook open sdk',
                    required=True),
            ApiParam('email',
                    'user email',
                    required=True),
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
            ApiResponse.error(403, 'Authorization Failed (from facebook server)'),
            ApiResponse.error(403, 'Already existing facebook user'),
            *signup_responses,
        ]
    )
    def post(self):
        args = get_args()
        fbauth_token = args['facebook_auth_token']

        token_resp = FacebookApi.debug_token(fbauth_token)
        if 'error' in token_resp or not token_resp['data']['is_valid'] or \
                token_resp['data']['app_id'] != app.config['FACEBOOK_APP_ID']:
            raise InvalidUsage("Authroization Failed", 403)
        facebook_id = str(token_resp['data']['user_id'])

        if UserModel.objects(facebook_id=facebook_id).first() is not None:
            raise InvalidUsage("Already existing facebook user", 403)

        signup(args, random_pw=True, validate_pw=False, facebook_id=facebook_id)

        return {'result': True}


class FacebookApi(object):
    @classmethod
    def debug_token(cls, fbauth_token):
        server = app.config['FACEBOOK_API_SERVER']
        app_token_url = "{}/oauth/access_token?client_id={}" \
                        "&client_secret={}&grant_type=client_credentials"\
            .format(server, app.config['FACEBOOK_APP_ID'], app.config['FACEBOOK_APP_SECRET'])
        app_token_json = requests.get(app_token_url).json()
        app_token = app_token_json["access_token"]
        url = "{}/debug_token/?input_token={}&access_token={}".format(
            server, fbauth_token, app_token)
        resp = requests.get(url).json()
        return resp

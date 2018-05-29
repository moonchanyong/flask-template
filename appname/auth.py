import bcrypt
import uuid
import datetime
import jwt
import re
import arrow
import json
import random

from flask import request, g, render_template
from flask import current_app as app
from flask_restful import Resource
from appname.db import UserModel
from appname.error import InvalidUsage
from appname.apitools import get_args, \
    spec, ApiParam, ApiResponse, Swagger,\
    EnumConstraint, LengthConstraint
import appname.apitools as apitools
from mongoengine.queryset.visitor import Q
from email_validator import validate_email


token_example = {
    'auth_token': 'Auth Token',
    'refresh_token': 'Refresh Token',
    'exp_time': '2017-12-31T23:59:59'
}

pwd_words = []
def gen_pwd():
    global pwd_words
    if len(pwd_words) == 0:
        with open('words.txt') as f:
            pwd_words = f.readlines()

    words = [random.choice(pwd_words).strip() for i in range(4)]
    words[random.randint(0, 3)] = str(random.randint(0, 999))
    return "-".join(words)

class User(object):
    def __init__(self, email=None, pwd=None, user_id=None, authenticated=False):
        self.email = email
        self.pwd = pwd
        self.authenticated = authenticated

        self.user_db = None
        if user_id is not None:
            try:
                self.user_db = UserModel.objects.get(user_id=user_id)
            except UserModel.DoesNotExist:
                self.user_db = None
        elif email is not None:
            try:
                self.user_db = UserModel.objects.get(email=email)
            except UserModel.DoesNotExist:
                self.user_db = None

    def is_user(self):
        return self.user_db and self.user_db.email == self.email

    def check_pwd(self, pwd):
        if not self.user_db.password:
            return False
        return bcrypt.checkpw(
                pwd.encode('utf-8'),
                self.user_db.password.encode('utf-8'))

    def check_tmp_pwd(self, pwd):
        if not self.user_db.tmp_password:
            return False
        return bcrypt.checkpw(
                pwd.encode('utf-8'),
                self.user_db.tmp_password.encode('utf-8'))

    def is_expired_tmp_pwd(self):
        valid_period = self.user_db.tmp_password_valid_period
        if valid_period:
            return valid_period <= datetime.datetime.now()
        return False


    def is_authenticated(self):
        return self.authenticated

    def generate_auth_token(self):
        exp_time = datetime.datetime.utcnow() + datetime.timedelta(days=0, hours=6)
        iat_time = datetime.datetime.utcnow()
        payload = {
            'exp': exp_time,
            'iat': iat_time,
            'sub': self.user_db.user_id
        }
        refresh_payload = {
            'iat': iat_time,
            'sub': self.user_db.user_id
        }
        auth_token = jwt.encode(
            payload,
            app.config['SECRET_KEY'],
            algorithm='HS512'
        ).decode()
        refresh_token = jwt.encode(
            refresh_payload,
            app.config['SECRET_KEY'],
            algorithm='HS256'
        ).decode()
        self.user_db.update(set__auth_token=auth_token, set__refresh_token=refresh_token)
        self.user_db.reload()
        return auth_token, refresh_token, str(arrow.get(exp_time))

def check_auth(func):
    def new_func(*args, **kwargs):
        auth_token = request.headers.get('authorization')
        if auth_token:
            auth_token = auth_token.encode()
            try:
                user_id = jwt.decode(auth_token, app.config['SECRET_KEY'], algorithms='HS512')['sub']
            except jwt.ExpiredSignatureError:
                raise InvalidUsage('Auth Token was expired. Try Again for refresh token.', status_code=401)
            except Exception:
                raise InvalidUsage('Auth Token is invalid.', status_code=401)
            try:
                user_db = UserModel.objects.get(user_id=user_id)
            except UserModel.DoesNotExist:
                raise InvalidUsage('This user does not exist.', status_code=401)

            if user_db.auth_token and auth_token == user_db.auth_token.encode():
                g.user = User(user_db.email, authenticated=True)
                return func(*args, **kwargs)
            else:
                raise InvalidUsage('Auth Token is invalid. Try Again.', status_code=401)
        else:
            raise InvalidUsage('Auth Token is not found. Try Again.', status_code=401)

    new_func._original = func
    new_func.__name__ = func.__name__
    return new_func


def hash_pwd(pwd):
    return bcrypt.hashpw(pwd.encode('utf-8'), bcrypt.gensalt()).decode()

def signup(user_info, random_pw=False, validate_pw=True, kakao_id=None, facebook_id=None):
    email = user_info.get('email').lower()
    pwd = user_info.get('pwd')
    name = user_info.get('name')
    birthday = user_info.get('birthday')
    gender = user_info.get('gender')

    place = user_info.get('place')
    space = user_info.get('space')
    purpose = user_info.get('purpose')

    prefer_scents = user_info.get('prefer_scents')


    if email is None:
        raise InvalidUsage("Email is required", status_code=400)

    try:
        validate_email(email, check_deliverability=False)
    except:
        raise InvalidUsage("Email is not valid", status_code=403)


    if pwd is None:
        if random_pw:
            pwd = str(uuid.uuid4())
        else:
            raise InvalidUsage("Password is requied", status_code=400)

    if validate_pw:
        pattern = r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[`\-=\\\[\];',\./~!@#$%^&*\(\)_\+|\{\}:\"<>\?])" \
                  r"[A-Za-z\d`\-=\\\[\];',\./~!@#$%^&*\(\)_\+|\{\}:\"<>\?]{8,}$"
        if not re.match(pattern, pwd):
            raise InvalidUsage("Password is not secure one", status_code=400)

    if UserModel.objects(Q(email=email)).first() is not None:
        err = email + ' already exists.'
        raise InvalidUsage(err, status_code=403)

    UserModel(
        user_id=str(uuid.uuid4()),
        kakao_id=kakao_id,
        facebook_id=facebook_id,
        email=email,
        password=hash_pwd(pwd),
        name=name,
        birthday=birthday,
        gender=gender,
        place=place,
        space=space,
        purpose=purpose,
        prefer_scents=prefer_scents
    ).save()


    try:
        user = UserModel.objects.get(email=email)
    except UserModel.DoesNotExist:
        err = email + ' signup failed. Try again.'
        raise InvalidUsage(err, status_code=500)




signup_responses = [
    ApiResponse.error(400, "Password is required"),
    ApiResponse.error(400, "Email is required"),
    ApiResponse.error(400, "Password is not secure one"),
    ApiResponse.error(403, "abc1@abcmart.com already exists"),
    ApiResponse.error(403, "Email is not valid")
]

response_example = dict(
    user_id='User ID',
    email='User E-Mail',
    name='User Name',
    birthday='2017-12-31T23:59:59',
    gender='Female',
    picture='User Profile Picture img_src',
    devices={'Device ID': 'Device Name'}
)

class UserInfo(Resource):
    @spec('/auth/user_info', 'Get User Info',
        header_params=[*Swagger.Params.Authorization],
        query_params=[
            ApiParam('user_id', 'user_id to find user')
        ],
        responses=[
            ApiResponse(200, 'User Information', {
                    'user_info': response_example
            }),
            ApiResponse(401, 'Get User Info Fail because of Auth Issue', {
                'message': 'Auth Token is not found.'
            }),
            ApiResponse(404, 'Get User Info Fail because User Does Not Exist', {
                'message': 'User does not exist.'
            }),
            ApiResponse(406, 'Get User Info Fail because of DB Issue', {
                'message': 'User Info cannot be found. Try Again.'
            })
    ])
    @check_auth
    def get(self):
        args = get_args()
        if args.get('user_id', None):
            try:
                user_db = UserModel.objects.get(user_id=args.get('user_id'))
            except UserModel.doesNotExist:
                raise InvalidUsage('User does not exist.', status_code=404)

            return dict(
                user_info=dict(
                    name=user_db.name,
                    picture=user_db.picture
                ))
        else:
            user = g.user.user_db
            return dict(user_info=user.marshall())

    @spec('/auth/user_info', 'Update User Info',
        header_params=[
            *Swagger.Params.Authorization
        ],
        body_params=[
            ApiParam('pwd',
                'user password',
                constraints=[LengthConstraint(4)]),
            ApiParam('name',
                'real name',
                constraints=[LengthConstraint(1)]),
            ApiParam('birthday',
                'birthday',
                type='date-time'),
            ApiParam('gender',
                'gender (male/female)',
                default='',
                constraints=[EnumConstraint(['', 'male', 'female'])]),
            ApiParam('picture', 'profile image')
        ],
        responses=[
            ApiResponse(200, 'User Information', {
                    'user_info': response_example
            }),
            ApiResponse(401, 'Put User Info Fail because of Auth Issue', {
                'message': 'Auth Token is not found.'
            }),
            ApiResponse(406, 'Put User Info Fail because of DB Issue', {
                'message': 'User Info cannot be found. Try Again.'
            })
    ])
    @check_auth
    def put(self):
        args = get_args()
        user = g.user.user_db

        if args.get('pwd', None):
            user.password = hash_pwd(args.get('pwd'))
        if args.get('name', None):
            user.name = args.get('name')
        if args.get('birthday', None):
            user.birthday = arrow.get(args.get('birthday')).datetime
        if args.get('gender', None):
            user.gender = args.get('gender')
        if args.get('picture', None):
            user.picture = args.get('picture')

        user.save()

        return dict(user_info=user.marshall())


class Signup(Resource):
    @spec('/auth/signup', 'New User Signup',
        body_params=[
            ApiParam('email',
                'user email',
                required=True,
                constraints=[LengthConstraint(5, 100)]),
            ApiParam('pwd',
                'user password',
                required=True,
                constraints=[LengthConstraint(4)]),
            ApiParam('name',
                'real name',
                constraints=[LengthConstraint(1)]),
            ApiParam('birthday',
                'birthday',
                type='date-time'),
            ApiParam('gender',
                'gender (male/female)',
                constraints=[EnumConstraint(['male', 'female'])]),
            ApiParam('place', 'office or home'),
            ApiParam('space', 'Where Arom will be installed'),
            ApiParam('purpose', 'Why use Arom'),
            ApiParam('prefer_scents', 'Prefer Scents',
                type='array',
                item=ApiParam("item", "item", type="string"))
        ],
        responses=[
            ApiResponse(200, 'User Signup Succeed', dict(result=True)),
            *signup_responses,
            ApiResponse(500, 'User Signup Fail because of DB Issue', {
                'message': 'ex@example.com signup failed. Try again.'
            })
        ]
    )
    def post(self):
        args = get_args()

        signup(args, random_pw=False, validate_pw=not app.config['TESTING'])

        return dict(result=True)

class Login(Resource):
    @spec('/auth/login', 'User Login',
        body_params=[
            ApiParam('email',
                'user email', required=True,
                constraints=[LengthConstraint(5, 100)]),
            ApiParam('pwd',
                'user password', required=True,
                constraints=[LengthConstraint(4)]),
        ],
        responses=[
            ApiResponse(200, 'Login Succeed', token_example),
            ApiResponse(403, 'User Login Fail because email not signed up',
                {'message': 'ex@example.com is not signed up user.'}
            ),
            ApiResponse(400, 'User Login Fail because email/pwd invalid',
                {'message': 'Password is invalid.'}
            ),
            ApiResponse.error(406, 'Expired Temporary Password')
        ]
    )
    def post(self):
        args = get_args()
        email = args['email'].lower()
        pwd = args['pwd']

        user = User(email, pwd=pwd)

        if not user.is_user():
            err = email + ' is not signed up user.'
            raise InvalidUsage(err, status_code=403)

        is_tmp_pwd = user.check_tmp_pwd(pwd)
        if not user.check_pwd(pwd) and not is_tmp_pwd:
            err = 'Password is invalid.'
            raise InvalidUsage(err, status_code=400)
        
        if is_tmp_pwd and user.is_expired_tmp_pwd():
            err = 'Expired Temporary Password'
            raise InvalidUsage(err, status_code=406)

        auth_token, refresh_token, exp_time = user.generate_auth_token()
        user.authenticated = True

        result = {
            'auth_token': auth_token,
            'refresh_token': refresh_token,
            'exp_time': exp_time
        }

        if is_tmp_pwd:
            result['used_tmp_pwd'] = is_tmp_pwd


        return result

class Logout(Resource):
    @spec('/auth/logout', 'User Logout',
        header_params=[*Swagger.Params.Authorization],
        responses=[
            ApiResponse(200, 'User Logout Success', dict(result=True)),
            ApiResponse(401, 'User Logout Fail because of Auth Issue',
                        {'message': 'Auth Token is not found.'}),
            ApiResponse(500, 'User Logout Fail because of DB Issue',
                        {'message': 'Token does not deleted. Try Again.'}),
        ]
    )
    @check_auth
    def post(self):
        g.user.user_db.update(unset__auth_token=1)
        if g.user.user_db.access_token:
            g.user.user_db.update(unset__access_token=1)
        g.user.user_db.reload()
        if g.user.user_db.auth_token or g.user.user_db.access_token:
            raise InvalidUsage('Token does not deleted. Try Again.', status_code=500)
        g.user.authenticated = False

        return dict(result=True)

class RefreshAuthToken(Resource):
    @spec(
        '/auth/refresh_token',
        'Refresh User Auth Token and User Refresh Token',
        body_params=[
            ApiParam('refresh_token', 'refresh token for user', required=True)
        ],
        responses=[
            ApiResponse(200, 'Refresh Auth Token Success', token_example),
            ApiResponse(401, 'Refresh Auth Token Failed',
                        dict(message='Refresh Token failed'))
        ]
    )
    def post(self):
        args = get_args()
        auth_token = request.headers.get('authorization')
        refresh_token = args['refresh_token']

        if auth_token and refresh_token:
            auth_token = auth_token.encode()
            refresh_token = refresh_token.encode()
            try:
                user_id = jwt.decode(auth_token,
                                     app.config['SECRET_KEY'],
                                     algorithms='HS512',
                                     options=dict(verify_exp=False)
                                     )['sub']
            except jwt.InvalidTokenError:
                raise InvalidUsage('Auth Token is invalid.', status_code=401)

            try:
                user_db = UserModel.objects.get(user_id=user_id)
            except UserModel.DoesNotExist:
                raise InvalidUsage('This user does not exist.', status_code=401)

            if refresh_token == user_db.refresh_token.encode():
                user = User(user_db.email, user_id=user_id)
                auth_token, refresh_token, exp_time = user.generate_auth_token()
                return {'auth_token': auth_token, 'refresh_token': refresh_token, 'exp_time': exp_time}
            else:
                raise InvalidUsage('Refresh Token is invalid.', status_code=401)
        else:
            raise InvalidUsage('Token is not found.', status_code=401)

class ResetPassword(Resource):
    @spec(
        '/auth/reset_password',
        'Request reset password mail',
        body_params=[
            ApiParam('email', 'email to reset password', required=True)
        ],
        responses=[
            ApiResponse(200, 'Email sent', dict(result=True)),
            ApiResponse.error(404, 'User not found'),
            ApiResponse.error(500, 'Email Server Error')
        ]
    )
    def post(self):
        args = get_args()
        user_model = UserModel.objects(email=args['email']).first()
        if user_model is None:
            raise InvalidUsage('User not found', 404)

        tmp_password = gen_pwd()

        body = render_template(
            "pwd_reset_mail.template.html",
            name=user_model.name,
            password=tmp_password)

        try:
            charset = 'UTF-8'
            response = apitools.email_client.send_email(
                Destination={
                    'ToAddresses': [
                        user_model.email
                    ]
                },
                Message=dict(
                    Subject=dict(
                        Data="[아롬] 임시 비밀번호 발급",
                        Charset='utf8'),
                    Body=dict(Html=dict(Charset='utf8', Data=str(body)))
                ),
                Source=app.config['CONTACT_EMAIL'])
        except Exception as ex:
            raise InvalidUsage("Email Server Error: {}".format(ex), 500)

        user_model.tmp_password = hash_pwd(tmp_password)
        user_model.tmp_password_valid_period = datetime.datetime.now() + \
                app.config['PASSWORD_RESET_EXPIRE_DURATION']
        user_model.save()
        
        return dict(result=True)

class UserExists(Resource):
    @spec(
        '/user/exists',
        'Check whether user exists or not',
        query_params=[
            ApiParam('email', 'email to find user', required=True)
        ],
        responses=[
            ApiResponse(200, 'User presence', dict(exists=True))
        ]
    )
    def get(self):
        args = get_args()
        user_model = UserModel.objects(email=args['email'].lower()).first()
        if user_model is None:
            return dict(exists=False)

        return dict(exists=True)

class TokenValidation(Resource):
    @spec(
        '/auth/tokenvalidate',
        'Check whether token is valid or not',
        header_params=[*Swagger.Params.Authorization],
        responses=[
            ApiResponse(200, 'Token Validation Success', dict(result=True)),
            ApiResponse(401, 'Token is not Valid ',
                        {'message': 'Auth Token is not valid.'}),
            ApiResponse(500, 'Tocken Validate Fail because of DB Issue',
                        {'message': 'Token does not deleted. Try Again.'}),
        ]
    )
    @check_auth
    def get(self):
   
      return dict(result=True)

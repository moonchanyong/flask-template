import uuid
import datetime
import time
from flask import current_app as app
from boto3 import client
from flask import json, g
from flask_restful import Resource
from mongoengine.queryset.visitor import Q
from appname.db import UserModel
from appname.error import InvalidUsage, exceptionReport
from appname.auth import check_auth
from appname.apitools import get_args, get_path, get_path_args, spec,\
        ApiParam, ApiResponse, Swagger
import random
iot_client = client('iot-data', region_name='ap-northeast-2')

sharing_code_words = []
def check_device(func):
    @check_auth
    def new_func(*args, **kwargs):
        device_id = kwargs['device_id']
        user_id = g.user.user_db.user_id
        res = iot_client.get_thing_shadow(thingName=device_id)
        payload = json.loads(res['payload'].read())
        state = payload['state']['reported']
        owner_id = state.get('owner_id', None)
        if type(owner_id) is list: #array2str search formater
            owner_id = owner_id[0]
            payload = json.dumps({
                'state': {
                    'reported': {
                        "owner_id" : owner_id
                    }
                }
            })
            iot_client.update_thing_shadow(thingName=device_id, payload=payload)


        try:
            user_db = UserModel.objects.get(user_id=user_id)
        except UserModel.DoesNotExist:
            raise InvalidUsage('This user is not found.', status_code=401)
        

        if user_id == owner_id and device_id in user_db.devices: #original user 
            return func(*args, **kwargs)
        else:   
            raise InvalidUsage('This user is not owner of this device.', status_code=401)

    new_func._original = func
    new_func.__name__ = func.__name__
    return new_func


shadow_example = {
    'name': 'example_name',
    'reported': {
        'light': 0,
        'power': False,
        'status1': 4200,
        'status2': 0,
        'owner_id': 'example_ownerId',
        'timestamp': 12312321,
    },
    'desired': {
        'light': 0,
        'power': True,
        'status1': 4200,
        'status2': 0,
        'timestamp': 12312321
    }

}

class DeviceRegister(Resource):
    @spec(
        '/devices/<string:device_id>/register',
        'Register Device ID in User DB Document',
        header_params=[*Swagger.Params.Authorization],
        path_params=[ApiParam('device_id', 'Device ID')],
        responses=[
            ApiResponse(200, 'Register Device Succeed', shadow_example),
            ApiResponse(401, 'Unauthenticated Device',
                dict(message='This user is not owner of this device.')),
            ApiResponse.error(406, 'Expired Temporary Code'),
            ApiResponse.error(409, "Already Registered Device")
    ])
    @check_auth
    def post(self, device_id):
        
        user_db = g.user.user_db
        user_id = user_db.user_id
        res = iot_client.get_thing_shadow(thingName=device_id)
        payload = json.loads(res['payload'].read())
        state = payload['state']
        reported = state.get('reported', {})
        desired = state.get('desired', {})

        if device_id in user_db.devices:
            exceptionReport(g.user.user_db , get_path(), get_path_args(), get_args())
            raise InvalidUsage('Already Registered Device', 409)


        if user_id == reported['owner_id']: 
            user_db.update(**{'set__devices__'+ device_id: device_id})
            user_db.reload()

            return state
        else:
            exceptionReport(g.user.user_db , get_path(), get_path_args(), get_args())
            raise InvalidUsage('This user is not owner of this device.', status_code=401)

    

class DeviceState(Resource):
    @spec(
        '/devices/<string:device_id>/state',
        'Get Current State of Device',
        header_params=[*Swagger.Params.Authorization],
        path_params=[ApiParam('device_id', 'Device ID')],
        responses=[
            ApiResponse(200, 'Register Device Succeed', shadow_example),
            ApiResponse(401, 'Unauthenticated Device',
                dict(message='This user is not owner of this device.'))
        ]
    )
    @check_device
    def get(self, device_id):
        payload = json.dumps({
            'state': {
                'desired': {
                    'timestamp': int(time.time() * 1000)
                }
            }
        })

        res = iot_client.get_thing_shadow(thingName=device_id)
        iot_client.update_thing_shadow(thingName=device_id, payload=payload)
        payload = json.loads(res['payload'].read())

        state = payload['state']
        state['name'] = g.user.user_db.devices[device_id]

        return state

    @spec(
        '/devices/<string:device_id>/state',
        'Update Current State of Device',
        header_params=[*Swagger.Params.Authorization],
        path_params=[ApiParam('device_id', 'Device ID')],
        body_name="Device States",
        body_params=[
            ApiParam('state', 'Device State Info', "object", properties=[
                ApiParam("state1", type="boolean"),
                ApiParam("state2", type="number"),
                ApiParam("state3", type="string")
            ])
        ],
        responses=[
            ApiResponse(200, 'Register Device Succeed', shadow_example),
            ApiResponse(401, 'Unauthenticated Device',
                dict(message='This user is not owner of this device.'))
        ]
    )
    @check_device
    def post(self, device_id):
        args = get_args()
        desired = args['state']
        desired['timestamp'] = int(time.time() * 1000)

        if 'name' in desired:
            name = desired.pop('name')
            g.user.user_db.devices[device_id] = name
            g.user.user_db.save()

        payload = json.dumps({
            'state': {
                'desired': desired
            }
        })
        iot_client.update_thing_shadow(thingName=device_id, payload=payload)
        res = iot_client.get_thing_shadow(thingName=device_id)
        data = json.loads(res['payload'].read())
        state = data['state']
        state['name'] = g.user.user_db.devices[device_id]

        return state


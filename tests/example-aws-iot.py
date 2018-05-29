import collections
import unittest
from flask import json
from deepscent.db import UserModel
from unittest.mock import Mock, patch
from tests.common import BaseTest
from deepscent.app import app
from copy import deepcopy

state = {
    'name': 'kibak`s arom',
    'reported': {
        'light': 0,
        'power': False,
        'fan1': 4200,
        'fan2': 0,
        'fan3': 4200,
        'fan4': 100,
        'owner_id': 'kibak',
        'timestamp': 12312321,
        'cart1_scent': 'lemon',
        'cart1_serial': 'dfadsfasfd',
        'cart2_scent': 'lavender',
        'cart2_serial': 'kfadmflkaadkflas',
        'cart3_scent': 'citronella',
        'cart3_serial': 'dafklkajdflk',
        'cart4_scent': 'peppermint',
        'cart4_serial': 'adsfkadslfk'
    },
    'desired': {
        'light': 0,
        'power': True,
        'fan1': 4200,
        'fan2': 0,
        'fan3': 4200,
        'fan4': 100,
    }
}

class Payload:
    def __init__(self, state):
        self.state = state 

    def read(self):
        return json.dumps(dict(state=self.state))

class MockIotClient:
    def __init__(self, state):
        self.state = deepcopy(state)

    def get_thing_shadow(self, thingName):
        return dict(payload=Payload(self.state))

    def update_thing_shadow(self, thingName, payload):
        self.state = self._update(self.state, json.loads(payload))
        
    def _update(self, table, data):
        for key, value in data.items():
            if isinstance(value, dict):
                table[key] = self._update(table.get(key, {}), value)
            else:
                table[key] = value
        return table


class DeviceTest(BaseTest):
    def tearDown(self):
        try:
            UserModel.objects.get(email='abc1@abcmart.com').delete()
        except UserModel.DoesNotExist:
            return None


    def test_ShareDevice(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)
        rv_prev3 = self.app.post('/auth/signup', data=dict(email='abc2@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev3.status_code, 200)

        rv_prev4 = self.app.post('/auth/login', data=dict(email='abc2@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev4.status_code, 200)

        user = UserModel.objects.get(email='abc1@abcmart.com')

        state['reported']['owner_id'] = user.user_id

        auth_token = json.loads(rv_prev2.data)['auth_token']
        other_auth_token = json.loads(rv_prev4.data)['auth_token']
        
        device_id = 'Device ID'

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv = self.app.post(
                    '/devices/' + device_id + '/register',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 200)
            rv = self.app.get(
                    '/devices/' + device_id + '/sharingCode',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 200)            
            rv_prev = self.app.post(
                    '/devices/sharingCode/register',
                    data=dict(sharingCode=json.loads(rv.data)['sharingCode']) ,
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv_prev.status_code, 409)
            rv = self.app.post(
                    '/devices/sharingCode/register',
                    data=dict(sharingCode=json.loads(rv.data)['sharingCode']) ,
                    headers={'Authorization': '{}'.format(other_auth_token)})
            self.assertEqual(rv.status_code, 200)
            rv = self.app.post(
                    '/devices/sharingCode/register',
                    data=dict(sharingCode="wrong") ,
                    headers={'Authorization': '{}'.format(other_auth_token)})
            self.assertEqual(rv.status_code, 401)

    def test_get_device_sharing_code(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        user = UserModel.objects.get(email='abc1@abcmart.com')

        state['reported']['owner_id'] = user.user_id

        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv = self.app.post(
                    '/devices/' + device_id + '/register',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 200)
            rv = self.app.get(
                    '/devices/' + device_id + '/sharingCode',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 200)
            rv = self.app.get(
                    '/devices/' + 'wrongdevice_id' + '/sharingCode',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 401)
    


    def test_get_deviceSharingUser(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        user = UserModel.objects.get(email='abc1@abcmart.com')

        state['reported']['owner_id'] = user.user_id

        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv = self.app.post(
                    '/devices/' + device_id + '/register',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 200)
            rv = self.app.get(
                    '/devices/' + device_id + '/sharing',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 200)
            rv = self.app.get(
                    '/devices/' + 'wrongdevice_id' + '/sharing',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 401)
    


    def test_device_register_success(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        user = UserModel.objects.get(email='abc1@abcmart.com')

        state['reported']['owner_id'] = user.user_id

        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv = self.app.post(
                    '/devices/' + device_id + '/register',
                    headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 200)

    def test_device_register_fail(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        state['reported']['owner_id'] = None

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv = self.app.post('/devices/' + device_id + '/register',
                               headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 401)

    def test_device_get_state_success(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc4@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)
        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc4@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        user = UserModel.objects.get(email='abc4@abcmart.com')
        state['reported']['owner_id'] = user.user_id

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv_prev3 = self.app.post('/devices/' + device_id + '/register',
                                     headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv_prev3.status_code, 200)

            rv = self.app.get('/devices/' + device_id + '/state',
                              headers={'Authorization': '{}'.format(auth_token)})

            self.assertEqual(rv.status_code, 200)

    def test_device_get_state_fail(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc1@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        user = UserModel.objects.get(email='abc1@abcmart.com')
        state['reported']['owner_id'] = user.user_id

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv = self.app.get('/devices/' + device_id + '/state',
                              headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 401)

    def test_device_change_state_success(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc5@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc5@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        user = UserModel.objects.get(email='abc5@abcmart.com')
        state['reported']['owner_id'] = user.user_id

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv_prev3 = self.app.post('/devices/' + device_id + '/register',
                                     headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv_prev3.status_code, 200)
            rv = self.app.post('/devices/' + device_id + '/state',
                               data=dict(state=json.dumps(dict(power=True))),
                               headers={'Authorization': '{}'.format(auth_token)})

            UserModel.objects.get(email='abc5@abcmart.com').delete()
            self.assertEqual(rv.status_code, 200)

    def test_device_change_state_fail(self):
        rv_prev1 = self.app.post('/auth/signup', data=dict(email='abc6@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev1.status_code, 200)

        rv_prev2 = self.app.post('/auth/login', data=dict(email='abc6@abcmart.com', pwd='abcdefg'))
        self.assertEqual(rv_prev2.status_code, 200)

        UserModel.objects.get(email='abc6@abcmart.com').delete()
        auth_token = json.loads(rv_prev2.data)['auth_token']
        device_id = 'Device ID'

        with patch('deepscent.device.iot_client', MockIotClient(state)):
            rv = self.app.post('/devices/' + device_id + '/state',
                               data=dict(state=json.dumps(dict(power=True))),
                               headers={'Authorization': '{}'.format(auth_token)})
            self.assertEqual(rv.status_code, 401)


from tests.common import BaseTest
from deepscent.db import HelpDataModel, drop_all_collection
from unittest.mock import patch

class HelpTest(BaseTest):
    def setUp(self):
        super().setUp()
        drop_all_collection()
        email = 'abc1@abcmart.com'
        token = self.signup_login(email)
        self.auth = token['auth_token']
        self.headers = {'Authorization': '{}'.format(self.auth)}
        HelpDataModel(
            title='비밀번호를 잊어버렸습니다.',
            details=('로그인 페이지 하단의 "비밀번호 찾기" 버튼을 클릭하여 임시 비밀번호를 발급받으실 수 있습니다.' +
                     '<br><br>임시 비밀번호는 발급받은 직후부터 10분간 유효하며, 회원가입 시 입력했던 이메일로 ' +
                     '발송되니 이메일을 확인해주세요.<br><br>이메일이 발송되는 데에는 약간의 시간이 소요되며, ' +
                     '2분이 지나도 이메일이 오지 않는다면 현재 페이지의 우측 상단에 있는 "문의하기" 버튼을 ' +
                     '클릭하여 고객센터로 문의해주시면 감사하겠습니다.'),
            type='auth'
        ).save()

    def tearDown(self):
        drop_all_collection()

    def test_help_data_get(self):
        rv = self.client.get('/help')
        self.assertEqual(rv.status_code, 200)

        data = rv.json['data']
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['title'], '비밀번호를 잊어버렸습니다.')
        self.assertEqual(data[0]['type'], 'auth')

    def test_contact_email_not_user(self):
        with patch('deepscent.apitools.email_client.send_email') as mock,\
                patch('deepscent.help.render_template') as template_mock:
            mock.return_value = None
            data = dict(email='abcd@abcdmart.com',
                        title='비밀번호',
                        type='Auth',
                        details='비밀번호 찾기는 어떻게 하나요?')
            rv = self.app.post('/auth/logout', headers=self.headers)
            self.assertEqual(rv.status_code, 200)
            rv = self.app.post('/help/contact', data=data)
            self.assertEqual(rv.status_code, 200)

    def test_contact_email_is_user(self):
        with patch('deepscent.apitools.email_client.send_email') as mock,\
                patch('deepscent.help.render_template') as template_mock:
            mock.return_value = None
            data = dict(email='abc1@abcmart.com',
                        title='카트리지 문의',
                        type='Device',
                        details='카트리지 교체는 어떻게 하나요?')
            rv = self.app.post('/help/contact', data=data)
            self.assertEqual(rv.status_code, 200)

    def test_contact_email_error(self):
        data = dict(email='abc1@abcmart.com',
                    title='카트리지 문의',
                    type='Device',
                    details='카트리지 교체는 어떻게 하나요?')
        with patch('deepscent.apitools.email_client.send_email') as mock,\
                patch('deepscent.help.render_template') as template_mock:
            mock.side_effect = Exception()
            rv = self.app.post('/help/contact', data=data)
            self.assertEqual(rv.status_code, 500)


from tests.common import BaseTest
from unittest.mock import Mock, patch
from deepscent.db import ImageAttachmentModel, drop_all_collection, UserModel
from io import StringIO

class AttachmentTest(BaseTest):
    def setUp(self):
        super().setUp()
        try:
            UserModel.objects.get(email='abc1@abcmart.com').delete()
            UserModel.objects.get(email='abc2@abcmart.com').delete()
        except UserModel.DoesNotExist:
            pass

        email = 'abc1@abcmart.com'
        token = self.signup_login(email)
        self.auth = token['auth_token']
        self.headers = {'Authorization': '{}'.format(self.auth)}

    def upload_image(self, image_name):
        rv = self.client.post(
            '/attachments',
            headers=self.headers,
            data = {
                'image': (StringIO(''), image_name)
            }
        )
        return rv

    def test_attachment_upload(self):
        with patch('deepscent.attachment.s3.upload_fileobj') as mock:
            mock.return_value = None
            rv = self.upload_image("test.png")
            self.assertEqual(rv.status_code, 200)
            self.assertTrue(rv.json['url'].startswith('http'))
            self.assertEqual(rv.json['original_name'], 'test.png')

    def test_attachment_list(self):
        with patch('deepscent.attachment.s3.upload_fileobj') as mock:
            mock.return_value = None

            for i in range(0, 30):
                rv = self.upload_image("test%i.png" % i)

                self.assertEqual(rv.status_code, 200)

        rv = self.client.get('/attachments?limit=10', headers=self.headers)

        self.assertEqual(200, rv.status_code)
        self.assertEqual(len(rv.json['attachments']), 10)
        self.assertEqual(rv.json['total_size'], 30)

        rv2 = self.client.get('/attachments?offset=5&limit=10', headers=self.headers)

        self.assertEqual(200, rv2.status_code)
        self.assertEqual(len(rv2.json['attachments']), 10)
        self.assertEqual(rv2.json['total_size'], 30)
        self.assertEqual(rv.json['attachments'][5:], rv2.json['attachments'][:5])


    def test_attachment_upload_invalid_file_type(self):
        with patch('deepscent.attachment.s3.upload_fileobj') as mock:
            mock.side_effect = None
            rv = self.upload_image("test.txt")

            self.assertEqual(rv.status_code, 400)

    def test_attachment_upload_aws_exception(self):
        with patch('deepscent.attachment.s3.upload_fileobj') as mock:
            mock.side_effect = Exception()
            rv = self.upload_image("test.png")
            self.assertEqual(rv.status_code, 500)

    def test_attachment_delete(self):
        with patch('deepscent.attachment.s3.upload_fileobj') as mock:
            mock.return_value = None
            rv = self.upload_image('test.png')
            attachment_id = rv.json['id']

        with patch('deepscent.attachment.s3.delete_object') as mock:
            rv = self.client.delete(
                    '/attachments/' + attachment_id,
                    headers=self.headers)
            self.assertEqual(200, rv.status_code)

            rv = self.client.delete(
                    '/attachments/' + attachment_id,
                    headers=self.headers)
            self.assertEqual(404, rv.status_code)

    
    def test_attachment_delete_by_another_user(self):
        with patch('deepscent.attachment.s3.upload_fileobj') as mock:
            mock.return_value = None
            rv = self.upload_image('test.png')
            attachment_id = rv.json['id']

        token2 = self.signup_login("abc2@abcmart.com")
        headers2 = {'Authorization': '{}'.format(token2['auth_token'])}

        with patch('deepscent.attachment.s3.delete_object') as mock:
            rv = self.client.delete(
                    '/attachments/' + attachment_id,
                    headers=headers2)
            self.assertEqual(403, rv.status_code)

    def test_attachment_delete_s3_error(self):
        with patch('deepscent.attachment.s3.upload_fileobj') as mock:
            rv = self.upload_image('test.png')
            attachment_id = rv.json['id']

        with patch('deepscent.attachment.s3.delete_object') as mock:
            mock.side_effect = Exception()
            rv = self.client.delete(
                    '/attachments/' + attachment_id,
                    headers=self.headers)
            self.assertEqual(500, rv.status_code)

            mock.side_effect = None
            rv = self.client.delete(
                    '/attachments/' + attachment_id,
                    headers=self.headers)
            self.assertEqual(200, rv.status_code)



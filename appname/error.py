from flask import current_app as app
from flask import g, render_template, Markup
import boto3


email_client = boto3.client(
        'ses',
        region_name='us-west-2')

class exceptionReport(object):
    def __init__(self, userData, path, pathParam, requestParam=None):
        if app.testing is not True:
            template = render_template(
                            'exception_report_mail.template.html',
                            userdata=userData.marshall(),
                            path=path,
                            pathParam=pathParam,
                            requestParam=requestParam)
            email_client.send_email(
                    Destination={
                        'ToAddresses': [
                            'example_reciver@example.com'
                        ]
                    },
                    Message=dict(
                        Subject=dict(
                            Data="서버에 예외 발생",
                            Charset='utf8'),
                        Body=dict(Html=dict(Charset='utf8', Data=template))
                    ),
                    Source='example_writer@example.com')



class InvalidUsage(Exception):
    status_code = 400
    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


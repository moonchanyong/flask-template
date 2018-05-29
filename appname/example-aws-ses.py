from flask import g, render_template, Markup
from flask import current_app as app
from flask_restful import Resource
from functional import seq
from appname.error import InvalidUsage
from appname.db import StaticDataModel, UserModel
from appname.apitools import spec, Swagger, ApiResponse,\
    get_args, ApiParam, EnumConstraint, LengthConstraint
import appname.apitools as apitools
from mongoengine import ValidationError

mail_example = dict(
    title='example title ',
    details=('this is example' +
            '<br><br>its next line' ),
)


class HelpList(Resource):
    @spec('/help', 'Get help data list',
        responses=[
            ApiResponse(200, 'Succeed', dict(data=[mail_example]))
        ]
    )
    def get(self):
        try:
            help_data = list(HelpDataModel.objects)
            return dict(
                data=seq(help_data).map(lambda x: x.marshall()).list())
        except ValidationError:
            raise InvalidUsage("Help Data Not Found", status_code=404)

class Contact(Resource):
    @spec('/help/contact', 'Send Contact mail to us',
        header_params=[
            *Swagger.Params.Authorization
        ],
        body_params=[
            ApiParam('email',
                     'user email to receive answer',
                     constraints=[LengthConstraint(5, 100)]),
            ApiParam('title',
                    'user question title',
                    constraints=[LengthConstraint(2)]),
            ApiParam('details',
                    'user question details',
                    constraints=[LengthConstraint(10)]),
            ApiParam('type',
                    'user question type(Auth/Device/Etc)',
                    default='Etc',
                    constraints=[EnumConstraint(['Auth', 'Device', 'Etc'])])
          ],
        responses=[
            ApiResponse(200, 'Succeed', dict(result=True)),
            ApiResponse.error(500, 'Email Server Error')
        ]
    )
    def post(self):
        args = get_args()
        email = args['email']
        title = args['title']
        details = args['details']
        

        try:
            user = UserModel.objects.get(email=email)
        except UserModel.DoesNotExist:
            user = None

        try:
            if user:
                name = user.name
            else:
                name = ''

            template = render_template(
                'mail.template.html',
                name=name,
                details=Markup(details))
            charset = 'UTF-8'
            response = apitools.email_client.send_email(
                Destination={
                    'ToAddresses': [
                        app.config['CONTACT_EMAIL']
                    ],
                    'CcAddresses': [
                        email,
                    ],
                },
                Message=dict(
                    Subject=dict(
                        Data=title,
                        Charset='utf8'),
                    Body=dict(Html=dict(Charset='utf8', Data=template))
                ),
                Source=app.config['CONTACT_EMAIL'])
        except Exception as ex:
            print(ex)
            raise InvalidUsage("Email Server Error: {}".format(ex), 500)

        return dict(result=True)

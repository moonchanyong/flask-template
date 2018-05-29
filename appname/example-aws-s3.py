from functional import seq
from flask import g
from flask_restful import Resource
from appname.apitools import Swagger, spec, ApiResponse, ApiParam, \
    get_args, get_path, get_path_args
from appname.db import ImageAttachmentModel
from appname.auth import check_auth
from appname.error import InvalidUsage, exceptionReport
import boto3
from boto3.s3.transfer import TransferConfig
from flask import current_app as app

s3 = boto3.client('s3')

attachment_example = dict(
    original_name="example.png",
    url="http://example.png",
    reg_date='2018-01-04T14:08:29.520207+09:00'
)

class AttachmentList(Resource):
    @spec('/attachments', 'Get My Attachment List',
        header_params=Swagger.Params.Authorization,
        query_params=Swagger.Params.Page,
        responses=[
            ApiResponse(200, "Succeed",
                dict(attachments=[attachment_example], limit=20, total_size=100))
        ]
    )
    @check_auth
    def get(self):
        args = get_args()
        offset = args['offset']
        limit = args['limit']

        user_id = g.user.user_db.user_id
        query = ImageAttachmentModel.objects(user_id=user_id)

        attachments = query[offset:offset+limit]

        return dict(
            attachments=seq(attachments).map(lambda x: x.marshall()).list(),
            limit=limit,
            total_size=len(query))

    @spec('/attachments', 'Post Image Attachment',
        header_params=Swagger.Params.Authorization,
        body_type="data",
        body_params=[
            ApiParam("image", type="file", required=True)
        ],
        responses=[
            ApiResponse(200, "Succeed", attachment_example),
            ApiResponse.error(400, "Invalid Image Type"),
            ApiResponse.error(500, "s3 upload error. try again")
        ]
    )
    @check_auth
    def post(self):
        args = get_args()
        image = args['image']
        if not image.content_type.startswith('image'):
            exceptionReport(g.user.user_db , get_path(), get_path_args(), get_args())
            raise InvalidUsage("Invalid Image Type", 400)

        extension = image.filename.split('.')[-1]

        image_model = ImageAttachmentModel(
                user_id=g.user.user_db.user_id,
                extension=extension,
                orignal_name=image.filename)
        image_model.save()

        key = image_model.s3filename 
        upload_config = TransferConfig(use_threads=False)

        try:
            result = s3.upload_fileobj(
                    image, app.config['ATTACHMENT_S3_BUCKET'], key,
                    ExtraArgs={
                        "ACL": "public-read",
                        "ContentType": image.content_type
                    },
                    Config=upload_config)
        except:
            image_model.delete()
            exceptionReport(g.user.user_db , get_path(), get_path_args(), get_args())
            raise InvalidUsage("s3 upload error. try again", 500)

        return image_model.marshall()

class Attachment(Resource):
    @spec(
        '/attachments/<string:attachment_id>',
        "Delete Image Attachment",
        header_params=Swagger.Params.Authorization,
        responses=[
            ApiResponse(200, "Succeed", dict(result=True)),
            ApiResponse.error(404, "Image Not Found"),
            ApiResponse.error(403, "Image Uploaded by another user"),
            ApiResponse.error(500, "s3 delete error. try again")
        ]
    )
    @check_auth
    def delete(self, attachment_id):
        img = ImageAttachmentModel.objects.with_id(attachment_id)
        if img is None:
            exceptionReport(g.user.user_db , get_path(), get_path_args(), get_args())
            raise InvalidUsage("Image Not Found", 404)

        if img.user_id != g.user.user_db.user_id:
            exceptionReport(g.user.user_db , get_path(), get_path_args(), get_args())
            raise InvalidUsage("Image Uploaded by another user", 403)
        try:
            s3.delete_object(
                Bucket=app.config['ATTACHMENT_S3_BUCKET'],
                Key=img.s3filename)
        except:
            exceptionReport(g.user.user_db , get_path(), get_path_args(), get_args())
            raise InvalidUsage("s3 delete error. try again", 500)

        img.delete()
        return dict(result=True)
        



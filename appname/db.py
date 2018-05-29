from mongoengine import Document, StringField, ListField
from mongoengine import DictField, DateTimeField, IntField
from flask import current_app as app

import arrow
import datetime

class UserModel(Document):
    user_id = StringField(required=True, unique=True)
    email = StringField(required=True, unique=True)
    kakao_id = StringField()
    facebook_id = StringField()
    password = StringField()
    auth_token = StringField()
    refresh_token = StringField()
    access_token = StringField()

    picture = StringField()
    gender = StringField()
    name = StringField()
    birthday = DateTimeField()
    devices = DictField()

    tmp_password = StringField()
    tmp_password_valid_period = DateTimeField()

    place = StringField()
    space = StringField()
    purpose = StringField()

    prefer_scents = ListField(StringField())
    reg_date = DateTimeField(default=datetime.datetime.now)


    meta = {
            'indexes': [
                'user_id',
                'email',
                'kakao_id'
            ]
        }

    def marshall(self):
        return dict(
            user_id=self.user_id,
            email=self.email,
            name=self.name,
            gender=self.gender,
            picture=self.picture,
            devices=self.devices,
            birthday=str(arrow.get(self.birthday)))

class ImageAttachmentModel(Document):
    user_id = StringField(required=True, index=True)
    extension = StringField(required=True, default="png")
    orignal_name = StringField(required=True)

    reg_date = DateTimeField(default=datetime.datetime.now)

    @property
    def s3filename(self):
        return str(self.id) + "." + self.extension

    @property
    def s3_url(self):
        s3_root = app.config['S3_URL']
        s3_bucket = "{}/{}".format(s3_root, app.config['ATTACHMENT_S3_BUCKET'])
        return "{}/{}".format(s3_bucket, self.s3filename)

    def marshall(self):
        return dict(
            id=str(self.id),
            original_name=self.orignal_name,
            url=self.s3_url,
            reg_date=str(arrow.get(self.reg_date)))

class StaticDataModel(Document):
    title = StringField(required=True)
    details = StringField(required=True)
    type = StringField(required=True, default="etc")

    def marshall(self):
        return dict(
            id=str(self.id),
            title=self.title,
            details=self.details,
            type=self.type)

def drop_all_collection():
    for key, value in globals().items():
        if key.endswith("Model"):
            print("drop {}".format(key))
            try:
                value.drop_collection()
            except:
                pass

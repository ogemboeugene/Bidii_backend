from datetime import datetime
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import Schema, fields, post_load
from app.models import Notification

class NotificationSchema(SQLAlchemyAutoSchema):
    id = fields.Int(dump_only=True)
    user_id = fields.Int(required=True)
    message = fields.Str(required=True)
    created_at = fields.DateTime(format='iso', required=True)
    read = fields.Bool(required=True)

    @post_load
    def make_notification(self, data, **kwargs):
        # Convert created_at from string to datetime object if needed
        if isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return Notification(**data)

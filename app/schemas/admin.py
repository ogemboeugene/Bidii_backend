from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from app.models import AdminLog

class AdminLogSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AdminLog
        include_relationships = True
        load_instance = True

    id = auto_field()
    admin_id = auto_field()
    action = auto_field()
    details = auto_field()

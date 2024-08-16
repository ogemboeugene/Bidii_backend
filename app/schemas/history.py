import marshmallow
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import History, User, FormRecords, AdvanceHistory, AdvanceSummary
# Import UserSchema here
from app.schemas import UserSchema

class HistorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = History
        load_instance = True
        include_fk = True 

    user = marshmallow.fields.Nested('UserSchema', exclude=['password_hash'])

class FormRecordsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FormRecords
        load_instance = True
        include_fk = True

class AdvanceHistorySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AdvanceHistory
        load_instance = True
        include_fk = True

class AdvanceSummarySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = AdvanceSummary
        load_instance = True
        include_fk = True


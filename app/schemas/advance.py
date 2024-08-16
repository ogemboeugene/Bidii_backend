# app/schemas.py

from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import Advance, MonthlyAdvanceCredit

class AdvanceSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Advance
        load_instance = True
        include_fk = True

class MonthlyAdvanceCreditSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MonthlyAdvanceCredit
        load_instance = True
        include_fk = True

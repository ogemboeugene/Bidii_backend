from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from app.models import Transaction

class TransactionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Transaction
        load_instance = True

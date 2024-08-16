from app.models import Transaction
from app.extensions import db
from datetime import datetime
from dateutil.parser import parse as parse_datetime  # Import datetime parser

class TransactionService:
    @staticmethod
    def create_transaction(data):
        try:
            # Ensure required fields are present
            if 'amount' not in data or 'user_id' not in data:
                raise ValueError("Missing required fields")

            # Create new transaction object
            transaction = Transaction(
                amount=data['amount'],
                description=data.get('description', ''),
                user_id=data['user_id']
            )
            db.session.add(transaction)
            db.session.commit()
            return transaction
        except Exception as e:
            db.session.rollback()
            raise e
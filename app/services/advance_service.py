# app/services/advance_service.py

import logging
from app.extensions import db
from app.models import Advance, Transaction, GroupMonthlyPerformance
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AdvanceService:

    @staticmethod
    def create_advance(data):
        try:
            # Ensure data is converted correctly
            initial_amount = float(data['initial_amount'])
            interest_rate = 10  # 10% interest rate for new advances
            payment_amount = interest_rate/100 * initial_amount
            total_amount_due = initial_amount + payment_amount
            is_paid = False  # Advance is not paid at creation
            status = 'pending'  # Status at creation

            # Validate group_id
            group_id = data.get('group_id')
            if not GroupMonthlyPerformance.query.filter_by(group_id=group_id).first():
                raise ValueError(f"Invalid group_id: {group_id}")

            # Create an Advance instance
            advance = Advance(
                member_name=data['member_name'],
                initial_amount=initial_amount,
                payment_amount=payment_amount,
                is_paid=is_paid,
                user_id=data['user_id'],
                status=status,
                interest_rate=interest_rate,
                paid_amount=0.0,  # No payment made at creation
                total_amount_due=total_amount_due,
                group_id=data.get('group_id')
            )
            db.session.add(advance)
            db.session.commit()
            return advance
        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error occurred: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))
        
        
    @staticmethod
    def make_payment(advance_id, payment_amount, user_id):
        try:
            # Retrieve the advance
            advance = Advance.query.get(advance_id)
            if not advance:
                raise ValueError("Advance not found")

            if advance.is_paid:
                raise ValueError("Advance already paid")

            if payment_amount <= 0:
                raise ValueError("Payment amount must be greater than zero")

            # Update the advance details
            advance.paid_amount += payment_amount

            if advance.paid_amount >= advance.amount:
                advance.is_paid = True
                advance.paid_amount = advance.amount
                advance.status = 'paid'

            # Create and add the transaction
            transaction = Transaction(
                amount=payment_amount,
                description=f"Payment of {payment_amount} towards advance {advance_id}",
                user_id=user_id
            )
            db.session.add(transaction)

            # Commit changes to both Advance and Transaction tables
            db.session.commit()
            return advance

        except SQLAlchemyError as e:
            db.session.rollback()
            raise Exception(f"Database error occurred: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))


    @staticmethod
    def get_advance(advance_id):
        try:
            advance = Advance.query.get(advance_id)
            if not advance:
                raise ValueError("Advance not found")
            return advance
        except SQLAlchemyError as e:
            raise Exception(f"Database error occurred: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))

    @staticmethod
    def update_advance(advance_id, data):
        try:
            # Fetch the advance record
            advance = Advance.query.get(advance_id)
            if not advance:
                raise ValueError("Advance not found")

            logging.info(f"Advance record before update: {advance.paid_amount}, {advance.updated_at}, {advance.status}, {advance.is_paid}")

            # Check if 'paid_amount' is in the request data
            if 'paid_amount' in data:
                paid_amount = data['paid_amount']
                
                # Ensure paid_amount is converted to float and non-negative
                try:
                    paid_amount = float(paid_amount)
                except ValueError:
                    raise ValueError("Invalid paid_amount value")
                
                if paid_amount < 0:
                    raise ValueError("Paid amount cannot be negative")
                
                # Add paid_amount to the existing paid_amount
                advance.paid_amount += paid_amount
                logging.info(f"Updated paid_amount: {advance.paid_amount}")

                # Update updated_at timestamp
                advance.updated_at = datetime.utcnow()
                logging.info(f"Updated timestamp: {advance.updated_at}")

                # Ensure total_amount_due is a float for comparison
                try:
                    total_amount_due = float(advance.total_amount_due)
                except ValueError:
                    raise ValueError("Invalid total_amount_due value")
                
                # Check if paid_amount equals or exceeds total_amount_due
                if advance.paid_amount >= total_amount_due:
                    advance.status = 'completed'
                    advance.is_paid = True
                    logging.info(f"Advance status updated to completed and is_paid set to True")

            # Commit the changes
            db.session.commit()
            logging.info("Database commit successful")
            return advance

        except SQLAlchemyError as e:
            db.session.rollback()
            logging.error(f"Database error occurred: {str(e)}")
            raise Exception(f"Database error occurred: {str(e)}")
        except ValueError as e:
            logging.error(f"Value Error: {str(e)}")
            raise ValueError(str(e))
    
    @staticmethod
    def calculate_remaining_balance(advance_id):
        try:
            advance = Advance.query.get(advance_id)
            if not advance:
                raise ValueError("Advance not found")

            if advance.is_paid:
                return 0

            remaining_balance = advance.amount - advance.paid_amount
            return remaining_balance
        except SQLAlchemyError as e:
            raise Exception(f"Database error occurred: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))
        
    @staticmethod
    def list_advances(user_id):
        return Advance.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def list_advances_by_group_id(group_id):
        return Advance.query.filter_by(group_id=group_id).all()
    
    @staticmethod
    def delete_advance(advance_id):
        advance = Advance.query.get(advance_id)
        if advance:
            db.session.delete(advance)
            db.session.commit()
            return True
        return False

    @staticmethod
    def search_advances(user_id, query):
        return Advance.query.filter(Advance.user_id == user_id, Advance.status.ilike(f'%{query}%')).all()

    @staticmethod
    def update_advance_status(advance_id, status):
        advance = Advance.query.get(advance_id)
        if advance:
            advance.status = status
            db.session.commit()
            return advance
        return None

    @staticmethod
    def get_payment_history(transaction_id):
        try:
            # Retrieve the specific transaction by its ID
            transaction = Transaction.query.get(transaction_id)
            if not transaction:
                raise ValueError("Transaction not found")
            return transaction.to_dict()
        except SQLAlchemyError as e:
            raise Exception(f"Database error occurred: {str(e)}")
        except ValueError as e:
            raise ValueError(str(e))
from flask import Blueprint, current_app, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
from marshmallow.exceptions import ValidationError
from app.models import Transaction
from app.extensions import db
from app.models.user import User
from app.schemas import TransactionSchema
from app.services.transaction_service import TransactionService
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.validators import validate_current_user

bp = Blueprint('transaction', __name__)

@bp.route('/transactions', methods=['POST'])
@jwt_required()  # Requires a valid JWT token to access this endpoint
def create_transaction():
    try:
        current_user = get_jwt_identity()  # Retrieve current user from JWT token
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        data = request.get_json()
        print(f"Received data for create_transaction: {data}")  # Debugging statement
        
        # Ensure timestamp is not included in the data
        data.pop('timestamp', None)  # Remove timestamp from data if present
        
        # Create transaction using TransactionService
        transaction = TransactionService.create_transaction(data)
        
        # Serialize the transaction object
        serialized_transaction = TransactionSchema().dump(transaction)
        
        return jsonify(serialized_transaction), 201  # Return serialized data with status code 201
    except ValidationError as e:
        print(f"Validation Error: {str(e)}")  # Debugging statement
        return jsonify({'error': str(e)}), 400  # Bad request if validation fails
    except SQLAlchemyError as e:
        print(f"Database Error: {str(e)}")  # Debugging statement
        db.session.rollback()  # Rollback any database transaction in case of error
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Internal Server Error: {str(e)}")  # Debugging statement
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/transactions', methods=['GET'])
@jwt_required()  # Requires a valid JWT token to access this endpoint
def get_transactions():
    try:
        current_user = get_jwt_identity()  # Retrieve current user from JWT token
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        transactions = Transaction.query.all()
        serialized_transactions = TransactionSchema(many=True).dump(transactions)
        return jsonify(serialized_transactions), 200
    except SQLAlchemyError as e:
        print(f"Database Error: {str(e)}")  # Debugging statement
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        print(f"Internal Server Error: {str(e)}")  # Debugging statement
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/transactions/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    try:
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({'error': 'Unauthorized'}), 401

        transaction = Transaction.query.get_or_404(transaction_id)
        serialized_transaction = TransactionSchema().dump(transaction)
        return jsonify(serialized_transaction), 200
    except SQLAlchemyError as e:
        current_app.logger.error(f"Database Error: {str(e)}")
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/transactions/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_transactions_by_user(user_id):
    try:
        # Retrieve the current user from JWT token
        current_user = get_jwt_identity()
        
        # Validate the current user using the new function
        if not validate_current_user(current_user):
            return jsonify({'error': 'Invalid user data'}), 500
        
        # Ensure the current user is authorized to access the transactions
        current_user_id = current_user['id']
        current_user_role = current_user['role']
        
        if current_user_role == 'admin':
            # Admin can view all transactions
            transactions = Transaction.query.all()
        elif current_user_id == user_id:
            # Regular user can only view their own transactions
            transactions = Transaction.query.filter_by(user_id=user_id).all()
        else:
            return jsonify({'error': 'Forbidden'}), 403
        
        # If no transactions are found, return an empty list
        if not transactions:
            return jsonify([]), 200
        
        # Serialize the transactions
        serialized_transactions = TransactionSchema(many=True).dump(transactions)
        return jsonify(serialized_transactions), 200
    
    except SQLAlchemyError as e:
        # Log the database error and rollback the session
        current_app.logger.error(f"Database Error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        # Log any other unexpected errors
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/transactions/date-range', methods=['GET'])
@jwt_required()
def get_transactions_by_date_range():
    try:
        # Retrieve the current user from JWT token
        current_user = get_jwt_identity()
        
        # Validate the current user using the new function
        if not validate_current_user(current_user):
            return jsonify({'error': 'Invalid user data'}), 500
        
        # Check if start_date and end_date are provided
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'Start date and end date are required'}), 400

        # Ensure the current user is authorized to access the transactions
        current_user_id = current_user['id']
        current_user_role = current_user['role']
        
        if current_user_role == 'admin':
            # Admin can view all transactions within the date range
            transactions = Transaction.query.filter(
                Transaction.timestamp.between(start_date, end_date)
            ).all()
        elif current_user_role == 'user':
            # Regular user can only view their own transactions within the date range
            transactions = Transaction.query.filter(
                Transaction.user_id == current_user_id,
                Transaction.timestamp.between(start_date, end_date)
            ).all()
        else:
            return jsonify({'error': 'Forbidden'}), 403
        
        # Serialize the transactions
        serialized_transactions = TransactionSchema(many=True).dump(transactions)
        return jsonify(serialized_transactions), 200
    
    except SQLAlchemyError as e:
        # Log the database error and rollback the session
        current_app.logger.error(f"Database Error: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Database error'}), 500
    except Exception as e:
        # Log any other unexpected errors
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
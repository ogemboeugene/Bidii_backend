import logging
from flask import current_app
from flask import Blueprint, app, current_app, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from flask_cors import cross_origin
from marshmallow import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.models import GroupMonthlyPerformance, MonthlyPerformance
from app.extensions import db
from app.models.user import User
from app.schemas import GroupMonthlyPerformanceSchema, MonthlyPerformanceSchema
from app.services.performance_service import PerformanceService
import csv
from io import StringIO
from flask import Response
from sqlalchemy.orm import Session

bp = Blueprint('performance', __name__)

# Set up logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Define valid months
VALID_MONTHS = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12
}

@bp.route('/group_performances', methods=['POST'])
@cross_origin()
def create_group_performance():
    data = request.get_json()

    # Log the entire request data
    current_app.logger.debug(f"Request data: {data}")

    # Check for required fields
    required_fields = ['group_id', 'member_details', 'total_paid', 'month', 'year']
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        error_message = f'Missing fields: {", ".join(missing_fields)}'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

    # Validate and convert month
    month_name = data.get('month')
    if month_name not in VALID_MONTHS:
        error_message = f'Invalid month name: {month_name}'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

     # Check if the group_id is valid
    group_id = data.get('group_id')
    current_app.logger.debug(f"Received group_id: {group_id}")

    if not MonthlyPerformance.query.get(group_id):
        error_message = 'Invalid Group ID'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400
    
    # Validate year
    try:
        year = int(data.get('year'))
    except ValueError:
        error_message = 'Invalid year format'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

    # Convert fields with explicit checks
    def to_float(value):
        try:
            return float(value) if value not in [None, ''] else 0.0
        except ValueError:
            return 0.0

    # Convert fields and log values
    total_paid = to_float(data.get('total_paid'))
    this_month_shares = to_float(data.get('this_month_shares', 0))
    fine_and_charges = to_float(data.get('fine_and_charges', 0))
    savings_shares_bf = to_float(data.get('savings_shares_bf', 0))
    loan_balance_bf = to_float(data.get('loan_balance_bf', 0))

    # Log the converted values for debugging
    current_app.logger.debug(f"Converted Values: total_paid={total_paid}, this_month_shares={this_month_shares}, fine_and_charges={fine_and_charges}, savings_shares_bf={savings_shares_bf}, loan_balance_bf={loan_balance_bf}")

    # Validate this_month_shares
    if this_month_shares > total_paid:
        error_message = 'this_month_shares cannot be greater than total_paid'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

    # Initialize variables
    loan_interest = 0
    principal = 0
    savings_shares_cf = 0
    loan_cf = 0

    # Check if group already exists for the month
    existing_performance = GroupMonthlyPerformance.query.filter_by(
        group_id=data.get('group_id'),
        member_details=data.get('member_details'),
        month=month_name,
        year=year
    ).first()

    if existing_performance:
        # Use carried forward values from existing performance
        savings_shares_bf = existing_performance.savings_shares_bf or 0
        loan_balance_bf = existing_performance.loan_balance_bf or 0

        # Calculate fields based on carried forward values
        loan_interest = round(loan_balance_bf * 0.015, 2)
        principal = round(total_paid - this_month_shares - loan_interest, 2)

        # Adjust principal and this_month_shares if principal is negative
        if principal < 0:
            principal = 0
            this_month_shares = total_paid - loan_interest

        loan_cf = round(loan_balance_bf - principal, 2)
        if loan_cf < 0:
            principal = round(loan_balance_bf, 2)
            loan_cf = 0
            this_month_shares = total_paid - principal - loan_interest

        savings_shares_cf = savings_shares_bf + this_month_shares

        # Handle fine_and_charges, default to 0 if not provided
        fine_and_charges = round(to_float(data.get('fine_and_charges', 0)), 2)

        # Log intermediate calculation values
        current_app.logger.debug(f"Intermediate Intermediate Calculations: loan_interest={loan_interest}, principal={principal}, loan_cf={loan_cf}, savings_shares_cf={savings_shares_cf}")

        # Update existing performance record
        existing_performance.total_paid = total_paid
        existing_performance.principal = principal
        existing_performance.loan_interest = loan_interest
        existing_performance.this_month_shares = this_month_shares
        existing_performance.fine_and_charges = fine_and_charges
        existing_performance.savings_shares_cf = savings_shares_cf
        existing_performance.loan_cf = loan_cf
    else:
        # New group: set defaults and perform calculations
        if savings_shares_bf == 0 and loan_balance_bf == 0:
            # No loan balance or savings carried forward, set principal and loan_cf to 0
            loan_interest = 0
            principal = 0
            savings_shares_cf = total_paid
            loan_cf = 0
        else:
            loan_interest = loan_balance_bf * 0.015
            principal = total_paid - this_month_shares - loan_interest

            # Adjust principal and this_month_shares if principal is negative
            if principal < 0:
                principal = 0
                this_month_shares = total_paid

            loan_cf = loan_balance_bf - principal
            if loan_cf < 0:
                principal = loan_balance_bf
                loan_cf = 0
                this_month_shares = total_paid - principal - loan_interest
                

            savings_shares_cf = savings_shares_bf + this_month_shares

        # Log intermediate calculation values
        current_app.logger.debug(f"Intermediate Calculations: loan_interest={loan_interest}, principal={principal}, loan_cf={loan_cf}, savings_shares_cf={savings_shares_cf}")

        # Create new performance record
        group_performance = GroupMonthlyPerformance(
            group_id=data.get('group_id'),
            member_details=data.get('member_details'),
            savings_shares_bf=savings_shares_bf,
            loan_balance_bf=loan_balance_bf,
            total_paid=total_paid,
            principal=principal,
            loan_interest=loan_interest,
            this_month_shares=this_month_shares,
            fine_and_charges=fine_and_charges,
            savings_shares_cf=savings_shares_cf,
            loan_cf=loan_cf,
            month=month_name,
            year=year
        )
        db.session.add(group_performance)

    try:
        db.session.commit()
        response = {
            'id': existing_performance.id if existing_performance else group_performance.id,
            'message': 'Group performance updated/created successfully'
        }
        return jsonify(response), 201
    
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error creating/updating group performance: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error'}), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500


@bp.route('/monthly_performance', methods=['POST'])
@cross_origin()
def create_or_update_monthly_performance():
    data = request.get_json()
    current_app.logger.debug(f'Received data: {data}')

    # Check for required fields
    required_fields = ['group_name', 'month', 'year']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        error_message = f'Missing fields: {", ".join(missing_fields)}'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

    # Validate and convert month
    month_name = data.get('month')
    if month_name not in VALID_MONTHS:
        error_message = f'Invalid month name: {month_name}'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

    # Validate year
    try:
        year = int(data.get('year'))
    except ValueError:
        error_message = 'Invalid year format'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

    # Validate numerical fields (handle defaults for missing fields)
    try:
        banking = float(data.get('banking', 0))
        service_fee = float(data.get('service_fee', 0))
        passbook = float(data.get('passbook', 0))
        office_debt_paid = float(data.get('office_debt_paid', 0))
        office_banking = float(data.get('office_banking', 0))
        loan_form = float(data.get('loan_form', 0))
    except ValueError:
        error_message = 'Invalid numerical value in one or more fields'
        current_app.logger.error(f"Bad Request: {error_message}")
        return jsonify({'error': error_message}), 400

    # Check if performance record already exists for the month
    existing_performance = MonthlyPerformance.query.filter_by(
        group_name=data['group_name'],
        month=month_name,
        year=year
    ).first()

    if existing_performance:
        # Update existing performance record
        existing_performance.banking = banking
        existing_performance.service_fee = service_fee
        existing_performance.passbook = passbook
        existing_performance.office_debt_paid = office_debt_paid
        existing_performance.office_banking = office_banking
        existing_performance.loan_form =  loan_form
    else:
        # Create new performance record
        new_performance = MonthlyPerformance(
            group_name=data['group_name'],
            banking=banking,
            service_fee=service_fee,
            passbook=passbook,
            office_debt_paid=office_debt_paid,
            office_banking=office_banking,
            loan_form=loan_form,
            month=month_name,
            year=year
        )
        db.session.add(new_performance)

    try:
        db.session.commit()
        response = {
            'id': existing_performance.id if existing_performance else new_performance.id,
            'message': 'Monthly performance updated/created successfully'
        }
        current_app.logger.debug(f'Success response: {response}')
        return jsonify(response), 201
    
    except SQLAlchemyError as e:
        current_app.logger.error(f"Error creating/updating monthly performance: {e}")
        db.session.rollback()
        return jsonify({'error': 'Internal Server Error'}), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500

@bp.route('/group_performances', methods=['GET'])
@cross_origin()
@jwt_required()
def get_group_performances():
    try:
        # Get the current user from the JWT token
        current_user = get_jwt_identity()
        
        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 401

        # Get group_id from query parameters
        group_id = request.args.get('group_id', type=int)

        if group_id is None:
            return jsonify({'error': 'group_id is required'}), 400

        if group_id <= 0:
            return jsonify({'error': 'Invalid group_id'}), 400

        # Query the database for records matching the group_id
        performances = GroupMonthlyPerformance.query.filter_by(group_id=group_id).all()
        
        if not performances:
            return jsonify({'message': 'No records found for this group ID'}), 404

        # Serialize the data
        performance_schema = GroupMonthlyPerformanceSchema(many=True)
        result = performance_schema.dump(performances)

        return jsonify(result), 200
        
    except SQLAlchemyError as e:
        db.session.rollback()
        app.logger.error(f'Database error: {e}')  # Log the database error
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        app.logger.error(f'Internal server error: {e}')  # Log the general error
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/monthly_performances', methods=['GET'])
@cross_origin()
@jwt_required()
def get_monthly_performances():
    try:
        current_user = get_jwt_identity()
        
        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 401
        
        performances = MonthlyPerformance.query.all()
        
        return MonthlyPerformanceSchema(many=True).dump(performances), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/group_performances/<int:id>', methods=['GET'])
@cross_origin()
@jwt_required()
def get_group_performance(id):
    try:
        current_user = get_jwt_identity()
        
        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 401
        
        performance = db.session.get(GroupMonthlyPerformance, id)
        
        return GroupMonthlyPerformanceSchema().dump(performance), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/monthly_performances/<int:id>', methods=['GET'])
@cross_origin()
@jwt_required()
def get_monthly_performance(id):
    try:
        current_user = get_jwt_identity()
        
        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 401
        
        session = Session(db.engine)  # Create a session
        performance = session.get(MonthlyPerformance, id)  # Use session.get() to fetch the record
        
        if not performance:
            return jsonify({'error': 'Monthly performance not found'}), 404
        
        return MonthlyPerformanceSchema().dump(performance), 200
    except SQLAlchemyError as e:
        session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        session.close()  # Ensure the session is closed

@bp.route('/group_performances/<int:id>', methods=['PUT'])
@cross_origin()
@jwt_required()
def update_group_performance(id):
    session = None
    try:
        current_user_id = get_jwt_identity()
        current_app.logger.debug(f"Current user ID from JWT: {current_user_id}")

        if isinstance(current_user_id, dict):
            current_user_id = current_user_id.get('id')

        session = Session(db.engine)
        user = session.get(User, current_user_id)

        if not user:
            current_app.logger.debug(f"User with ID {current_user_id} not found")
            return jsonify({'error': 'User not found'}), 404
        
        if user.role != 'admin':
            current_app.logger.debug(f"User with ID {current_user_id} is not an admin")
            return jsonify({'error': 'Admins only!'}), 403

        performance = session.get(GroupMonthlyPerformance, id)
        if not performance:
            current_app.logger.debug(f"Group performance with ID {id} not found")
            return jsonify({'error': 'Group performance not found'}), 404

        data = request.get_json()
        updated_performance = PerformanceService.update_group_performance(performance, data)
        session.commit()
        
        result = GroupMonthlyPerformanceSchema().dump(updated_performance)
        return jsonify(result), 200

    except ValidationError as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        if session:
            session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        if session:
            session.rollback()
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if session:
            session.close()
            current_app.logger.debug("Session closed")


@bp.route('/monthly_performances/<int:id>', methods=['PUT'])
@cross_origin()
@jwt_required()
def update_monthly_performance(id):
    try:
        current_user_id = get_jwt_identity()  # Get user ID from JWT
        
        # Convert current_user_id to a simple value
        current_user_id = current_user_id.get('id')

        session = Session(db.engine)
        user = session.get(User, current_user_id)  # Fetch the user by ID using Session.get()

        if not user or user.role != 'admin':
            session.close()
            return jsonify({'error': 'Admins only!'}), 403

        performance = session.get(MonthlyPerformance, id)
        if not performance:
            session.close()
            return jsonify({'error': 'Monthly performance not found'}), 404

        data = request.get_json()
        updated_performance = PerformanceService.update_monthly_performance(performance, data)
        session.commit()
        result = MonthlyPerformanceSchema().dump(updated_performance)
        session.close()
        
        return jsonify(result), 200
    except ValidationError as e:
        current_app.logger.error(f"Validation error: {e}")
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/group_performances/filter', methods=['POST'])
@cross_origin()
@jwt_required()
def filter_group_performances():
    try:
        current_user = get_jwt_identity()
        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 401
        
        # Retrieve JSON data
        data = request.get_json()
        
        # Log the received data for debugging
        current_app.logger.debug(f"Received JSON data: {data}")

        # Extract parameters from the JSON data
        month = data.get('month')
        year = data.get('year')
        group_name = data.get('group_name')

        # Log received parameters for debugging
        current_app.logger.debug(f"Received parameters - Month: {month}, Year: {year}, Group Name: {group_name}")

        # Ensure at least one parameter is provided
        if not month and not year and not group_name:
            return jsonify({'error': 'No filter parameters provided'}), 400

        # Start with the base query
        query = GroupMonthlyPerformance.query
        
        # Apply filters based on provided parameters
        if month:
            current_app.logger.debug(f"Applying filter for month: {month}")
            query = query.filter(GroupMonthlyPerformance.month.ilike(f'%{month}%'))
        if year:
            try:
                year = int(year)
                current_app.logger.debug(f"Applying filter for year: {year}")
                query = query.filter(GroupMonthlyPerformance.year == year)
            except ValueError:
                return jsonify({'error': 'Invalid year format'}), 400
        if group_name:
            current_app.logger.debug(f"Applying filter for group name: {group_name}")
            query = query.filter(GroupMonthlyPerformance.group_name.ilike(f'%{group_name}%'))
        
        # Execute the query and get results
        performances = query.all()
        
        # Log the final query and results
        current_app.logger.debug(f"Final query executed: {str(query)}")
        current_app.logger.debug(f"Number of records found: {len(performances)}")
        
        return GroupMonthlyPerformanceSchema(many=True).dump(performances), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/monthly_performances/filter', methods=['POST'])
@cross_origin()
@jwt_required()
def filter_monthly_performances():
    try:
        current_user = get_jwt_identity()
        
        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 401
        
        # Retrieve JSON data
        data = request.get_json()
        
        # Log the received data for debugging
        current_app.logger.debug(f"Received JSON data: {data}")

        # Extract parameters from the JSON data
        month = data.get('month')
        year = data.get('year')
        group_name = data.get('group_name')

        # Log received parameters for debugging
        current_app.logger.debug(f"Received parameters - Month: {month}, Year: {year}, Group Name: {group_name}")

        # Ensure at least one parameter is provided
        if not month and not year and not group_name:
            return jsonify({'error': 'No filter parameters provided'}), 400

        # Start with the base query
        query = MonthlyPerformance.query
        
        # Apply filters based on provided parameters
        if month:
            current_app.logger.debug(f"Applying filter for month: {month}")
            query = query.filter(MonthlyPerformance.month.ilike(f'%{month}%'))
        if year:
            try:
                year = int(year)
                current_app.logger.debug(f"Applying filter for year: {year}")
                query = query.filter(MonthlyPerformance.year == year)
            except ValueError:
                return jsonify({'error': 'Invalid year format'}), 400
        if group_name:
            current_app.logger.debug(f"Applying filter for group name: {group_name}")
            query = query.filter(MonthlyPerformance.group_name.ilike(f'%{group_name}%'))
        
        # Execute the query and get results
        performances = query.all()
        
        # Log the final query and results
        current_app.logger.debug(f"Final query executed: {str(query)}")
        current_app.logger.debug(f"Number of records found: {len(performances)}")
        
        return MonthlyPerformanceSchema(many=True).dump(performances), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"Database error: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# list all members and total members
@bp.route('/member_names', methods=['GET'])
@cross_origin()
@jwt_required()  # Ensure that the user is authenticated
def get_member_details():
    try:
        # Query all member details from the GroupMonthlyPerformance table
        member_details_query = db.session.query(
            GroupMonthlyPerformance.savings_shares_bf,
            GroupMonthlyPerformance.loan_balance_bf
        ).all()

        # Calculate total member details count, and sums of savings_shares_bf and loan_balance_bf
        total_member_details = len(member_details_query)
        total_savings_shares_bf = sum(detail[0] for detail in member_details_query if detail[0] is not None)
        total_loan_balance_bf = sum(detail[1] for detail in member_details_query if detail[1] is not None)

        # Query count of active users
        total_active_users = User.query.filter_by(active=True).count()

        # Get the current user's identity
        current_user_id = get_jwt_identity().get('id')

        # Fetch the current user's username
        current_user = User.query.get(current_user_id)
        if current_user:
            full_username = current_user.username
            # Extract the first name from the username
            first_name = full_username.split()[0] if full_username else 'Unknown'
        else:
            first_name = 'Unknown'

        # Return the results as JSON
        return jsonify({
            'total_member_details': total_member_details,
            'total_savings_shares_bf': total_savings_shares_bf,
            'total_loan_balance_bf': total_loan_balance_bf,
            'total_active_users': total_active_users,
            'current_first_name': first_name
        }), 200

    except Exception as e:
        # Handle any exceptions that occur
        return jsonify({'error': str(e)}), 500
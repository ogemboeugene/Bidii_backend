# app/routes/advance_routes.py

from flask import Blueprint, jsonify, request, current_app
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from app.schemas.advance import MonthlyAdvanceCreditSchema
from app.schemas import AdvanceSchema
from app.services.advance_service import AdvanceService
from app.models import MonthlyAdvanceCredit, GroupMonthlyPerformance, MonthlyPerformance
from app.extensions import db

bp = Blueprint('advances', __name__)

@bp.route('/advances', methods=['POST'])
@cross_origin()
@jwt_required()
def create_advance():
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        data['user_id'] = current_user['id']
        
        # Validate and create the advance
        advance = AdvanceService.create_advance(data)
        serialized_advance = AdvanceSchema().dump(advance)
        return jsonify(serialized_advance), 201

    except ValidationError as e:
        current_app.logger.warning(f"Validation Error: {str(e)}")
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/member_details', methods=['GET'])
@cross_origin()
@jwt_required()
def get_member_details():
    try:
        # Query all member details
        results = GroupMonthlyPerformance.query.with_entities(GroupMonthlyPerformance.member_details).all()
        
        # Extract member details
        member_details = [result.member_details for result in results]
        
        return jsonify(member_details), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500
    
@bp.route('/advances/<int:advance_id>/payment', methods=['POST'])
@cross_origin()
@jwt_required()
def make_payment(advance_id):
    try:
        data = request.get_json()
        payment_amount = data.get('payment_amount')

        if not payment_amount:
            return jsonify({'error': 'Payment amount is required'}), 400

        current_user = get_jwt_identity()
        user_id = current_user['id']

        # Make payment and update advance
        advance = AdvanceService.make_payment(advance_id, payment_amount, user_id)
        serialized_advance = AdvanceSchema().dump(advance)
        return jsonify(serialized_advance), 200

    except ValidationError as e:
        current_app.logger.warning(f"Validation Error: {str(e)}")
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/advances/<int:advance_id>', methods=['GET'])
@cross_origin()
@jwt_required()
def get_advance(advance_id):
    try:
        # Retrieve advance details
        advance = AdvanceService.get_advance(advance_id)
        serialized_advance = AdvanceSchema().dump(advance)
        return jsonify(serialized_advance), 200

    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/advances/<int:advance_id>', methods=['PATCH'])
@cross_origin()
@jwt_required()
def update_advance(advance_id):
    try:
        data = request.get_json()
        # Ensure only 'paid_amount' is allowed in the request
        if not ('paid_amount' in data and len(data) == 1):
            raise ValueError("Request data must contain only 'paid_amount'")

        # Update advance details
        advance = AdvanceService.update_advance(advance_id, data)
        serialized_advance = AdvanceSchema().dump(advance)
        return jsonify(serialized_advance), 200

    except ValueError as e:
        current_app.logger.warning(f"Value Error: {str(e)}")
        return jsonify({'error': str(e)}), 400

    except ValidationError as e:
        current_app.logger.warning(f"Validation Error: {str(e)}")
        return jsonify({'error': str(e)}), 400

    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/advances/<int:advance_id>/balance', methods=['GET'])
@cross_origin()
@jwt_required()
def get_remaining_balance(advance_id):
    try:
        # Calculate remaining balance
        remaining_balance = AdvanceService.calculate_remaining_balance(advance_id)
        return jsonify({'remaining_balance': remaining_balance}), 200

    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/advances', methods=['GET'])
@cross_origin()
@jwt_required()
def list_advances():
    group_id = request.args.get('group_id')
    
    if not group_id:
        return jsonify({"error": "Group ID is required"}), 400
    
    try:
        # Assuming AdvanceService has a method to get advances by group_id
        advances = AdvanceService.list_advances_by_group_id(group_id)
        serialized_advances = AdvanceSchema(many=True).dump(advances)
        return jsonify(serialized_advances), 200
    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/advances/search', methods=['GET'])
@cross_origin()
@jwt_required()
def search_advances():
    try:
        current_user = get_jwt_identity()
        query = request.args.get('query', '')
        advances = AdvanceService.search_advances(current_user['id'], query)
        serialized_advances = AdvanceSchema(many=True).dump(advances)
        return jsonify(serialized_advances), 200
    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/advances/<int:advance_id>/payments', methods=['GET'])
@cross_origin()
@jwt_required()
def get_payment_history(advance_id):
    try:
        payments = AdvanceService.get_payment_history(advance_id)
        return jsonify(payments), 200
    except Exception as e:
        current_app.logger.error(f"Internal Server Error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# MonthlyAdvanceCredit
@bp.route('/monthly_advance_credits', methods=['GET'])
@jwt_required() 
@cross_origin()
def get_monthly_advance_credits():
    credits = MonthlyAdvanceCredit.query.all()
    result = [credit.to_dict() for credit in credits]  # Use to_dict to convert models to dicts
    return jsonify(result)

@bp.route('/monthly_advance_credits', methods=['POST'])
@jwt_required()
@cross_origin()
def create_monthly_advance_credit():
    schema = MonthlyAdvanceCreditSchema()

    try:
        # Log the incoming request data
        current_app.logger.info(f"Incoming data: {request.json}")

        # Load the data and create an instance of MonthlyAdvanceCredit
        validated_data = schema.load(request.json, session=db.session)

        # Log the validated data
        current_app.logger.info(f"Validated data: {validated_data}")

        # validated_data is now an instance of MonthlyAdvanceCredit
        new_credit = validated_data
        
        # Add to session and commit
        db.session.add(new_credit)
        db.session.commit()

        # Log the successful creation
        current_app.logger.info(f"Successfully created new credit: {new_credit}")

        # Return success response
        result = schema.dump(new_credit)
        return jsonify(result), 201

    except ValidationError as err:
        # Log validation errors
        current_app.logger.error(f"Validation error: {err.messages}")
        return jsonify({"message": "Validation error", "errors": err.messages}), 400

    except Exception as e:
        # Log the error for debugging
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"message": "An error occurred while creating the record", "error": str(e)}), 500

@bp.route('/monthly_performance/filter', methods=['GET'])
@cross_origin()
def get_all_group_names():
    try:
        # Query all unique group names and their corresponding IDs
        group_data = db.session.query(
            MonthlyPerformance.id, 
            MonthlyPerformance.group_name
        ).distinct().all()

        # Convert the result to a list of dictionaries with 'id' and 'group_name'
        unique_groups = [{'id': id, 'group_name': group_name} for id, group_name in group_data]
        
        # Return the list of unique groups as JSON
        return jsonify(unique_groups), 200
    
    except Exception as e:
        # Log the error for debugging
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"message": "An error occurred while fetching group names", "error": str(e)}), 500

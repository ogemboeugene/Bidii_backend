from datetime import datetime
from flask_cors import cross_origin
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, NotFound
from flask import Blueprint,Flask, current_app, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from app.schemas import HistorySchema, FormRecordsSchema
from app.models import History, GroupMonthlyPerformance, MonthlyPerformance, User, FormRecords, AdvanceHistory, Advance, AdvanceSummary, User, MonthlyAdvanceCredit
from app.extensions import db
app = Flask(__name__)


bp = Blueprint('history', __name__)

@bp.route('/histories', methods=['GET'])
@jwt_required()
@cross_origin()
def get_histories():
    try:
        histories = History.query.all()  # Make sure History has query attribute
        return jsonify([history.to_dict() for history in histories]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@bp.route('/generate_form', methods=['POST'])
@jwt_required()
@cross_origin()
def generate_form():
    # Retrieve the JWT identity
    jwt_identity = get_jwt_identity()
    current_user_id = jwt_identity.get('id')  # Extract the user ID from the JWT identity
    current_app.logger.debug(f"JWT Identity: {current_user_id}")

    group_id = request.json.get('group_id')
    current_app.logger.debug(f"Received group_id: {group_id}")

    if not group_id:
        current_app.logger.error('group_id is required')
        return jsonify({'message': 'group_id is required'}), 400

    try:
        # Retrieve user based on the JWT identity
        user = User.query.filter_by(id=current_user_id).first()
        if not user:
            current_app.logger.error(f"User not found for ID: {current_user_id}")
            return jsonify({'message': 'User not found'}), 404
        current_app.logger.debug(f"Current User: {user.username}")

        # Retrieve records for the specific group_id from GroupMonthlyPerformance
        records = GroupMonthlyPerformance.query.filter_by(group_id=group_id).all()
        current_app.logger.debug(f"Records found: {len(records)}")

        if not records:
            current_app.logger.error(f"No records found for group_id: {group_id}")
            return jsonify({'message': 'No records found for the given group_id'}), 404

        # Query the MonthlyPerformance table to get the group_name using the group_id
        monthly_performance = MonthlyPerformance.query.filter_by(id=group_id).first()
        if monthly_performance:
            group_name = monthly_performance.group_name
        else:
            group_name = 'Unknown Group'
        current_app.logger.debug(f"Group Name: {group_name}")

        # Save records into the History table
        history_entry = History(
            group_name=group_name,
            created_by=user.username,  # Assuming 'username' is the column for user name
            date=datetime.utcnow()
        )
        db.session.add(history_entry)
        db.session.commit()
        current_app.logger.debug(f"History Entry Added: {history_entry}")

        # Save records into FormRecords table
        form_records_schema = FormRecordsSchema()
        form_records_to_save = []
        for record in records:
            form_record = FormRecords(
                history_id=history_entry.id,
                group_id=record.group_id,
                member_details=record.member_details,
                savings_shares_bf=record.savings_shares_cf,
                loan_balance_bf=record.loan_cf,
                total_paid=record.total_paid,
                principal=record.principal,
                loan_interest=record.loan_interest,
                this_month_shares=record.this_month_shares,
                fine_and_charges=record.fine_and_charges,
                savings_shares_cf=record.savings_shares_cf,
                loan_cf=record.loan_cf,
                month=record.month,
                year=record.year
            )
            form_records_to_save.append(form_record)
        db.session.bulk_save_objects(form_records_to_save)
        db.session.commit()
        current_app.logger.debug(f"Form Records Saved: {len(form_records_to_save)}")

        # Temporarily store the records to re-add after deletion
        records_to_readd = []
        for record in records:
            new_record = GroupMonthlyPerformance(
                group_id=record.group_id,
                member_details=record.member_details,
                savings_shares_bf=record.savings_shares_cf,
                loan_balance_bf=record.loan_cf,
                month=record.month,
                year=record.year
            )
            records_to_readd.append(new_record)
        current_app.logger.debug(f"Records to re-add: {len(records_to_readd)}")

        # Clear the GroupMonthlyPerformance table for the specific group_id
        GroupMonthlyPerformance.query.filter_by(group_id=group_id).delete()
        db.session.commit()
        current_app.logger.debug(f"Cleared records for group_id: {group_id}")

        # Re-add records with updated values
        db.session.bulk_save_objects(records_to_readd)
        db.session.commit()
        current_app.logger.debug("Records re-added successfully")

        return jsonify({'message': 'Form generated and records updated successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"SQLAlchemy Error: {str(e)}")
        return jsonify({'message': 'A database error occurred', 'error': str(e)}), 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred', 'error': str(e)}), 500
    
# Advance History
@bp.route('/generate_monthly_form', methods=['POST'])
@jwt_required()
@cross_origin()
def generate_monthly_form():
    # Retrieve the JWT identity
    jwt_identity = get_jwt_identity()
    current_user_id = jwt_identity.get('id')
    current_app.logger.debug(f"JWT Identity: {current_user_id}")

    group_id = request.json.get('group_id')
    current_app.logger.debug(f"Received group_id: {group_id}")

    if not group_id:
        current_app.logger.error('group_id is required')
        return jsonify({'message': 'group_id is required'}), 400

    try:
        # Retrieve user based on the JWT identity
        user = User.query.filter_by(id=current_user_id).first()
        if not user:
            current_app.logger.error(f"User not found for ID: {current_user_id}")
            return jsonify({'message': 'User not found'}), 404
        current_app.logger.debug(f"Current User: {user.username}")

        # Retrieve group name based on group_id
        group = MonthlyAdvanceCredit.query.filter_by(group_id=group_id).first()
        if not group:
            current_app.logger.error(f"Group not found for ID: {group_id}")
            return jsonify({'message': 'Group not found'}), 404
        group_name = group.group_name  # Adjust if necessary to match your User model

        # Retrieve all advance records for the specific group_id (both pending and completed)
        advances = Advance.query.filter_by(group_id=group_id).all()
        current_app.logger.debug(f"Advances found: {len(advances)}")

        if not advances:
            current_app.logger.error(f"No advances found for group_id: {group_id}")
            return jsonify({'message': 'No advances found for the given group_id'}), 404

        # Save records into the AdvanceHistory table
        history_entries = []
        for advance in advances:
            history_entry = AdvanceHistory(
                member_name=advance.member_name,
                initial_amount=advance.initial_amount,
                payment_amount=advance.payment_amount,
                is_paid=advance.is_paid,
                user_id=advance.user_id,
                status=advance.status,
                created_at=advance.created_at,
                updated_at=advance.updated_at,
                interest_rate=advance.interest_rate,
                paid_amount=advance.paid_amount,
                total_amount_due=advance.total_amount_due,
                group_id=advance.group_id
            )
            history_entries.append(history_entry)

        db.session.bulk_save_objects(history_entries)
        db.session.commit()
        current_app.logger.debug(f"Advance History Entries Saved: {len(history_entries)}")

        # Generate or update the AdvanceSummary record
        total_advances = len(advances)
        summary_entry = AdvanceSummary(
            group_name=group_name,  # Use the retrieved group name
            date=datetime.utcnow().date(),
            total_advances=total_advances
        )
        
        # Check if an entry already exists for the given group and date
        existing_summary = AdvanceSummary.query.filter_by(
            group_name=group_name,
            date=datetime.utcnow().date()
        ).first()
        
        if existing_summary:
            # Update existing entry
            existing_summary.total_advances = total_advances
        else:
            # Add new entry
            db.session.add(summary_entry)
        
        db.session.commit()
        current_app.logger.debug(f"Advance Summary Entry Saved/Updated: {summary_entry.to_dict()}")

        return jsonify({'message': 'Monthly form generated and advance history updated successfully'}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        current_app.logger.error(f"SQLAlchemy Error: {str(e)}")
        return jsonify({'message': 'A database error occurred', 'error': str(e)}), 500

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred', 'error': str(e)}), 500
    
@bp.route('/query_advance_history', methods=['GET'])
@jwt_required()
@cross_origin()
def query_advance_history():
    # Retrieve the group_id from query parameters
    group_id = request.args.get('group_id')
    current_app.logger.debug(f"Received group_id: {group_id}")

    if not group_id:
        current_app.logger.error('group_id is required')
        return jsonify({'message': 'group_id is required'}), 400

    try:
        # Query AdvanceHistory based on group_id
        history_records = AdvanceHistory.query.filter_by(group_id=group_id).all()
        current_app.logger.debug(f"Advance History Records Found: {len(history_records)}")

        if not history_records:
            current_app.logger.error(f"No advance history found for group_id: {group_id}")
            return jsonify({'message': 'No advance history found for the given group_id'}), 404

        # Convert records to list of dictionaries
        history_entries = [
            {
                'id': record.id,
                'member_name': record.member_name,
                'initial_amount': record.initial_amount,
                'payment_amount': record.payment_amount,
                'is_paid': record.is_paid,
                'user_id': record.user_id,
                'status': record.status,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat(),
                'interest_rate': record.interest_rate,
                'paid_amount': record.paid_amount,
                'total_amount_due': record.total_amount_due,
                'group_id': record.group_id
            }
            for record in history_records
        ]

        return jsonify({'advance_history': history_entries}), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"SQLAlchemy Error: {str(e)}")
        return jsonify({'message': 'A database error occurred', 'error': str(e)}), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred', 'error': str(e)}), 500


@bp.route('/query_advance_summary', methods=['GET'])
@jwt_required()
@cross_origin()
def query_advance_summary():
    # Retrieve query parameters
    group_name = request.args.get('group_name')
    date = request.args.get('date')  # Expected format: YYYY-MM-DD
    
    try:
        # Build query
        query = AdvanceSummary.query
        
        if group_name:
            query = query.filter_by(group_name=group_name)
        
        if date:
            date_filter = datetime.strptime(date, '%Y-%m-%d').date()
            query = query.filter_by(date=date_filter)
        
        summaries = query.all()
        current_app.logger.debug(f"Advance Summaries found: {len(summaries)}")
        
        if not summaries:
            current_app.logger.error('No summaries found matching the criteria')
            return jsonify({'message': 'No summaries found matching the criteria'}), 404
        
        # Convert results to list of dictionaries
        results = [summary.to_dict() for summary in summaries]
        
        return jsonify(results), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"SQLAlchemy Error: {str(e)}")
        return jsonify({'message': 'A database error occurred', 'error': str(e)}), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred', 'error': str(e)}), 500
    
@bp.route('/form_records/<int:history_id>', methods=['GET'])
@jwt_required()
@cross_origin()
def get_form_records(history_id):
    current_app.logger.debug(f"Received history_id: {history_id}")

    try:
        # Query the FormRecords table for the specified history_id
        records = FormRecords.query.filter_by(history_id=history_id).all()
        current_app.logger.debug(f"Records found: {len(records)}")

        if not records:
            current_app.logger.error(f"No records found for history_id: {history_id}")
            return jsonify({'message': 'No records found for the given history_id'}), 404

        # Serialize the records using FormRecordsSchema
        form_records_schema = FormRecordsSchema(many=True)
        result = form_records_schema.dump(records)
        current_app.logger.debug(f"Serialized Records: {result}")

        return jsonify(result), 200

    except SQLAlchemyError as e:
        current_app.logger.error(f"SQLAlchemy Error: {str(e)}")
        return jsonify({'message': 'A database error occurred', 'error': str(e)}), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected Error: {str(e)}")
        return jsonify({'message': 'An unexpected error occurred', 'error': str(e)}), 500
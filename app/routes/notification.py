from datetime import datetime
import logging
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from marshmallow.exceptions import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from app.models import Notification
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.schemas import NotificationSchema
from app.services.notification_service import NotificationService

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

bp = Blueprint('notification', __name__)

@bp.route('/notifications', methods=['POST'])
@jwt_required()
@cross_origin()
def create_notification():
    try:
        data = request.get_json()
        current_user = get_jwt_identity()

        if not current_user:
            return jsonify({'error': 'Unauthorized access'}), 401

        # Extract user_id from JWT if not provided in the request
        if 'user_id' not in data:
            data['user_id'] = current_user.get('id')  # Use the user ID from JWT claims
        
        # Convert created_at to datetime object if provided
        if 'created_at' in data:
            try:
                data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            except ValueError as e:
                logger.error(f"Invalid date format: {data['created_at']}")
                return jsonify({'error': 'Invalid date format'}), 400

        # Ensure user_id is a simple integer
        if isinstance(data.get('user_id'), dict):
            logger.error(f"Invalid user_id format: {data['user_id']} - user_id should not be a dictionary")
            return jsonify({'error': 'user_id should not be a dictionary'}), 400
        
        
        notification = NotificationService.create_notification(data)
        return NotificationSchema().dump(notification), 201
    except ValidationError as e:
        return jsonify({'error': str(e)}), 400
    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Internal Server Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/notifications', methods=['GET'])
@jwt_required()
@cross_origin()
def get_notifications():
    try:
        # Extract user_id from JWT token
        current_user = get_jwt_identity()
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user
        
        if not user_id:
            return jsonify({'error': 'Unauthorized access'}), 401

        # Fetch notifications for the current user
        notifications = Notification.query.filter_by(user_id=user_id).all()
        
        # If no notifications found, return an empty list with status 200
        if not notifications:
            return jsonify([]), 200

        return jsonify(NotificationSchema(many=True).dump(notifications)), 200
    except SQLAlchemyError as e:
        # Log detailed error message
        logger.error(f"SQLAlchemyError: {e}")
        db.session.rollback()
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        # Log detailed error message
        logger.error(f"Internal Server Error: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/notifications/<int:notification_id>', methods=['GET'])
@jwt_required()
@cross_origin()
def get_notification(notification_id):
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user

        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        return NotificationSchema().dump(notification), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemyError: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Exception: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@jwt_required()
@cross_origin()
def delete_notification(notification_id):
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user

        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        NotificationService.delete_notification(notification)
        return jsonify({'message': 'Notification deleted successfully'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemyError: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Exception: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    
@bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
@cross_origin()
def mark_as_read(notification_id):
    try:
        current_user = get_jwt_identity()
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user

        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if not notification:
            return jsonify({'error': 'Notification not found'}), 404

        notification.read = True
        db.session.commit()
        return jsonify({'message': 'Notification marked as read'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemyError: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Exception: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/notifications/read', methods=['PUT'])
@jwt_required()
@cross_origin()
def mark_all_as_read():
    try:
        # Get the current user's ID from the JWT token
        current_user = get_jwt_identity()
        user_id = current_user.get('id') if isinstance(current_user, dict) else current_user

        # Fetch all notifications for the current user
        notifications = Notification.query.filter_by(user_id=user_id).all()

        # Check if notifications are retrieved
        if not notifications:
            return jsonify({'error': 'No notifications found'}), 404

        # Update all notifications to read
        updated_notifications = []
        for notification in notifications:
            notification.read = True
            updated_notifications.append(notification.id)  # Collect updated notification IDs

        db.session.commit()

        # Log updated notifications for debugging
        logger.info(f"Marked all notifications as read: {updated_notifications}")

        return jsonify({'message': 'All notifications marked as read'}), 200
    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"SQLAlchemyError: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logger.error(f"Exception: {e}")
        return jsonify({'error': 'Internal server error'}), 500

from datetime import datetime
from app.models import Notification, User
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db
import logging
from dateutil import parser

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def create_notification(data):
        try:
            # Validate user_id
            user_id = data.get('user_id')
            if isinstance(user_id, dict):
                logger.error(f"Invalid user_id format: {user_id} - user_id should not be a dictionary")
                raise ValueError('user_id should not be a dictionary')

            if user_id:
                try:
                    user_id = int(user_id)  # Ensure user_id is an integer
                except (ValueError, TypeError) as e:
                    logger.error(f"Invalid user_id format: {user_id} - Error: {e}")
                    raise ValueError('Invalid user_id format')
                
                user = User.query.get(user_id)
                if not user:
                    logger.error(f"User with id {user_id} does not exist.")
                    raise ValueError('User does not exist')
            
            notification = Notification(**data)
            db.session.add(notification)
            db.session.commit()
            logger.debug(f"Notification created: {notification.to_dict()}")
            return notification
        except ValueError as e:
            logger.error(f"Value error: {e}")
            db.session.rollback()
            raise
        except SQLAlchemyError as e:
            logger.error(f"SQLAlchemy error: {e}")
            db.session.rollback()
            raise
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            db.session.rollback()
            raise
    @staticmethod
    def update_notification(notification, data):
        try:
            notification.message = data.get('message', notification.message)
            notification.read = data.get('read', notification.read)
            db.session.commit()
            return notification
        except SQLAlchemyError as e:
            logger.error(f"Error updating notification: {e}")
            db.session.rollback()
            raise e

    @staticmethod
    def delete_notification(notification):
        try:
            db.session.delete(notification)
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Error deleting notification: {e}")
            db.session.rollback()
            raise e
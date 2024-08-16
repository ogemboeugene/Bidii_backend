import re

from flask import current_app

def validate_email(email):
    regex = r'^\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.match(regex, email)

def validate_password(password):
    # Add password validation logic here
    return True

def validate_current_user(current_user):
    """Validate the current user's data."""
    if not isinstance(current_user, dict):
        current_app.logger.error(f"Invalid user data type: {type(current_user)}")
        return False
    if 'id' not in current_user:
        current_app.logger.error("User data missing 'id' field")
        return False
    if 'role' not in current_user:
        current_app.logger.error("User data missing 'role' field")
        return False
    return True
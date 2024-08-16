import os
from getpass import getpass
from app import create_app
from app.extensions import db
from app.models import User
from app.utils.helpers import hash_password

app = create_app(os.getenv('FLASK_CONFIG') or 'development')

def reset_password():
    email = input('Enter user email: ')
    new_password = getpass('Enter new password: ')

    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = hash_password(new_password)
            db.session.commit()
            print('Password reset successfully.')
        else:
            print('User not found.')

if __name__ == '__main__':
    reset_password()

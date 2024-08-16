import os
from getpass import getpass
from app import create_app
from app.extensions import db
from app.models import User

app = create_app(os.getenv('FLASK_CONFIG') or 'development')

def create_admin():
    email = input('Enter admin email: ')
    password = getpass('Enter admin password: ')

    with app.app_context():
        admin = User(email=email, password=password, is_admin=True)
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully.')

if __name__ == '__main__':
    create_admin()

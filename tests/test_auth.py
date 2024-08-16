from datetime import datetime
import time
import uuid
import pytest
from unittest.mock import patch
import json
from app import create_app, db
from app.models.user import User
from app.services.auth_service import AuthService
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from flask_mail import Mail, Message
from app.utils import hash_password

@pytest.fixture(scope='module')
def client():
    app = create_app()  # Adjust config if needed
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            user = User(email='testuser@example.com', username='testuser',role='admin', password_hash='testpassword')
            db.session.add(user)
            db.session.commit()
        yield client
        with app.app_context():
            db.drop_all()

@pytest.fixture
def auth_service():
    return AuthService()

@pytest.fixture
def admin_user(client, auth_service):
    unique_username = f"adminuser_{datetime.now().timestamp()}"
    unique_email = f"adminuser_{datetime.now().timestamp()}@example.com"
    
    user_data = {
        "username": unique_username,
        "email": unique_email,
        "password": "adminpassword",
        "role": "admin"  # Set role to admin
    }
    
    auth_service.create_user(user_data)
    
    created_user = db.session.query(User).filter_by(username=unique_username).first()
    if not created_user:
        pytest.fail("Admin user creation failed or user not found in the database.")
    
    access_token = create_access_token(identity={"id": created_user.id, "role": "admin"})
    
    return access_token, {
        "id": created_user.id,
        "username": created_user.username,
        "email": created_user.email,
        "role": created_user.role,
        "password": "adminpassword"  # Include password here
    }


@pytest.fixture
def user(client, auth_service):
    # Generate unique username and email to avoid conflicts
    unique_username = f"testuser_{datetime.now().timestamp()}"
    unique_email = f"testuser_{datetime.now().timestamp()}@example.com"
    
    user_data = {
        "username": unique_username,
        "email": unique_email,
        "password": "testpassword",
        "role": "user"
    }
    
    # Create the user
    auth_service.create_user(user_data)
    
    # Retrieve the user from the database to get the ID
    created_user = db.session.query(User).filter_by(username=unique_username).first()
    if not created_user:
        pytest.fail("User creation failed or user not found in the database.")
    
    # Generate a token for the created user
    access_token = create_access_token(identity={"id": created_user.id, "role": "user"})
    
    return access_token, {
        "id": created_user.id,
        "username": created_user.username,
        'password': 'testpassword',
        "email": created_user.email,
        "role": created_user.role
    }


@pytest.fixture
def token(client, user):
    login_data = {
        "username": user["username"],
        "password": user["password"]
    }
    response = client.post('/signin', json=login_data)
    assert response.status_code == 200
    return response.get_json()["token"]

def test_signup(client):
    new_user_data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "newpassword",
        "role": "user"
    }
    response = client.post('/signup', json=new_user_data)
    assert response.status_code == 201
    response_json = response.get_json()
    assert 'username' in response_json
    assert response_json['username'] == new_user_data['username']

def test_signin(client, user):
    # Unpack the tuple
    token, user_data = user
    
    # Print user_data to debug
    print("User data:", user_data)
    
    login_data = {
        "username": user_data["username"],
        "password": user_data["password"]  # Access the password
    }
    
    response = client.post('/signin', json=login_data)
    assert response.status_code == 200
    assert 'token' in response.get_json()


def test_deactivate_account(client, admin_user):
    token, user_data = admin_user

    # Debug print user_data to verify its structure
    print("User data:", user_data)

    # Verify if 'id' is present in user_data
    user_id = user_data.get('id')
    if user_id is None:
        pytest.fail("User ID is missing in user_data")

    # Check if the user actually exists in the database before attempting to deactivate
    existing_user = db.session.get(User, user_id)
    if existing_user is None:
        pytest.fail(f"User with ID {user_id} does not exist in the database")

    # Prepare the request payload
    payload = {
        "user_id": user_id
    }

    # Make the request with proper JSON content
    response = client.post('/user/deactivate', json=payload, headers={'Authorization': f'Bearer {token}'})

    # Print response details for debugging
    print("Deactivate response status code:", response.status_code)
    print("Deactivate response data:", response.get_data(as_text=True))
    
    # Assert that the response status code is 200 (OK)
    assert response.status_code == 200
    
    # Verify that the user is indeed deactivated
    deactivated_user = db.session.get(User, user_id)
    assert deactivated_user is not None, "User should still exist in the database"
    assert not deactivated_user.active, "User should be deactivated"


def test_activate_account(client, admin_user):
    token, user_data = admin_user

    # Create a new user to activate
    new_user_data = {
        "username": "activateuser",
        "email": "activateuser@example.com",
        "password": "activatepassword",
        "role": "user"
    }
    response = client.post('/signup', json=new_user_data)
    assert response.status_code == 201
    new_user_id = response.get_json()['id']

    print("New user created with ID:", new_user_id)

    # Deactivate the new user first
    deactivate_response = client.post('/user/deactivate', json={'user_id': new_user_id}, headers={'Authorization': f'Bearer {token}'})
    print("Deactivate response status code:", deactivate_response.status_code)
    print("Deactivate response data:", deactivate_response.get_data(as_text=True))
    assert deactivate_response.status_code == 200

    # Now, activate the user
    activate_response = client.post('/user/activate', json={'user_id': new_user_id}, headers={'Authorization': f'Bearer {token}'})
    print("Activate response status code:", activate_response.status_code)
    print("Activate response data:", activate_response.get_data(as_text=True))
    assert activate_response.status_code == 200
    assert 'Account activated successfully' in activate_response.get_json()['message']
    
    # Verify user is activated
    user_in_db = db.session.get(User, new_user_id)
    assert user_in_db is not None
    assert user_in_db.active == True

@patch('flask_mail.Mail.send')
def test_reset_password_request(mock_send, client):
    mock_send.return_value = None

    unique_username = f"testuser_{int(time.time())}"
    unique_email = f"{unique_username}@example.com"
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword",
        "role": "user"
    }

    user = User(
        email=user_data["email"],
        username=user_data["username"],
        password_hash=hash_password(user_data["password"]),
        role=user_data["role"]
    )
    db.session.add(user)
    db.session.commit()

    response = client.post('/reset_password_request', json={"email": unique_email})
    
    print(f"Response data: {response.get_data(as_text=True)}")  # Print response for debugging

    assert response.status_code == 200


@patch('flask_mail.Mail.send')  # Adjust this path to where `mail` is imported in your code
def test_reset_password(mock_send, client):
    mock_send.return_value = None  # Mock mail.send to avoid sending real emails

    # Set up unique user data and create user
    unique_username = f"testuser_{int(time.time())}"
    unique_email = f"{unique_username}@example.com"
    user_data = {
        "email": unique_email,
        "username": unique_username,
        "password": "testpassword",
        "role": "user"
    }

    user = User(
        email=user_data["email"],
        username=user_data["username"],
        password_hash=hash_password(user_data["password"]),      
        role=user_data["role"]
    )
    db.session.add(user)
    db.session.commit()

    # Simulate a reset password request to get a token
    reset_request_data = {
        "email": unique_email
    }
    response = client.post('/reset_password_request', json=reset_request_data)
    print("Reset password request response:", response.get_data(as_text=True))
    assert response.status_code == 200
    response_json = response.get_json()
    reset_token = response_json.get('token', None)
    print("Generated Reset Token:", reset_token)
    
    # Use this token to reset the password
    if reset_token:
        new_password_data = {
            "new_password": "newpassword"
        }
        response = client.post(f'/reset_password/{reset_token}', json=new_password_data)
        print("Reset password response:", response.get_data(as_text=True))
        assert response.status_code == 200
        response_json = response.get_json()
        assert response_json['message'] == 'Password has been reset successfully.'
    else:
        pytest.fail("Reset token not found. Ensure /reset_password_request returns a valid token.")

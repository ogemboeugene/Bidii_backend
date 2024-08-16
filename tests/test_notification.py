import pytest
from app import create_app, db
from app.models import Notification, User
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['JWT_SECRET_KEY'] = 'JWT_SECRET_KEY'  # Set a test JWT secret key

    with app.app_context():
        db.create_all()  # Create tables for testing if not already created

        # Create a test user
        test_user = User(username='test_user', email='test@example.com', password_hash='password123', role='admin')
        db.session.add(test_user)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_token(client):
    # Generate a test JWT token for the test user
    with client.application.app_context():
        test_user = User.query.filter_by(username='test_user').first()
        test_token = create_access_token(identity=test_user.id, expires_delta=timedelta(days=1))
        return test_token

@pytest.fixture
def notification_data():
    return {
        'message': 'Test notification message',
        'created_at': datetime.utcnow().isoformat(),
        'user_id': 1,
        'read': False
    }

@pytest.fixture
def setup_notifications(client, test_token):
    """Fixture to create notifications for testing."""
    notifications = [
        Notification(user_id=1, message='Test notification 1', created_at=datetime.utcnow(), read=False),
        Notification(user_id=1, message='Test notification 2', created_at=datetime.utcnow(), read=False),
        Notification(user_id=2, message='Test notification 3', created_at=datetime.utcnow(), read=False)  # Different user
    ]
    db.session.add_all(notifications)
    db.session.commit()
    
    return [n.id for n in notifications if n.user_id == 1]  # Return IDs for user 1


def test_create_notification(client, test_token):
    notification_data = {
        'created_at': datetime.utcnow().isoformat(),  # Ensure ISO format
        'message': 'Test notification message',
        'read': False,
        'user_id': 1
    }
    response = client.post('/notifications', json=notification_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201

def test_get_notifications(client, test_token):
    response = client.get('/notifications', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    assert len(response.json) > 0

def test_get_notification(client, test_token):
    response = client.get('/notifications', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    notifications = response.json
    assert len(notifications) > 0

    notification_id = notifications[0]['id']
    response = client.get(f'/notifications/{notification_id}', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    assert 'id' in response.json

def test_update_notification(client, test_token, notification_data):
    response = client.post('/notifications', json=notification_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    notification_id = response.json['id']

    updated_data = {
        'message': 'Updated notification message',
        'read': True
    }
    response = client.put(f'/notifications/{notification_id}', json=updated_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200

    with client.application.app_context():
        session = Session(db.engine)
        notification = session.get(Notification, notification_id)
        assert notification is not None
        assert notification.message == updated_data['message']
        assert notification.read == updated_data['read']
        session.close()

def test_delete_notification(client, test_token, notification_data):
    response = client.post('/notifications', json=notification_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    notification_id = response.json['id']

    response = client.delete(f'/notifications/{notification_id}', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200

    with client.application.app_context():
        session = Session(db.engine)
        notification = session.get(Notification, notification_id)
        assert notification is None
        session.close()

def test_mark_as_read(client, test_token, notification_data):
    response = client.post('/notifications', json=notification_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    notification_id = response.json['id']

    response = client.put(f'/notifications/{notification_id}/read', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200

    with client.application.app_context():
        session = Session(db.engine)
        notification = session.get(Notification, notification_id)
        assert notification.read is True
        session.close()

def test_mark_as_unread(client, test_token, notification_data):
    response = client.post('/notifications', json=notification_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    notification_id = response.json['id']

    response = client.put(f'/notifications/{notification_id}/unread', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200

    with client.application.app_context():
        session = Session(db.engine)
        notification = session.get(Notification, notification_id)
        assert notification.read is False
        session.close()

def test_mark_multiple_as_read(client, test_token, setup_notifications):
    notification_ids = setup_notifications  # IDs of notifications for user 1

    # Send PUT request to mark notifications as read
    response = client.put('/notifications/read', json={'notification_ids': notification_ids}, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    assert response.json['message'] == 'Notifications marked as read'

    # Check that notifications are marked as read in the database
    for notification_id in notification_ids:
        notification = Notification.query.get(notification_id)
        assert notification.read is True

def test_delete_multiple_notifications(client, test_token, notification_data):
    response = client.post('/notifications', json=notification_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    notification_id = response.json['id']

    response = client.delete('/notifications/delete', json={'notification_ids': [notification_id]}, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200

    with client.application.app_context():
        session = Session(db.engine)
        notification = session.get(Notification, notification_id)
        assert notification is None
        session.close()

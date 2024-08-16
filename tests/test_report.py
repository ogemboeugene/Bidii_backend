from flask import json
import pytest
from app import create_app, db
from app.models import Report, User
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.schemas import ReportSchema
from marshmallow.exceptions import ValidationError

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['JWT_SECRET_KEY'] = 'JWT_SECRET_KEY'  # Set a test JWT secret key

    with app.app_context():
        db.create_all()  # Create tables for testing if not already created

        # Create test users
        admin_user = User(username='admin_user', email='admin@example.com', password_hash='password123', role='admin')
        regular_user = User(username='regular_user', email='user@example.com', password_hash='password123', role='user')
        db.session.add_all([admin_user, regular_user])
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_token(client):
    with client.application.app_context():
        admin_user = User.query.filter_by(username='admin_user').first()
        token = create_access_token(identity=admin_user.id, expires_delta=timedelta(days=1))
        return token

@pytest.fixture
def user_token(client):
    with client.application.app_context():
        regular_user = User.query.filter_by(username='regular_user').first()
        token = create_access_token(identity=regular_user.id, expires_delta=timedelta(days=1))
        return token

@pytest.fixture
def report_data():
    return {
        'title': 'Test Report',
        'content': 'This is a test report.',
        'created_at': datetime.utcnow().isoformat()
    }

@pytest.fixture
def setup_reports(client, admin_token):
    """Fixture to create reports for testing."""
    reports = [
        Report(title='Report A', content='Content A', created_at=datetime.utcnow()),
        Report(title='Report B', content='Content B', created_at=datetime.utcnow())
    ]
    db.session.add_all(reports)
    db.session.commit()

    return [r.id for r in reports]  # Return IDs for further use

@pytest.fixture
def valid_report_data():
    return {
        'id': 1,
        'user_id': 2,
        'message': 'Sample report message',
        'created_at': '2024-07-20T12:00:00',
        'read': False
    }

@pytest.fixture
def invalid_report_data():
    return {
        'user_id': 'not_an_int',
        'message': '',
        'created_at': 'invalid_date_format',
        'read': 'not_a_boolean'
    }


def test_report_schema_invalid_data():
    schema = ReportSchema()
    invalid_data = {
        'user_id': 'not_an_int',  # Invalid type
        'message': '',  # Message should not be empty
        'created_at': 'invalid_date_format',
        'read': 'not_a_boolean'  # Invalid type
    }
    with pytest.raises(ValidationError):
        schema.load(invalid_data, session=db.session)

# def test_report_schema_serialize():
#     schema = ReportSchema()
#     data = {
#         'id': 1,
#         'user_id': 2,
#         'message': 'This is a report',
#         'created_at': '2024-07-20T12:00:00',
#         'read': False
#     }
#     # Simulating a SQLAlchemy model instance
#     report_instance = Report(**data)
#     result = schema.dump(report_instance)
#     assert result['id'] == data['id']
#     assert result['user_id'] == data['user_id']
#     assert result['message'] == data['message']
#     assert result['created_at'] == data['created_at']
#     assert result['read'] == data['read']

def test_report_schema_message_length():
    schema = ReportSchema()
    long_message = 'a' * 1001  # Assuming max length for 'message' is 1000
    data = {
        'id': 1,
        'user_id': 2,
        'message': long_message,
        'created_at': '2024-07-20T12:00:00',
        'read': False
    }
    with pytest.raises(ValidationError):
        schema.load(data, session=db.session)

def test_report_schema_missing_fields():
    schema = ReportSchema()
    data = {
        'user_id': 2,
        'message': 'This is a report',
        'created_at': '2024-07-20T12:00:00',
        'read': False
    }
    with pytest.raises(ValidationError):
        schema.load(data, session=db.session)  # Missing 'id'

def test_create_report(client, admin_token, report_data):
    response = client.post('/reports', json=report_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    assert 'id' in response.json  # Ensure that the response contains an ID


def test_create_report(client, admin_token):
    report_data = {
        'title': 'Test Report',
        'content': 'This is a test report.',
        'created_at': '2024-07-20T15:25:42.956870'
    }
    response = client.post(
        '/reports',
        json=report_data,
        headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == 201
    response_json = json.loads(response.data)
    assert 'title' in response_json
    assert 'content' in response_json
    assert 'created_at' in response_json

def test_create_report_without_token(client):
    report_data = {
        'title': 'Test Report',
        'content': 'This is a test report.',
        'created_at': '2024-07-20T15:25:42.956870'
    }
    response = client.post(
        '/reports',
        json=report_data
    )

    print(response.data)  # Debugging line
    assert response.status_code == 401
    response_json = json.loads(response.data)
    assert 'msg' in response_json
    assert response_json['msg'] == 'Missing Authorization Header'

def test_create_report_with_invalid_data(client, admin_token):
    # Missing 'title' field
    report_data = {
        'content': 'This is a test report.',
        'created_at': '2024-07-20T15:25:42.956870'
    }
    response = client.post(
        '/reports',
        json=report_data,
        headers={'Authorization': f'Bearer {admin_token}'}
    )

    assert response.status_code == 400
    response_json = json.loads(response.data)
    assert 'error' in response_json
def test_get_report(client, admin_token, setup_reports):
    report_id = setup_reports[0]
    response = client.get(f'/reports/{report_id}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert 'id' in response.json
    assert response.json['id'] == report_id

def test_update_report(client, admin_token, report_data, setup_reports):
    report_id = setup_reports[0]
    updated_data = {'title': 'Updated Report', 'content': 'Updated content'}
    response = client.put(f'/reports/{report_id}', json=updated_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert response.json['title'] == 'Updated Report'

    # Verify the update
    with client.application.app_context():
        session = Session(db.engine)
        report = session.get(Report, report_id)
        assert report is not None
        assert report.title == updated_data['title']
        session.close()

def test_delete_report(client, admin_token, setup_reports):
    report_id = setup_reports[0]
    response = client.delete(f'/reports/{report_id}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert response.json['message'] == 'Report deleted successfully'

    with client.application.app_context():
        session = Session(db.engine)
        report = session.get(Report, report_id)
        assert report is None
        session.close()

def test_get_reports_by_user(client, admin_token):
    # This test assumes the ReportService.get_reports_by_user method is properly implemented.
    response = client.get('/reports/user/1', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_search_reports(client, admin_token):
    # Test with query parameters
    response = client.get('/reports/search', query_string={'query': 'Test', 'user_id': 1}, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert isinstance(response.json, list)

def test_get_recent_reports(client, admin_token):
    response = client.get('/reports/recent', query_string={'limit': 5}, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert isinstance(response.json, list)

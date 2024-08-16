from flask_jwt_extended import create_access_token
import pytest
from app import create_app, db
from app.models import AdminLog, User
from app.schemas import AdminLogSchema

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def init_db(app):
    with app.app_context():
        db.create_all()

        admin_user = User(username='admin', email='admin@example.com', role='admin')
        admin_user.set_password('adminpassword')
        db.session.add(admin_user)
        db.session.commit()

        yield db

        db.session.remove()
        db.drop_all()

@pytest.fixture
def admin_token(app):
    with app.app_context():
        user = User.query.filter_by(username='admin').first()
        token = create_access_token(identity=user.id)
        return token
    
@pytest.fixture
def admin_log_data():
    return {
        'admin_id': 1,
        'action': 'login',
        'details': 'Admin logged in successfully.'
    }

def test_admin_log_schema_load_instance(app, admin_log_data):
    schema = AdminLogSchema()
    with app.app_context():
        admin_log = schema.load(admin_log_data, session=db.session)
    assert admin_log.admin_id == admin_log_data['admin_id']
    assert admin_log.action == admin_log_data['action']
    assert admin_log.details == admin_log_data['details']

def test_admin_log_schema_dump_instance(admin_log_data):
    admin_log = AdminLog(**admin_log_data)
    schema = AdminLogSchema()
    result = schema.dump(admin_log)
    assert result['admin_id'] == admin_log_data['admin_id']
    assert result['action'] == admin_log_data['action']
    assert result['details'] == admin_log_data['details']

def test_create_admin_log(client, init_db, admin_token, admin_log_data):
    headers = {'Authorization': f'Bearer {admin_token}'}
    response = client.post('/admin/logs', headers=headers, json=admin_log_data)
    
    print("Status Code:", response.status_code)
    print("Response Data:", response.get_data(as_text=True))  # Print response data for debugging
    
    assert response.status_code == 201
    data = response.get_json()
    assert data['action'] == admin_log_data['action']
    assert data['admin_id'] == admin_log_data['admin_id']
    assert data['details'] == admin_log_data['details']

def test_get_admin_logs(client, init_db, admin_token):
    # First, create a sample admin log to ensure the GET request has data to retrieve
    headers = {'Authorization': f'Bearer {admin_token}'}
    admin_log_data = {
        'admin_id': 1,
        'action': 'login',
        'details': 'Admin logged in successfully.'
    }
    client.post('/admin/logs', headers=headers, json=admin_log_data)

    # Now, fetch the admin logs
    response = client.get('/admin/logs', headers=headers)
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) > 0  # Ensure that there is at least one log
    assert data[0]['action'] == admin_log_data['action']
    assert data[0]['admin_id'] == admin_log_data['admin_id']
    assert data[0]['details'] == admin_log_data['details']

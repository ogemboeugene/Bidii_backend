import pytest
from datetime import datetime, timedelta
from flask_jwt_extended import create_access_token
from app import create_app, db
from app.models import User, SavingsAccount, SavingsTransaction

@pytest.fixture(scope='module')
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    app.config['JWT_SECRET_KEY'] = 'JWT_SECRET_KEY'  # Set a test JWT secret key

    with app.app_context():
        db.create_all()  # Create tables for testing

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
def setup_savings_account(client, admin_token):
    """Fixture to create a savings account for testing."""
    data = {
        'user_id': 1,
        'balance': 1000.00
    }
    response = client.post('/savings', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    return response.json['id']

@pytest.fixture
def setup_savings_transaction(client, setup_savings_account, admin_token):
    """Fixture to create a savings transaction for testing."""
    data = {
        'amount': 100.00
    }
    response = client.post(f'/savings/{setup_savings_account}/transactions', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    return response.json['id']

def test_create_savings_account(client, admin_token):
    data = {
        "user_id": 1,
        "balance": 1000.0
    }
    response = client.post('/savings', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    print(response.data)  # Print the response data for debugging
    assert response.status_code == 201
    assert 'id' in response.json
    assert response.json['balance'] == 1000.0

def test_get_savings_account(client, setup_savings_account, admin_token):
    response = client.get(f'/savings/{setup_savings_account}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert 'id' in response.json
    assert response.json['balance'] == 1000.0

def test_update_savings_account(client, setup_savings_account, admin_token):
    data = {
        'balance': 1500.00
    }
    response = client.put(f'/savings/{setup_savings_account}', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert response.json['balance'] == 1500.00

def test_delete_savings_account(client, setup_savings_account, admin_token):
    response = client.delete(f'/savings/{setup_savings_account}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 204

    response = client.get(f'/savings/{setup_savings_account}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 404

def test_create_transaction(client, setup_savings_account, admin_token):
    data = {
        'amount': 200.00
    }
    response = client.post(f'/savings/{setup_savings_account}/transactions', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    assert 'amount' in response.json
    assert response.json['amount'] == 200.00

def test_get_transactions(client, setup_savings_account, setup_savings_transaction, admin_token):
    response = client.get(f'/savings/{setup_savings_account}/transactions', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert isinstance(response.json, list)
    assert len(response.json) > 0

# def test_filter_transactions(client, setup_savings_account, setup_savings_transaction, admin_token):
#     from datetime import datetime, timedelta
#     start_date = datetime.utcnow().isoformat()
#     end_date = (datetime.utcnow() + timedelta(days=1)).isoformat()

#     print(f"Start Date: {start_date}")
#     print(f"End Date: {end_date}")

#     response = client.get(f'/savings/{setup_savings_account}/transactions/filter', query_string={'start_date': start_date, 'end_date': end_date}, headers={'Authorization': f'Bearer {admin_token}'})
#     assert response.status_code == 200
#     assert isinstance(response.json, list)
#     print(f"Filtered Transactions: {response.json}")
#     assert len(response.json) > 0

def test_get_balance(client, setup_savings_account, admin_token):
    response = client.get(f'/savings/{setup_savings_account}/balance', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert 'balance' in response.json
    assert response.json['balance'] == 1000.00

# # def test_savings_account_schema_load_instance(savings_account_data):
# #     schema = SavingsAccountSchema()
# #     savings_account = schema.load(savings_account_data)
# #     assert savings_account.account_holder == savings_account_data['account_holder']
# #     assert savings_account.balance == savings_account_data['balance']
# #     assert savings_account.interest_rate == savings_account_data['interest_rate']

# # def test_savings_account_schema_dump_instance(savings_account_data):
# #     savings_account = SavingsAccount(**savings_account_data)
# #     schema = SavingsAccountSchema()
# #     result = schema.dump(savings_account)
# #     assert result == savings_account_data

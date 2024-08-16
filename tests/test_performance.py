import pytest
from app import create_app, db
from app.models import GroupMonthlyPerformance, MonthlyPerformance, User
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.schemas import GroupMonthlyPerformanceSchema, MonthlyPerformanceSchema

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
def performance_data():
    return {
        'group_name': 'Test Group',
        'savings_shares_bf': 1000,
        'loan_balance_bf': 5000,
        'total_paid': 1500,
        'principal': 800,
        'loan_interest': 200,
        'this_month_shares': 200,
        'fine_and_charges': 50,
        'savings_shares_cf': 1200,
        'loan_cf': 5500,
        'month': 'January',
        'year': 2024
    }

@pytest.fixture
def setup_group_performances(client, admin_token):
    """Fixture to create group performances for testing."""
    performances = [
        GroupMonthlyPerformance(
            group_name='Group A',
            savings_shares_bf=1000,
            loan_balance_bf=5000,
            total_paid=1500,
            principal=800,
            loan_interest=200,
            this_month_shares=200,
            fine_and_charges=50,
            savings_shares_cf=1200,
            loan_cf=5500,
            month='January',
            year=2024
        ),
        GroupMonthlyPerformance(
            group_name='Group B',
            savings_shares_bf=1500,
            loan_balance_bf=6000,
            total_paid=2000,
            principal=1000,
            loan_interest=300,
            this_month_shares=300,
            fine_and_charges=60,
            savings_shares_cf=1500,
            loan_cf=6000,
            month='February',
            year=2024
        )
    ]
    db.session.add_all(performances)
    db.session.commit()

    return [p.id for p in performances]  # Return IDs for further use

@pytest.fixture
def setup_monthly_performances(client, admin_token):
    """Fixture to create monthly performances for testing."""
    performances = [
        MonthlyPerformance(
            group_name='Group A',
            banking=2000,
            sf=500,
            pb=300,
            od_paid=100,
            month='January',
            year=2024
        ),
        MonthlyPerformance(
            group_name='Group B',
            banking=2500,
            sf=600,
            pb=400,
            od_paid=150,
            month='February',
            year=2024
        )
    ]
    db.session.add_all(performances)
    db.session.commit()

    return [p.id for p in performances]  # Return IDs for further use

# Group Performance Tests

def test_create_group_performance(client, admin_token, performance_data):
    response = client.post('/group_performances', json=performance_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    assert b'Group performance created successfully' in response.data

def test_get_group_performances(client, admin_token):
    response = client.get('/group_performances', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert len(response.json) > 0

def test_get_group_performance(client, admin_token, setup_group_performances):
    performance_id = setup_group_performances[0]
    response = client.get(f'/group_performances/{performance_id}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert 'id' in response.json

def test_update_group_performance(client, admin_token, performance_data):
    # Create a new group performance record
    response = client.post('/group_performances', json=performance_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    response_json = response.json
    assert 'id' in response_json, "The response does not contain the 'id' key"
    performance_id = response_json['id']

    # Update the created group performance record
    updated_data = {
        'savings_shares_bf': 2000,
        'loan_balance_bf': 7000,
        'total_paid': 2500,
        'principal': 1000,
        'loan_interest': 400,
        'this_month_shares': 300,
        'fine_and_charges': 70,
        'savings_shares_cf': 1500,
        'loan_cf': 6000,
        'month': 'February',
        'year': 2024
    }
    response = client.put(f'/group_performances/{performance_id}', json=updated_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200

    # Validate the updated performance record
    with client.application.app_context():
        session = Session(db.engine)
        performance = session.get(GroupMonthlyPerformance, performance_id)
        assert performance is not None
        assert performance.savings_shares_bf == updated_data['savings_shares_bf']
        assert performance.loan_balance_bf == updated_data['loan_balance_bf']
        session.close()


def test_delete_group_performance(client, admin_token, performance_data):
    response = client.post('/group_performances', json=performance_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    performance_id = response.json['id']

    response = client.delete(f'/group_performances/{performance_id}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200

    with client.application.app_context():
        session = Session(db.engine)
        performance = session.get(GroupMonthlyPerformance, performance_id)
        assert performance is None
        session.close()

def test_bulk_create_group_performances(client, admin_token):
    data = [
        {
            'group_name': 'Group C',
            'savings_shares_bf': 2000,
            'loan_balance_bf': 7000,
            'total_paid': 2500,
            'principal': 1000,
            'loan_interest': 400,
            'this_month_shares': 300,
            'fine_and_charges': 70,
            'savings_shares_cf': 1500,
            'loan_cf': 6000,
            'month': 'March',
            'year': 2024
        },
        {
            'group_name': 'Group D',
            'savings_shares_bf': 3000,
            'loan_balance_bf': 8000,
            'total_paid': 3500,
            'principal': 1500,
            'loan_interest': 500,
            'this_month_shares': 400,
            'fine_and_charges': 80,
            'savings_shares_cf': 1800,
            'loan_cf': 7000,
            'month': 'March',
            'year': 2024
        }
    ]
    response = client.post('/group_performances/bulk', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    assert b'Group performances created successfully' in response.data

def test_bulk_delete_group_performances(client, admin_token, setup_group_performances):
    ids_to_delete = setup_group_performances

    response = client.delete('/group_performances/delete', json={'performance_ids': ids_to_delete}, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert response.json['message'] == 'Group performances deleted successfully'

    with client.application.app_context():
        session = Session(db.engine)
        for performance_id in ids_to_delete:
            performance = session.get(GroupMonthlyPerformance, performance_id)
            assert performance is None
        session.close()

# # Monthly Performance Tests

def test_create_monthly_performance(client, admin_token, performance_data):
    response = client.post('/monthly_performances', json=performance_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    assert b'Monthly performance created' in response.data

def test_get_monthly_performances(client, admin_token):
    response = client.get('/monthly_performances', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert len(response.json) > 0

def test_get_monthly_performance(client, admin_token, setup_monthly_performances):
    performance_id = setup_monthly_performances[0]
    response = client.get(f'/monthly_performances/{performance_id}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert 'id' in response.json

def test_update_monthly_performance(client, admin_token, performance_data):
    # Create a new performance
    data = {
        'group_name': performance_data['group_name'],
        'banking': 2000,
        'sf': 500,
        'pb': 300,
        'od_paid': 100,
        'month': 'January',
        'year': 2024
    }
    response = client.post('/monthly_performances', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    assert 'id' in response.json
    performance_id = response.json['id']

    # Update the performance
    updated_data = {
        'group_name': performance_data['group_name'],
        'banking': 2500,
        'sf': 600,
        'pb': 350,
        'od_paid': 150,
        'month': 'February',
        'year': 2024
    }
    response = client.put(f'/monthly_performances/{performance_id}', json=updated_data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200

    # Verify the update
    with client.application.app_context():
        session = Session(db.engine)
        performance = session.get(MonthlyPerformance, performance_id)
        assert performance is not None
        assert performance.banking == updated_data['banking']
        assert performance.sf == updated_data['sf']
        session.close()

def test_delete_monthly_performance(client, admin_token, performance_data):
    data = {
        'group_name': performance_data['group_name'],
        'banking': 2000,
        'sf': 500,
        'pb': 300,
        'od_paid': 100,
        'month': 'January',
        'year': 2024
    }
    response = client.post('/monthly_performances', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    performance_id = response.json['id']

    response = client.delete(f'/monthly_performances/{performance_id}', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200

    with client.application.app_context():
        session = Session(db.engine)
        performance = session.get(MonthlyPerformance, performance_id)
        assert performance is None
        session.close()

def test_bulk_create_monthly_performances(client, admin_token):
    data = [
        {
            'group_name': 'Group A',
            'banking': 2000,
            'sf': 500,
            'pb': 300,
            'od_paid': 100,
            'month': 'March',
            'year': 2024
        },
        {
            'group_name': 'Group B',
            'banking': 2500,
            'sf': 600,
            'pb': 400,
            'od_paid': 150,
            'month': 'March',
            'year': 2024
        }
    ]
    response = client.post('/monthly_performances/bulk', json=data, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 201
    assert b'Monthly performances created successfully' in response.data

def test_bulk_delete_monthly_performances(client, admin_token, setup_monthly_performances):
    ids_to_delete = setup_monthly_performances

    response = client.delete('/monthly_performances/delete', json={'performance_ids': ids_to_delete}, headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 200
    assert response.json['message'] == 'Monthly performances deleted successfully'

    with client.application.app_context():
        session = Session(db.engine)
        for performance_id in ids_to_delete:
            performance = session.get(MonthlyPerformance, performance_id)
            assert performance is None
        session.close()

def test_get_nonexistent_monthly_performance(client, admin_token):
    response = client.get('/monthly_performances/99999', headers={'Authorization': f'Bearer {admin_token}'})
    assert response.status_code == 404
    assert b'Monthly performance not found' in response.data


# @pytest.fixture
# def group_monthly_performance_data():
#     return {
#         'id': 1,
#         'month': '2024-06',
#         'revenue': 100000,
#         'expenses': 50000,
#         'profit': 50000
#     }

# def test_group_monthly_performance_schema_load_instance(group_monthly_performance_data):
#     schema = GroupMonthlyPerformanceSchema()
#     group_performance = schema.load(group_monthly_performance_data)
#     assert group_performance.id == group_monthly_performance_data['id']
#     assert group_performance.month == group_monthly_performance_data['month']
#     assert group_performance.revenue == group_monthly_performance_data['revenue']
#     assert group_performance.expenses == group_monthly_performance_data['expenses']
#     assert group_performance.profit == group_monthly_performance_data['profit']

# def test_group_monthly_performance_schema_dump_instance(group_monthly_performance_data):
#     group_performance = GroupMonthlyPerformance(**group_monthly_performance_data)
#     schema = GroupMonthlyPerformanceSchema()
#     result = schema.dump(group_performance)
#     assert result == group_monthly_performance_data

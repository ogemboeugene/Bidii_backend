import pytest
from datetime import datetime
from app import create_app, db
from app.models import LoanAgreement, LoanRepayment
from app.models.loan import PaymentStatus
from app.models.user import User
from flask_jwt_extended import create_access_token
from datetime import timedelta
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
def loan_agreement_data():
    return {
        'borrower_name': 'John Doe',
        'borrower_id': 'JD123',
        'borrower_phone': '1234567890',
        'borrower_email': 'john.doe@example.com',
        'group_lender': 'ABC Lending Group',
        'loan_amount': 10000.0,
        'interest_rate': 5.0,
        'payment_amount': 1500.0,
        'payment_months': 12,
        'purpose': 'Business expansion',
        'collateral': 'Property',
        'guarantors': ['Jane Smith', 'Michael Brown'],
        'status': 'pending',
        'document_url': 'http://example.com/document.pdf'
    }

@pytest.fixture
def loan_repayment_data():
    return {
        'due_date': datetime.now().date(),
        'amount': 1500.0,
        'balance': 0.0,
        'payment_method': 'Bank transfer',
        'payment_reference': 'REF123',
        'status': PaymentStatus.PENDING.value
    }

# Test cases with JWT token included in headers
def test_create_loan_agreement(client, test_token, loan_agreement_data):
    # Print or assert the JWT token to ensure it's correctly generated
    # print(f"Test Token: {test_token}")
    # print(f"Loan Agreement Data: {loan_agreement_data}")

    # Make the request with the token in the Authorization header
    response = client.post('/loans', json=loan_agreement_data, headers={'Authorization': f'Bearer {test_token}'})

    # Print response details for debugging
    # print(f"Response Status Code: {response.status_code}")
    # print(f"Response Data: {response.data}")

    # Assert the HTTP status code
    assert response.status_code == 201, f"Expected status code 201, but got {response.status_code}. Response data: {response.data}"

    # Ensure the response contains the loan agreement data
    assert 'id' in response.json, "Expected 'id' in response JSON, but it's missing."
    loan_id = response.json['id']

    # Verify data in the database
    with client.application.app_context():
        # loan = LoanAgreement.query.get(loan_id)
        session = Session(db.engine)
        loan = session.get(LoanAgreement, loan_id)
        assert loan.borrower_name == loan_agreement_data['borrower_name']
        assert loan.borrower_id == loan_agreement_data['borrower_id']
        assert loan.borrower_phone == loan_agreement_data['borrower_phone']
        assert loan.borrower_email == loan_agreement_data['borrower_email']
        assert loan.group_lender == loan_agreement_data['group_lender']
        assert loan.loan_amount == loan_agreement_data['loan_amount']
        assert loan.interest_rate == loan_agreement_data['interest_rate']
        assert loan.payment_amount == loan_agreement_data['payment_amount']
        assert loan.payment_months == loan_agreement_data['payment_months']
        assert loan.purpose == loan_agreement_data['purpose']
        assert loan.collateral == loan_agreement_data['collateral']
        assert loan.guarantors == loan_agreement_data['guarantors']
        assert loan.status == loan_agreement_data['status']
        assert loan.document_url == loan_agreement_data['document_url']
        session.close()


def test_get_loan_agreement(client, test_token):
    # Assuming at least one loan agreement exists in the database
    response = client.get('/loans', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    
    # Check if there is at least one loan agreement returned
    assert len(response.json) > 0, "Expected at least one loan agreement, but none were found in the response"

    # Assuming the first item in the response list has an 'id' field
    loan_id = response.json[0]['id']
    response = client.get(f'/loans/{loan_id}', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    assert 'id' in response.json, f"Expected 'id' field in loan details, but got {response.json}"

    # Verify data in the database
    with client.application.app_context():
        session = Session(db.engine)
        loan = session.get(LoanAgreement, loan_id)
        assert loan is not None, f"Loan with ID {loan_id} was not found in the database"
        session.close()

def test_update_loan_agreement(client, test_token, loan_agreement_data):
    # Create a loan agreement first
    response = client.post('/loans', json=loan_agreement_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    loan_id = response.json['id']

    # Update loan agreement
    updated_data = {
        'borrower_name': 'Updated Name',
        'loan_amount': 12000.0,
        'status': 'approved'
        # Add more fields as needed
    }
    response = client.put(f'/loans/{loan_id}', json=updated_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200

    # Verify updated data in the database
    with client.application.app_context():
        session = Session(db.engine)
        updated_loan = session.get(LoanAgreement, loan_id)
        assert updated_loan.borrower_name == updated_data['borrower_name']
        assert updated_loan.loan_amount == updated_data['loan_amount']
        assert updated_loan.status == updated_data['status']
        session.close()

def test_delete_loan_agreement(client, test_token, loan_agreement_data):
    # Create a loan agreement first
    response = client.post('/loans', json=loan_agreement_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    loan_id = response.json['id']

    # Delete the loan agreement
    response = client.delete(f'/loans/{loan_id}', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200

    # Verify deletion
    with client.application.app_context():
        session = Session(db.engine)
        deleted_loan = session.get(LoanAgreement, loan_id)
        assert deleted_loan is None
        session.close()

def test_update_repayment(client, test_token, loan_agreement_data, loan_repayment_data):
    # Create a loan agreement first
    response = client.post('/loans', json=loan_agreement_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    loan_id = response.json['id']

    # Ensure due_date is a string in the correct format
    if isinstance(loan_repayment_data['due_date'], datetime):
        loan_repayment_data['due_date'] = loan_repayment_data['due_date'].strftime('%Y-%m-%d')
    elif isinstance(loan_repayment_data['due_date'], str):
        # Try to convert to datetime object and then format as string
        try:
            loan_repayment_data['due_date'] = datetime.strptime(loan_repayment_data['due_date'], '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d')
        except ValueError:
            pass  # If conversion fails, assume it's already correctly formatted

    # Create a repayment
    response = client.post(f'/loans/{loan_id}/repayments', json=loan_repayment_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    repayment_id = response.json['repayment']['id']

    # Prepare updated data with correct date format
    updated_data = {
        'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),  # Format date as 'YYYY-MM-DD'
        'amount': 2000.0
    }
    response = client.put(f'/loans/{loan_id}/repayments/{repayment_id}', json=updated_data, headers={'Authorization': f'Bearer {test_token}'})
    
    # Debug response
    print(response.json)  # Add this line to understand the error response
    
    assert response.status_code == 200
    
    # Verify the updated data in the response
    updated_repayment_response = response.json
    assert updated_repayment_response['due_date'] == updated_data['due_date']
    assert updated_repayment_response['amount'] == updated_data['amount']

    # Verify updated data in the database
    with client.application.app_context():
        session = Session(db.engine)
        updated_repayment = session.get(LoanRepayment, repayment_id)
        assert updated_repayment is not None  # Ensure the repayment exists
        assert updated_repayment.due_date.strftime('%Y-%m-%d') == updated_data['due_date']
        assert updated_repayment.amount == updated_data['amount']
        
def test_get_repayment(client, test_token):
    # Fetch all loans to ensure at least one exists
    response = client.get('/loans', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    loans = response.json
    assert len(loans) > 0  # Ensure there is at least one loan

    loan_id = loans[0]['id']
    
    # Create a repayment for the selected loan
    loan_repayment_data = {
        'due_date': '2024-07-18',
        'amount': 1500.0,
        'balance': 0.0,
        'payment_method': 'Bank transfer',
        'payment_reference': 'REF123',
        'status': PaymentStatus.PENDING.value
    }
    response = client.post(f'/loans/{loan_id}/repayments', json=loan_repayment_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    
    # Fetch repayments for the selected loan
    response = client.get(f'/loans/{loan_id}/repayments', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    repayments = response.json
    print(f"Repayments: {repayments}")  # Add this line for debugging
    assert len(repayments) > 0  # Ensure there is at least one repayment


def test_update_repayment(client, test_token, loan_agreement_data, loan_repayment_data):
    # Debug: Initial data
    # print("Initial loan agreement data:", loan_agreement_data)
    # print("Initial loan repayment data:", loan_repayment_data)

    # Create a loan agreement first
    response = client.post('/loans', json=loan_agreement_data, headers={'Authorization': f'Bearer {test_token}'})
    # print("Loan agreement creation response:", response.json)
    assert response.status_code == 201
    loan_id = response.json['id']

    # Ensure due_date is a string in the correct format
    if isinstance(loan_repayment_data['due_date'], datetime):
        loan_repayment_data['due_date'] = loan_repayment_data['due_date'].strftime('%Y-%m-%d')
    elif isinstance(loan_repayment_data['due_date'], str):
        # Try to convert to datetime object and then format as string
        try:
            loan_repayment_data['due_date'] = datetime.strptime(loan_repayment_data['due_date'], '%a, %d %b %Y %H:%M:%S %Z').strftime('%Y-%m-%d')
        except ValueError:
            pass  # If conversion fails, assume it's already correctly formatted
    else:
        # Convert to string assuming it's a date object
        loan_repayment_data['due_date'] = loan_repayment_data['due_date'].strftime('%Y-%m-%d')

    # Debug: Formatted loan repayment data
    # print("Formatted loan repayment data:", loan_repayment_data)

    # Create a repayment
    response = client.post(f'/loans/{loan_id}/repayments', json=loan_repayment_data, headers={'Authorization': f'Bearer {test_token}'})
    # print("Loan repayment creation response:", response.json)
    assert response.status_code == 201
    repayment_id = response.json['repayment']['id']

    # Prepare updated data with correct date format
    updated_data = {
        'due_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),  # Format date as 'YYYY-MM-DD'
        'amount': 2000.0
    }

    # Debug: Updated data
    # print("Updated repayment data:", updated_data)

    response = client.put(f'/loans/{loan_id}/repayments/{repayment_id}', json=updated_data, headers={'Authorization': f'Bearer {test_token}'})
    # print("Loan repayment update response:", response.json)
    
    # Debug: Response status code
    # print("Response status code:", response.status_code)
    
    assert response.status_code == 200

    # Verify the updated data in the response
    updated_repayment_response = response.json
    # print("Updated repayment response data:", updated_repayment_response)
    assert updated_repayment_response['due_date'] == updated_data['due_date']
    assert updated_repayment_response['amount'] == updated_data['amount']

    # Verify updated data in the database
    with client.application.app_context():
        session = Session(db.engine)
        updated_repayment = session.get(LoanRepayment, repayment_id)
        # print("Updated repayment in DB:", updated_repayment)
        assert updated_repayment is not None  # Ensure the repayment exists
        assert updated_repayment.due_date.strftime('%Y-%m-%d') == updated_data['due_date']
        assert updated_repayment.amount == updated_data['amount']

def test_delete_repayment(client, test_token, loan_agreement_data, loan_repayment_data):
    # Create a loan agreement first
    response = client.post('/loans', json=loan_agreement_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    loan_id = response.json['id']

    # Correct the date format in loan_repayment_data
    loan_repayment_data['due_date'] = loan_repayment_data['due_date'].strftime('%Y-%m-%d')

    # Create a repayment
    response = client.post(f'/loans/{loan_id}/repayments', json=loan_repayment_data, headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 201
    repayment_id = response.json['repayment']['id']

    # Delete the repayment
    response = client.delete(f'/loans/{loan_id}/repayments/{repayment_id}', headers={'Authorization': f'Bearer {test_token}'})
    assert response.status_code == 200
    assert response.json.get('message') == 'Repayment deleted successfully'  # Check for a message or confirmation in the response

    # Verify that the repayment is deleted from the database
    session: Session = db.session
    deleted_repayment = session.get(LoanRepayment, repayment_id)
    assert deleted_repayment is None

# # Add more test cases as needed


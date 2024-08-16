# tests/test_transaction.py
import pytest
from app.models.transaction import Transaction
from app.services.transaction_service import TransactionService

@pytest.fixture
def setup_transaction():
    yield TransactionService()

def test_create_transaction(setup_transaction):
    transaction_service = setup_transaction
    new_transaction_data = {
        "amount": 100.0,
        "description": "Test transaction",
        "user_id": 1
    }
    result = transaction_service.create_transaction(new_transaction_data)
    assert result is not None
    assert isinstance(result, Transaction)
    assert result.amount == new_transaction_data["amount"]

import os
import sys
from faker import Faker
from app import create_app
from app.extensions import db
from app.models import User, Transaction, SavingsAccount, LoanAgreement

# Initialize the application
app = create_app(os.getenv('FLASK_CONFIG') or 'development')

fake = Faker()

def seed_users(num_users=10):
    for _ in range(num_users):
        user = User(
            email=fake.email(),
            password=fake.password()
        )
        db.session.add(user)
    db.session.commit()

def seed_transactions(num_transactions=20):
    user_ids = [user.id for user in User.query.all()]
    for _ in range(num_transactions):
        transaction = Transaction(
            user_id=fake.random_element(elements=user_ids),
            amount=fake.random_number(digits=5),
            transaction_type=fake.random_element(elements=('credit', 'debit'))
        )
        db.session.add(transaction)
    db.session.commit()

def seed_savings_accounts(num_accounts=10):
    user_ids = [user.id for user in User.query.all()]
    for _ in range(num_accounts):
        account = SavingsAccount(
            user_id=fake.random_element(elements=user_ids),
            balance=fake.random_number(digits=5)
        )
        db.session.add(account)
    db.session.commit()

def seed_loans(num_loans=5):
    user_ids = [user.id for user in User.query.all()]
    for _ in range(num_loans):
        loan = LoanAgreement(
            user_id=fake.random_element(elements=user_ids),
            amount=fake.random_number(digits=6),
            interest_rate=fake.random_number(digits=2),
            term=fake.random_number(digits=2)
        )
        db.session.add(loan)
    db.session.commit()

def main():
    with app.app_context():
        db.drop_all()
        db.create_all()
        seed_users()
        seed_transactions()
        seed_savings_accounts()
        seed_loans()
        print('Seeding completed!')

if __name__ == '__main__':
    main()

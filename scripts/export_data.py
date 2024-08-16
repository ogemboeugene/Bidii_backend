import os
import json
from app import create_app
from app.extensions import db
from app.models import User, Transaction, SavingsAccount, LoanAgreement

app = create_app(os.getenv('FLASK_CONFIG') or 'development')

def export_data():
    with app.app_context():
        data = {
            'users': [user.to_dict() for user in User.query.all()],
            'transactions': [transaction.to_dict() for transaction in Transaction.query.all()],
            'savings_accounts': [account.to_dict() for account in SavingsAccount.query.all()],
            'loans': [loan.to_dict() for loan in LoanAgreement.query.all()]
        }
        with open('data_export.json', 'w') as f:
            json.dump(data, f, indent=4)
        print('Data exported successfully.')

if __name__ == '__main__':
    export_data()

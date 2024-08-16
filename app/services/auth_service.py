import datetime
from app.models import User
from functools import wraps
from app.extensions import mail, db
from flask_mail import Message
from flask import current_app, request, jsonify
from flask_jwt_extended import get_jwt_identity, create_access_token
from itsdangerous import URLSafeTimedSerializer, BadSignature
from app.utils import hash_password, check_password
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash
# from .audit_utils import log_action

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'message': 'Unauthorized access'}), 401
        
        current_user = User.query.get(current_user_id)
        if not current_user or not current_user.is_admin:
            return jsonify({'message': 'Admins only!'}), 403
        
        return f(*args, **kwargs)

    return decorated_function

def create_admin(app):
    with app.app_context():
        if User.query.filter_by(username='admin').first() is None:
            admin_password = generate_password_hash('adminpass')  # Replace with a secure method to generate or set a password
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.password_hash = admin_password
            db.session.add(admin)
            db.session.commit()

def send_alert(message):
    msg = Message(subject='Alert from Your App', recipients=['admin@example.com'], body=message)
    mail.send(msg)

def flag_user_as_suspicious(user_id):
    user = User.query.get(user_id)
    if user:
        user.is_suspicious = True
        db.session.commit()


def detect_fraud_patterns(transactions):
    threshold_amount = 10000  # Example threshold for fraud detection
    fraud_patterns = [t for t in transactions if t.amount > threshold_amount]
    return fraud_patterns

def escalate_to_compliance(user_id):
    user = User.query.get(user_id)
    if user:
        admin_email = 'brianeugene851@gmail.com'
        message = f"User {user.username} (ID: {user.id}) needs further scrutiny."
        send_notification(admin_email, 'Compliance Escalation', message)

def check_due_payments():
    today = datetime.utcnow().date()
    due_repayments = LoanRepayment.query.filter_by(due_date=today, status='pending').all()
    for repayment in due_repayments:
        user = repayment.loan.user
        send_notification(user.id, 'Payment Due', f'Your payment of {repayment.amount} is due today.')

def check_overdue_loans():
    today = datetime.utcnow().date()
    overdue_repayments = LoanRepayment.query.filter(LoanRepayment.due_date < today, LoanRepayment.status == 'pending').all()
    for repayment in overdue_repayments:
        user = repayment.loan.user
        send_notification(user.id, 'Overdue Payment', f'Your payment of {repayment.amount} is overdue.')

def calculate_interest():
    savings_accounts = SavingsAccount.query.all()
    for account in savings_accounts:
        interest = account.balance * 0.05 / 12  # 5% annual interest, monthly
        account.balance += interest
        db.session.commit()

def integrate_payment_gateway(transaction_details):
    # Implement integration with payment gateway
    pass

def send_notification(user_id, subject, message):
    user = User.query.get(user_id)
    if user:
        msg = Message(subject=subject, recipients=[user.email], body=message)
        mail.send(msg)

class AuthService:    
    @staticmethod
    def create_user(data):
        password_hash = generate_password_hash(data['password'])
        user = User(username=data['username'], email=data['email'], password_hash=password_hash, role=data['role'], is_admin=data['is_admin'])
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(data):
        user = User.query.filter_by(username=data['username']).first()
        if user and check_password_hash(user.password_hash, data['password']):
            identity = {'id': user.id, 'role': user.role}
            token = create_access_token(identity=identity)
            return user, token
        return None, None
    
    @staticmethod
    def generate_password_reset_token(email):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        token = serializer.dumps(email, salt='password-reset-salt')
        print(f"Generated Token: {token}")  # Debugging output
        return token

    @staticmethod
    def verify_password_reset_token(token, expiration=3600):
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        try:
            email = serializer.loads(
                token,
                salt='password-reset-salt',
                max_age=expiration
            )
        except BadSignature:
            return None
        return email

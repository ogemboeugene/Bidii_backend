from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db

class History(db.Model):
    __tablename__ = 'history'
    
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(255), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    user = db.relationship('User', backref=db.backref('histories', lazy=True))

    def __repr__(self):
        return f'<History {self.id} - {self.group_name} on {self.date}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_name': self.group_name,
            'date': self.date.isoformat(),
            'created_by': self.created_by,
            'updated_at': self.updated_at.isoformat()
        }

class AdvanceSummary(db.Model):
    __tablename__ = 'advance_summary'

    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_advances = db.Column(db.Float, nullable=False)

    def __init__(self, group_name, date, total_advances):
        self.group_name = group_name
        self.date = date
        self.total_advances = total_advances

    def to_dict(self):
        return {
            'id': self.id,
            'group_name': self.group_name,
            'date': self.date.isoformat() if self.date else None,
            'total_advances': self.total_advances
        }
    
class AdvanceHistory(db.Model):
    __tablename__ = 'advance_history'

    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(100), nullable=False)
    initial_amount = db.Column(db.Float, nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('advance_histories', lazy=True))
    status = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    interest_rate = db.Column(db.Float, nullable=True)
    paid_amount = db.Column(db.Float, default=0.0)
    total_amount_due = db.Column(db.Float, nullable=True)
    group_id = db.Column(db.String(50), nullable=False)
    # month = db.Column(db.Integer, nullable=False)  # Ensure this is set
    # year = db.Column(db.Integer, nullable=False)   # Ensure this is set

    def to_dict(self):
        return {
            'id': self.id,
            'member_name': self.member_name,
            'initial_amount': self.initial_amount,
            'payment_amount': self.payment_amount,
            'is_paid': self.is_paid,
            'user_id': self.user_id,
            'status': self.status,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'interest_rate': self.interest_rate,
            'paid_amount': self.paid_amount,
            'total_amount_due': self.total_amount_due,
            'group_id': self.group_id,
            'month': self.month,
            'year': self.year,
        }
    

class FormRecords(db.Model):
    __tablename__ = 'form_records'
    
    id = db.Column(db.Integer, primary_key=True)
    history_id = db.Column(db.Integer, db.ForeignKey('history.id'), nullable=False)
    group_id = db.Column(db.Integer, nullable=False)
    member_details = db.Column(db.String, nullable=False)
    savings_shares_bf = db.Column(db.Float, nullable=False)
    loan_balance_bf = db.Column(db.Float, nullable=False)
    total_paid = db.Column(db.Float, nullable=False)
    principal = db.Column(db.Float, nullable=False)
    loan_interest = db.Column(db.Float, nullable=False)
    this_month_shares = db.Column(db.Float, nullable=False)
    fine_and_charges = db.Column(db.Float, nullable=True)
    savings_shares_cf = db.Column(db.Float, nullable=False)
    loan_cf = db.Column(db.Float, nullable=False)
    month = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with History
    history = db.relationship('History', backref=db.backref('form_records', lazy=True))
    
    def __repr__(self):
        return f'<FormRecords group_id={self.group_id} member_details={self.member_details} date={self.created_at}>'

# app/models.py

from app.extensions import db

class Advance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    member_name = db.Column(db.String(100), nullable=False)
    initial_amount = db.Column(db.Float, nullable=False)  # Initial amount of the advance
    payment_amount = db.Column(db.Float, nullable=False)  # Amount paid per installment
    is_paid = db.Column(db.Boolean, default=False)  # Whether the advance has been fully paid
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('advances', lazy=True))
    status = db.Column(db.String(20), default='pending', nullable=False)  # Status of the advance
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # When the advance was created
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())  # Last updated timestamp
    interest_rate = db.Column(db.Float, nullable=True)  # Interest rate for the advance
    paid_amount = db.Column(db.Float, default=0.0)  # Amount that has been paid towards the advance
    total_amount_due = db.Column(db.Float, nullable=True)  # Total amount due including interest
    group_id = db.Column(db.String(50), nullable=False)  


class MonthlyAdvanceCredit(db.Model):
    __tablename__ = 'monthly_advance_credits'

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.String(50), nullable=False)
    group_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_advance_amount = db.Column(db.Float, nullable=False)
    deductions = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<MonthlyAdvanceCredit {self.group_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_id': self.group_id,
            'group_name': self.group_name,
            'date': self.date.isoformat(),  # Convert date to ISO format string
            'total_advance_amount': self.total_advance_amount,
            'deductions': self.deductions
        }
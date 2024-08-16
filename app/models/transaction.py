import uuid
from app.extensions import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    is_flagged = db.Column(db.Boolean, default=False)
    transaction_ref = db.Column(db.String(20), unique=True, nullable=False, default='')

    # New relationship to Advance model
    advance_id = db.Column(db.Integer, db.ForeignKey('advance.id'))
    advance = db.relationship('Advance', backref=db.backref('transactions', lazy=True))

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.transaction_ref = self.generate_transaction_ref()

    def generate_transaction_ref(self):
        # Generate a unique transaction reference (e.g., 'TX1234ABCD')
        return f"TX{uuid.uuid4().hex[:8].upper()}"
    
    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'description': self.description,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'advance_id': self.advance_id,
            'is_flagged': self.is_flagged,
            'transaction_ref': self.transaction_ref
        }
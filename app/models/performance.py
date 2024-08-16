from app.extensions import db

class GroupMonthlyPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, nullable=False) 
    member_details = db.Column(db.String(100), nullable=False)
    savings_shares_bf = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    loan_balance_bf = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    total_paid = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    principal = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    loan_interest = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    this_month_shares = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    fine_and_charges = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    savings_shares_cf = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    loan_cf = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    month = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    

class MonthlyPerformance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(100), nullable=False)
    banking = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    service_fee = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    loan_form = db.Column(db.Float, nullable=True)
    passbook = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    office_debt_paid = db.Column(db.Float, nullable=True)  # Changed to nullable=True
    office_banking = db.Column(db.Float, nullable=True)
    month = db.Column(db.String(20), nullable=False)
    year = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<MonthlyPerformance {self.id} - {self.group_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'group_name': self.group_name,
            'banking': self.banking,
            'service_fee': self.service_fee,
            'loan_form': self.loan_form,
            'passbook': self.passbook,
            'office_debt_paid': self.office_debt_paid,
            'office_banking': self.office_banking,
            'month': self.month,
            'year': self.year
        }

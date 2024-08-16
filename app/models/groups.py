# groups.py
from app.extensions import db

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    officer_name = db.Column(db.String(100), nullable=False)
    project = db.Column(db.String(100), nullable=False)
    members = db.relationship('Member', backref='group', lazy=True)

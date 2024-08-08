from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from .. import db

class Interview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String, nullable=False, default = "")
    name = db.Column(db.String, nullable=False, default = "")
    rules = db.Column(db.String, nullable=False, default = "")                                      # E.g., maximum number of applicants = 200
    status = db.Column(db.String, nullable=True, default = "live")
    hr_id = db.Column(db.Integer, db.ForeignKey('hr.id'), nullable=False)
    interview_parameters = db.relationship('InterviewParameter', backref='interview',  cascade="all, delete-orphan")


    def __repr__(self):
        return f'<Interview {self.id}>'
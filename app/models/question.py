from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

from .. import db

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    audio_file_path = db.Column(db.String, nullable=True)  
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    answer = db.relationship('Answer', uselist=False, backref='question',  cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Question {self.id}>'
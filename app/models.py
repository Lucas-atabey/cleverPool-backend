from datetime import datetime
from .extensions import db, redis_client
from werkzeug.security import generate_password_hash, check_password_hash

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha256", salt_length=8)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Poll(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    questions = db.relationship('Question', backref='poll', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "questions": [q.to_dict() for q in self.questions]
        }

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(255), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey('poll.id'), nullable=False)
    options = db.relationship('Option', backref='question', cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "poll_id": self.poll_id,
            "options": [o.to_dict() for o in self.options]
        }

class Option(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('question.id'), nullable=False)
    votes = db.relationship('Vote', backref='option', cascade="all, delete-orphan")

    def to_dict(self):
        # récupérer le nombre de votes depuis Redis
        count = redis_client.get(f"option:{self.id}:votes")
        return {
            "id": self.id,
            "text": self.text,
            "question_id": self.question_id,
            "votes_count": int(count) if count else 0
        }

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "option_id": self.option_id
        }

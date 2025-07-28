from datetime import datetime
from .extensions import db

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
        return {
            "id": self.id,
            "text": self.text,
            "question_id": self.question_id,
            "votes_count": len(self.votes)
        }

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('option.id'), nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "option_id": self.option_id
        }

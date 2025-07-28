from flask import Blueprint, jsonify, request
from .models import Poll, Question, Option, Vote
from .extensions import db

bp = Blueprint('main', __name__)

@bp.route("/")
def index():
    return "CleverPoll backend is alive!"

@bp.route('/polls', methods=['GET'])
def get_polls():
    polls = Poll.query.all()
    return jsonify([poll.to_dict() for poll in polls])

@bp.route('/polls', methods=['POST'])
def create_poll():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')

    if not title:
        return jsonify({"message": "Le titre est requis"}), 400

    poll = Poll(title=title, description=description)
    db.session.add(poll)
    db.session.commit()

    return jsonify(poll.to_dict()), 201

@bp.route('/polls/<int:poll_id>/questions', methods=['POST'])
def create_question(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({"message": "Le texte de la question est requis"}), 400

    question = Question(text=text, poll_id=poll.id)
    db.session.add(question)
    db.session.commit()

    return jsonify(question.to_dict()), 201

@bp.route('/questions/<int:question_id>/options', methods=['POST'])
def add_option(question_id):
    question = Question.query.get_or_404(question_id)
    data = request.get_json()
    text = data.get('text')

    if not text:
        return jsonify({"message": "Le texte de l'option est requis"}), 400

    option = Option(text=text, question_id=question.id)
    db.session.add(option)
    db.session.commit()

    return jsonify(option.to_dict()), 201

@bp.route('/options/<int:option_id>/vote', methods=['POST'])
def vote_option(option_id):
    option = Option.query.get_or_404(option_id)
    vote = Vote(option_id=option.id)
    db.session.add(vote)
    db.session.commit()
    return jsonify({'message': 'Vote enregistré'}), 201

@bp.route('/questions/<int:question_id>/results', methods=['GET'])
def get_results(question_id):
    question = Question.query.get_or_404(question_id)
    results = []
    for option in question.options:
        votes_count = len(option.votes)
        results.append({
            'option_id': option.id,
            'text': option.text,
            'votes': votes_count
        })
    return jsonify({
        "question_id": question.id,
        "question_text": question.text,
        "results": results
    })

from flask import Blueprint, jsonify, request, jsonify
from .models import Poll, Question, Option, Vote, Admin
from werkzeug.security import check_password_hash
from .extensions import db, redis_client
from functools import wraps
from datetime import timedelta
import math
import jwt
import os

bp = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Unauthorized"}), 401

        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, os.environ['SECRET_KEY'], algorithms=['HS256'])
            admin_id = redis_client.get(f"admin_token:{token}")
            if not admin_id:
                return jsonify({"error": "Token expired or invalid"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated

@bp.route("/cpu")
def cpu():
    total = 0
    # Boucle lourde qui évite les optimisations
    for i in range(1, 10**7):
        total += math.sqrt(i) * math.sin(i)
    return str(total)

@bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')  # ⬅️ correction ici
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    admin = Admin.query.filter_by(username=username).first()
    if not admin or not admin.check_password(password):  # ⬅️ utilise ta méthode
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode({"id": admin.id}, os.environ['SECRET_KEY'], algorithm="HS256")
    redis_client.setex(f"admin_token:{token}", timedelta(minutes=15), admin.id)

    return jsonify({"token": token})

@bp.route('/admin/logout', methods=['POST'])
@admin_required
def admin_logout():
    auth_header = request.headers.get('Authorization')
    token = auth_header.split(' ')[1]
    redis_client.delete(f"admin_token:{token}")
    return jsonify({"message": "Logged out"})

@bp.route("/")
def index():
    return "CleverPoll backend is alive!"

@bp.route('/polls', methods=['GET'])
def get_polls():
    polls = Poll.query.all()
    return jsonify([poll.to_dict() for poll in polls])

@bp.route('/polls/<int:poll_id>', methods=['DELETE'])
@admin_required
def delete_poll(poll_id):
    poll = Poll.query.get(poll_id)
    if not poll:
        return jsonify({"message": "Sondage non trouvé"}), 404

    db.session.delete(poll)
    db.session.commit()
    return '', 204

@bp.route('/polls/<int:poll_id>', methods=['GET'])
def get_poll(poll_id):
    poll = Poll.query.get_or_404(poll_id)
    return jsonify(poll.to_dict())

@bp.route('/polls/full', methods=['POST'])
@admin_required
def create_full_poll():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    questions = data.get('questions', [])

    if not title:
        return jsonify({"message": "Le titre est requis"}), 400

    poll = Poll(title=title, description=description)
    db.session.add(poll)
    db.session.flush()  # pour récupérer poll.id

    for q in questions:
        question = Question(text=q.get('text'), poll_id=poll.id)
        db.session.add(question)
        db.session.flush()

        for opt in q.get('options', []):
            option = Option(text=opt, question_id=question.id)
            db.session.add(option)

    db.session.commit()

    return jsonify(poll.to_dict()), 201

@bp.route('/polls/<int:poll_id>/questions', methods=['GET'])
def get_poll_questions(poll_id):
    poll = Poll.query.get_or_404(poll_id)

    payload = {
        "id": poll.id,
        "title": poll.title,
        "description": poll.description,
        "questions": []
    }

    for q in poll.questions:
        q_dict = {
            "id": q.id,
            "text": q.text,
            "options": []
        }
        for o in q.options:
            # => Compter en SQL :
            votes_count = Vote.query.filter_by(option_id=o.id).count()

            o_dict = {
                "id": o.id,
                "text": o.text,
                "votes_count": votes_count
            }
            q_dict["options"].append(o_dict)

        payload["questions"].append(q_dict)

    return jsonify(payload)

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
    # Récupère l'option et sa question
    option = Option.query.get_or_404(option_id)
    question_id = option.question_id

    # On utilise l’adresse IP du client pour identifier temporairement la personne
    user_ip = request.remote_addr
    key = f"anti_spam:question:{question_id}:ip:{user_ip}"

    # Si la clé existe déjà => on bloque
    if redis_client.get(key):
        return jsonify({"message": "Tu as déjà voté récemment"}), 429

    # Sinon => on stocke la clé expirante (ex: 5 min)
    redis_client.setex(key, 5 * 60, 1)

    # Enregistre le vote dans Redis + MySQL
    redis_client.incr(f"option:{option_id}:votes")

    vote = Vote(option_id=option_id)
    db.session.add(vote)
    db.session.commit()

    return jsonify({'message': 'Vote enregistré'}), 201

@bp.route('/questions/<int:question_id>/results', methods=['GET'])
def get_results(question_id):
    question = Question.query.get_or_404(question_id)

    results = []
    for option in question.options:
        votes_count = Vote.query.filter_by(option_id=option.id).count()

        results.append({
            'option_id': option.id,
            'text': option.text,
            'votes': votes_count
        })

    return jsonify({
        "question_id": question.id,
        "question_text": question.text,
        "results": results,
    })

@bp.route('/polls/full/<int:poll_id>', methods=['PUT'])
@admin_required
def update_full_poll(poll_id):
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    questions_data = data.get('questions', [])

    poll = Poll.query.get_or_404(poll_id)

    # Mise à jour titre / description
    if title:
        poll.title = title
    if description is not None:
        poll.description = description

    # On garde une trace des questions existantes
    existing_questions = {q.id: q for q in poll.questions}

    for q_data in questions_data:
        q_id = q_data.get('id')
        q_text = q_data.get('text')
        q_options = q_data.get('options', [])

        if q_id and q_id in existing_questions:
            # Modification question existante
            question = existing_questions[q_id]
            if q_text:
                question.text = q_text

            # Gestion des options
            existing_options = {o.id: o for o in question.options}
            for opt_data in q_options:
                if isinstance(opt_data, dict):
                    opt_id = opt_data.get('id')
                    opt_text = opt_data.get('text')
                else:
                    # compatibilité avec format simple ["option1", "option2"]
                    opt_id = None
                    opt_text = opt_data

                if opt_id and opt_id in existing_options:
                    if opt_text:
                        existing_options[opt_id].text = opt_text
                else:
                    # Nouvelle option
                    db.session.add(Option(text=opt_text, question_id=question.id))

            # Suppression options non envoyées
            sent_option_ids = {
                o.get('id') for o in q_options if isinstance(o, dict) and o.get('id')
            }
            for opt in list(question.options):
                if opt.id not in sent_option_ids:
                    db.session.delete(opt)

        else:
            # Nouvelle question
            question = Question(text=q_text, poll_id=poll.id)
            db.session.add(question)
            db.session.flush()

            for opt_data in q_options:
                opt_text = opt_data.get('text') if isinstance(opt_data, dict) else opt_data
                db.session.add(Option(text=opt_text, question_id=question.id))

    # Suppression questions non envoyées
    sent_question_ids = {q.get('id') for q in questions_data if q.get('id')}
    for q in list(poll.questions):
        if q.id not in sent_question_ids:
            db.session.delete(q)

    db.session.commit()

    return jsonify(poll.to_dict()), 200

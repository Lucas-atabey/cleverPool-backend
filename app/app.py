from flask import Flask
from flask_cors import CORS
from .routes import bp
from .extensions import db, migrate, redis_client
import os

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRESQL_ADDON_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
    redis_client.__init__(host=redis_url)  # ou Redis.from_url(redis_url) à voir

    frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
    CORS(app, origins=[frontend_origin])

    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app

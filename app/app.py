from flask import Flask
from flask_cors import CORS
from .routes import bp
from sqlalchemy.exc import OperationalError, ProgrammingError
from .extensions import migrate
from app.models import Admin, db
import os



def create_admin_if_not_exists():
    username = os.getenv('ADMIN_USER')
    password = os.getenv('ADMIN_PASSWORD')

    if not username or not password:
        print("⚠️ Variables ADMIN_USER et ADMIN_PASSWORD non définies, admin non créé.")
        return

    try:
        admin = Admin.query.filter_by(username=username).first()
    except (OperationalError, ProgrammingError) as e:
        print("⚠️ Table 'admin' non trouvée, admin non créé pour l'instant. Faites la migration d'abord.")
        return

    if admin:
        print(f"Admin '{username}' existe déjà.")
        return

    admin = Admin(username=username)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    print(f"✅ Admin '{username}' créé automatiquement au démarrage.")

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("POSTGRESQL_ADDON_URI")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_size': 40,
        'max_overflow': 0,   # jamais de dépassement
        'pool_recycle': 1800
    }
    db.init_app(app)
    migrate.init_app(app, db)

    print(f"Frontend origin1: {os.getenv("FRONTEND_ORIGIN", "*")}")
    frontend_origin = os.getenv("FRONTEND_ORIGIN", "*")
    print(f"Frontend origi2: {frontend_origin}")
    CORS(app, origins=[frontend_origin])

    with app.app_context():
        create_admin_if_not_exists()
    app.register_blueprint(bp)
    return app

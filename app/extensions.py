# app/extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from redis import Redis
import os

db = SQLAlchemy()
migrate = Migrate()

# Récupération de l'URL depuis les variables d'env (Clever Cloud ou local fallback)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialise le client Redis une seule fois
redis_client = Redis.from_url(redis_url)

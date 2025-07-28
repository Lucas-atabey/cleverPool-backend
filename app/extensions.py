from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from redis import Redis

db = SQLAlchemy()
migrate = Migrate()
redis_client = Redis()

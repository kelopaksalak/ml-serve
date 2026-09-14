from flask import Flask
from flask_jwt_extended import JWTManager
from app.database import db
from config import config

jwt = JWTManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    jwt.init_app(app)

    with app.app_context():
        from app.models import User, MLModel
        db.create_all()

    from app.routes import register_routes
    register_routes(app)

    return app
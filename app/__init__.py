import os

from flask import Flask
from app.database import db
from config import config


def create_app(config_name=None, config_overrides=None):
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)

    with app.app_context():
        from app.models import MLModel
        db.create_all()

    from app.routes import register_routes
    register_routes(app)

    from app.openapi import register_swagger
    register_swagger(app)

    return app

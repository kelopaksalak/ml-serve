from app.controllers.model_controller import ml_model_bp

def register_routes(app):
    app.register_blueprint(ml_model_bp)

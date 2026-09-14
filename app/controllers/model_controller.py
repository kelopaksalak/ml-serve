from flask import Blueprint, request, jsonify
from app.dto.ml_model_dto import MlModelRequestSchema, MlModelResponseSchema, PredictRequestSchema
from app.services.ml_model_service import MlModelService
from app.middleware.auth_middleware import require_auth

ml_model_bp = Blueprint('ml_model_bp', __name__)
ml_model_service = MlModelService()

@ml_model_bp.route('/api/ml_model', methods=['GET'])
@require_auth
def get_all():
    models = ml_model_service.get_all()
    return jsonify({'success': True, 'data': MlModelResponseSchema().dump(models, many=True)}), 200

@ml_model_bp.route('/api/ml_model/<int:id>', methods=['GET'])
@require_auth
def get_by_id():
    model = ml_model_service.get_by_id(id)
    if not model:
        return jsonify({'success': False, 'message': 'Model not found'}), 404
    return jsonify({'success': True, 'data': MlModelResponseSchema().dump(model)}), 200

@ml_model_bp.route('/api/ml_model', methods=['POST'])
@require_auth
def create():
    from flask_jwt_extended import get_jwt_identity
    schema = MlModelRequestSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({'success': False, 'message': errors}), 404

    data = schema.load(request.json)
    user_id = int(get_jwt_identity)
    model, error = ml_model_service.create(data, user_id)
    if error:
        return jsonify({'success': False, 'message': errors}), 400

    return jsonify({'success': True, 'message': MlModelResponseSchema().dump(model)}), 201

@ml_model_bp.route('/api/ml_model/<int:id>/predict', methods=['POST'])
@require_auth
def predict(id):
    schema = PredictRequestSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({'success': False, 'message': errors}), 400

    data = schema.load(request.json)
    result, error = ml_model_service.predict(id, data['features'])
    if error:
        return jsonify({'success': False, 'message': error}), 400

    return jsonify({'success': True, 'data': result})
from flask import Blueprint, request, jsonify
from app.dto.auth_dto import LoginSchema, RegisterSchema, UserResponseSchema
from app.services.auth_service import AuthService
from app.middleware.auth_middleware import require_auth

auth_bp = Blueprint('auth_bp', __name__)
auth_service = AuthService()

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    schema = RegisterSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({'success': False, 'message': errors}), 400

    data = schema.load(request.json)
    user, error = auth_service.register(data)
    if error:
        return jsonify({'success': False, 'message': error}), 400
    return jsonify({'success': True, 'data': UserResponseSchema().dump(user)}), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    schema = LoginSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({'success': False, 'message': errors}), 400

    data = schema.load(request.json)
    result, error = auth_service.login(data)
    if error:
        return jsonify({'success': False, 'message': error}), 401
    return jsonify({'success': True, 'data': result})

@auth_bp.route('/api/auth/me', methods=['GET'])
@require_auth
def me():
    from flask_jwt_extended import get_jwt_identity
    user_id = int(get_jwt_identity())
    user = auth_service.get_user(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    return jsonify({'success': True, 'data': UserResponseSchema().dump(user)})

    
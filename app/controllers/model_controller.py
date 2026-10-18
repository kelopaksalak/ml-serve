from flask import Blueprint, jsonify
from marshmallow import ValidationError

from app.dto.ml_model_dto import (
    MlModelRequestSchema,
    MlModelResponseSchema,
    PredictRequestSchema,
)
from app.services.ml_model_service import MlModelService
from app.dto.request_validation import load_request

ml_model_bp = Blueprint("ml_model_bp", __name__)
ml_model_service = MlModelService()


@ml_model_bp.route("/api/ml_model", methods=["GET"])
def get_all():
    models = ml_model_service.get_all()

    return jsonify({
        "success": True,
        "data": MlModelResponseSchema().dump(models, many=True),
    }), 200


@ml_model_bp.route("/api/ml_model/<int:id>", methods=["GET"])
def get_by_id(id):
    model = ml_model_service.get_by_id(id)

    if model is None:
        return jsonify({
            "success": False,
            "message": "Model not found",
        }), 404

    return jsonify({
        "success": True,
        "data": MlModelResponseSchema().dump(model),
    }), 200


@ml_model_bp.route("/api/ml_model", methods=["POST"])
def create():
    try:
        data = load_request(MlModelRequestSchema())
    except ValidationError as error:
        return jsonify({
            "success": False,
            "message": error.messages,
        }), 400

    model, error = ml_model_service.create(data)

    if error:
        return jsonify({
            "success": False,
            "message": error,
        }), 400

    return jsonify({
        "success": True,
        "data": MlModelResponseSchema().dump(model),
    }), 201


@ml_model_bp.route(
    "/api/ml_model/<int:id>/predict",
    methods=["POST"],
)
def predict(id):
    if ml_model_service.get_by_id(id) is None:
        return jsonify({
            "success": False,
            "message": "Model not found",
        }), 404

    try:
        data = load_request(PredictRequestSchema())
    except ValidationError as error:
        return jsonify({
            "success": False,
            "message": error.messages,
        }), 400

    result, error = ml_model_service.predict(id, data["features"])

    if error:
        return jsonify({
            "success": False,
            "message": error,
        }), 400

    return jsonify({
        "success": True,
        "data": result,
    }), 200

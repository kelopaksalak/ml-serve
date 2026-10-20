import json

from flask import current_app
from marshmallow import ValidationError

from app.dto.ml_model_dto import MlModelResponseSchema
from app.dto.ws_dto import WsRequestSchema
from app.services.ml_model_service import MlModelService

ml_model_service = MlModelService()
_model_schema = MlModelResponseSchema()
_request_schema = WsRequestSchema()


def _error(message):
    return {"success": False, "message": message}


def handle_message(raw_message):
    """Turn one raw text message into the JSON envelope sent back to the client."""
    try:
        payload = json.loads(raw_message)
    except (TypeError, ValueError):
        return _error("Message must be valid JSON.")

    if not isinstance(payload, dict):
        return _error("Message must be a JSON object.")

    try:
        data = _request_schema.load(payload)
    except ValidationError as error:
        return _error(error.messages)

    action = data["action"]

    if action == "list":
        models = ml_model_service.get_all()
        return {"success": True, "data": _model_schema.dump(models, many=True)}

    if "id" not in data:
        return _error("id is required.")

    if action == "get":
        model = ml_model_service.get_by_id(data["id"])
        if model is None:
            return _error("Model not found")
        return {"success": True, "data": _model_schema.dump(model)}

    # action == "predict"
    if "features" not in data:
        return _error("features is required.")

    if ml_model_service.get_by_id(data["id"]) is None:
        return _error("Model not found")

    result, error = ml_model_service.predict(data["id"], data["features"])
    if error:
        return _error(error)
    return {"success": True, "data": result}


def ml_model_ws(ws):
    """Serve the read/predict protocol while the WebSocket connection is open."""
    while True:
        message = ws.receive()
        if message is None:
            break

        try:
            response = handle_message(message)
        except Exception:
            current_app.logger.exception("WebSocket message handling failed")
            response = _error("Internal server error")

        try:
            ws.send(json.dumps(response))
        except Exception:
            break


def register_ws_routes(sock):
    sock.route("/ws/ml_model")(ml_model_ws)

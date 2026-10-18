from flask import request
from marshmallow import ValidationError


def load_request(schema):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationError({
            '_schema': ['Request body must be a JSON object.']
        })
    return schema.load(payload)

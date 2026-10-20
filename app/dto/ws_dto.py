from marshmallow import Schema, fields, validate


class WsRequestSchema(Schema):
    """One request message received over the model WebSocket channel."""

    action = fields.Str(
        required=True,
        validate=validate.OneOf(["list", "get", "predict"]),
    )
    id = fields.Int(validate=validate.Range(min=1))
    features = fields.List(
        fields.Float(allow_nan=False),
        validate=validate.Length(min=1),
    )

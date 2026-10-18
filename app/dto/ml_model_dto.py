from marshmallow import Schema, fields, validate


class MlModelRequestSchema(Schema):
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=100),
            validate.Regexp(
                r"^[A-Za-z0-9_-]+$",
                error=(
                    "Use letters, numbers, underscores, "
                    "or hyphens only."
                ),
            ),
        ],
    )
    description = fields.Str()
    model_type = fields.Str(
        validate=validate.OneOf(["classifier", "regressor"])
    )


class MlModelResponseSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    description = fields.Str()
    model_type = fields.Str()
    features = fields.Str()
    model_path = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class PredictRequestSchema(Schema):
    features = fields.List(
        fields.Float(allow_nan=False),
        required=True,
        validate=validate.Length(min=1),
    )
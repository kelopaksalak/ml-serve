from marshmallow import Schema, fields

class MlModelRequestSchema(Schema):
    name = fields.Str(required=True)
    description = fields.Str()
    model_type = fields.Str()

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
    features = fields.List(fields.Float(), required=True)
from marshmallow import Schema, fields

class ResponseSchema(Schema):
    success = fields.Bool(required=True)
    message = fields.Str()
    data = fields.Raw()
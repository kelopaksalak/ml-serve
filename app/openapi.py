"""OpenAPI contract and locally served Swagger UI for the existing API."""

from flask import jsonify
from flask_swagger_ui import get_swaggerui_blueprint


def ref(name):
    return {'$ref': f'#/components/schemas/{name}'}


def response(description, schema):
    return {'description': description, 'content': {'application/json': {'schema': schema}}}


def success(data):
    return {
        'type': 'object', 'required': ['success', 'data'],
        'properties': {'success': {'type': 'boolean', 'enum': [True]}, 'data': data},
    }


def operation(summary, operation_id, tag, data, *, status='200', request=None,
              example=None, not_found=False, invalid=False):
    result = {
        'summary': summary, 'operationId': operation_id, 'tags': [tag],
        'responses': {status: response('Success', success(data))},
    }
    if invalid:
        result['responses']['400'] = response('Invalid request or model processing error', ref('Error'))
    if not_found:
        result['responses']['404'] = response('Resource not found', ref('Error'))
    if request:
        result['requestBody'] = {
            'required': True,
            'content': {'application/json': {'schema': ref(request), 'example': example}},
        }
    return result


def build_spec():
    schemas = {
        'ModelRequest': {
            'type': 'object', 'required': ['name'], 'additionalProperties': False,
            'properties': {
                'name': {'type': 'string', 'minLength': 1, 'maxLength': 100, 'pattern': '^[A-Za-z0-9_-]+$'},
                'description': {'type': 'string'},
                'model_type': {'type': 'string', 'enum': ['classifier', 'regressor']},
            },
        },
        'Model': {'type': 'object', 'properties': {
            'id': {'type': 'integer'}, 'name': {'type': 'string'},
            'description': {'type': 'string', 'nullable': True},
            'model_type': {'type': 'string', 'nullable': True},
            'features': {'type': 'string', 'nullable': True, 'example': '["feature1", "feature2"]',
                         'description': 'JSON-encoded feature names in training order, or "[]".'},
            'model_path': {'type': 'string', 'nullable': True},
            'created_at': {'type': 'string', 'format': 'date-time'},
            'updated_at': {'type': 'string', 'format': 'date-time'},
        }},
        'PredictRequest': {
            'type': 'object', 'required': ['features'], 'additionalProperties': False,
            'properties': {'features': {
                'type': 'array', 'minItems': 1, 'items': {'type': 'number'},
                'description': 'Finite numeric values in the model training feature order.',
            }},
        },
        'Prediction': {'type': 'object', 'properties': {
            'prediction': {'description': 'Raw model output; type depends on the estimator.', 'example': 5.0},
        }},
        'Error': {'type': 'object', 'properties': {
            'success': {'type': 'boolean', 'enum': [False]},
            'message': {'oneOf': [{'type': 'string'}, {'type': 'object', 'additionalProperties': True}]},
        }},
    }
    identifier = {'name': 'id', 'in': 'path', 'required': True, 'schema': {'type': 'integer', 'minimum': 0}}
    create = operation('Register an existing local model file', 'registerModel', 'Models', ref('Model'),
                       status='201', request='ModelRequest', invalid=True,
                       example={'name': 'fake_model', 'model_type': 'regressor'})
    create['description'] = 'Place a trusted .pkl file in ml_models/ first. This endpoint registers metadata; it does not upload files.'
    predict = operation('Run a prediction', 'predict', 'Models', ref('Prediction'),
                        request='PredictRequest', example={'features': [2.0, 3.0]}, invalid=True, not_found=True)
    predict['description'] = 'Returns data.prediction, not a difficulty decision or confidence score. The demo model adds two inputs.'
    return {
        'openapi': '3.0.3',
        'info': {'title': 'Flask ML Backend', 'version': '1.0.0',
                 'description': 'Public model API. Use Try it out to call endpoints directly; no credentials are required.'},
        'tags': [{'name': 'Models'}],
        'components': {'schemas': schemas},
        'paths': {
            '/api/ml_model': {
                'get': operation('List registered models', 'listModels', 'Models', {'type': 'array', 'items': ref('Model')}),
                'post': create,
            },
            '/api/ml_model/{id}': {'parameters': [identifier],
                'get': operation('Get model metadata', 'getModel', 'Models', ref('Model'), not_found=True)},
            '/api/ml_model/{id}/predict': {'parameters': [identifier], 'post': predict},
        },
    }


def register_swagger(app):
    @app.get('/openapi.json')
    def openapi_spec():
        return jsonify(build_spec())

    app.register_blueprint(get_swaggerui_blueprint(
        '/swagger', '/openapi.json',
        config={'app_name': 'Flask ML Backend', 'validatorUrl': None,
                'displayRequestDuration': True},
    ))

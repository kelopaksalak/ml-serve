import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
from sklearn.linear_model import LinearRegression

from app import create_app, db
from app.services.ml_model_service import MlModelService


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.models_dir = Path(self.temp.name)
        self.directory_patch = patch.object(MlModelService, 'MODELS_DIR', self.models_dir)
        self.directory_patch.start()
        self.addCleanup(self.directory_patch.stop)
        self.app = create_app('default', {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        })
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()
        self.addCleanup(self.context.pop)
        self.addCleanup(db.session.remove)
        model = LinearRegression().fit([[1, 2], [3, 4], [5, 6]], [3, 7, 11])
        joblib.dump(model, self.models_dir / 'demo.pkl')

    def register_model(self):
        response = self.client.post('/api/ml_model', json={'name': 'demo'})
        self.assertEqual(response.status_code, 201, response.json)
        return response.json['data']['id']

    def test_user_endpoints_and_tables_are_removed(self):
        for path, method in (('/api/auth/login', 'POST'),
                             ('/api/auth/register', 'POST'),
                             ('/api/auth/me', 'GET')):
            self.assertEqual(self.client.open(path, method=method).status_code, 404)
        self.assertNotIn('users', db.metadata.tables)
        self.assertNotIn('created_by', db.metadata.tables['ml_models'].columns)

    def test_model_registration_lookup_and_prediction(self):
        model_id = self.register_model()
        response = self.client.get(f'/api/ml_model/{model_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['data']['model_type'], 'regressor')
        self.assertEqual(json.loads(response.json['data']['features']), [])
        self.assertEqual(len(self.client.get('/api/ml_model').json['data']), 1)
        response = self.client.post(f'/api/ml_model/{model_id}/predict', json={'features': [2, 3]})
        self.assertEqual(response.status_code, 200, response.json)
        self.assertAlmostEqual(response.json['data']['prediction'], 5)

    def test_named_feature_metadata(self):
        model = joblib.load(self.models_dir / 'demo.pkl')
        model.feature_names_in_ = ['first', 'second']
        joblib.dump(model, self.models_dir / 'demo.pkl')
        model_id = self.register_model()
        response = self.client.get(f'/api/ml_model/{model_id}')
        self.assertEqual(json.loads(response.json['data']['features']), ['first', 'second'])

    def test_validation_and_missing_models(self):
        model_id = self.register_model()
        for features in ([], [1], ['invalid', 2], [None, 2]):
            response = self.client.post(f'/api/ml_model/{model_id}/predict', json={'features': features})
            self.assertEqual(response.status_code, 400, response.json)
        for path in ('/api/ml_model/999', '/api/ml_model/999/predict'):
            response = self.client.open(path, method='POST' if path.endswith('predict') else 'GET', json={'features': [2, 3]})
            self.assertEqual(response.status_code, 404)
        for name in ('demo', 'missing', '../escape'):
            response = self.client.post('/api/ml_model', json={'name': name})
            self.assertEqual(response.status_code, 400)

    def test_invalid_request_bodies(self):
        for path in ('/api/ml_model',):
            for body in ('null', '[]', '{broken'):
                response = self.client.post(path, data=body, content_type='application/json')
                self.assertEqual(response.status_code, 400)

    def test_model_load_failure_returns_bad_request(self):
        model_id = self.register_model()
        (self.models_dir / 'demo.pkl').write_bytes(b'invalid model')
        with self.assertLogs(self.app.logger, level='ERROR'):
            response = self.client.post(f'/api/ml_model/{model_id}/predict', json={'features': [2, 3]})
        self.assertEqual(response.status_code, 400)

    def test_environment_selects_production(self):
        with patch.dict('os.environ', {'FLASK_ENV': 'production'}):
            app = create_app(config_overrides={'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
        self.assertFalse(app.debug)


if __name__ == '__main__':
    unittest.main()

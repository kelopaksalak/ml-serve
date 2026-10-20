import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

import joblib
from sklearn.linear_model import LinearRegression
from sqlalchemy.pool import NullPool
from simple_websocket import Client
from werkzeug.serving import make_server

from app import create_app, db
from app.services.ml_model_service import MlModelService


class WebSocketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.models_dir = Path(self.temp.name)
        self.directory_patch = patch.object(MlModelService, 'MODELS_DIR', self.models_dir)
        self.directory_patch.start()
        self.addCleanup(self.directory_patch.stop)

        database_path = self.models_dir / 'test.db'
        self.app = create_app('default', {
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{database_path.as_posix()}',
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'connect_args': {'check_same_thread': False},
                'poolclass': NullPool,
            },
        })
        self.addCleanup(self._dispose)

        model = LinearRegression().fit([[1, 2], [3, 4], [5, 6]], [3, 7, 11])
        joblib.dump(model, self.models_dir / 'demo.pkl')
        with self.app.app_context():
            _, error = MlModelService().create({'name': 'demo'})
            self.assertIsNone(error)

        self.server = make_server('127.0.0.1', 0, self.app, threaded=True)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def _dispose(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def connect(self):
        ws = Client.connect(f'ws://127.0.0.1:{self.server.server_port}/ws/ml_model')
        self.addCleanup(ws.close)
        return ws

    def request(self, ws, message):
        ws.send(message if isinstance(message, str) else json.dumps(message))
        return json.loads(ws.receive(timeout=5))

    def test_list_get_and_predict_share_one_connection(self):
        ws = self.connect()
        listed = self.request(ws, {'action': 'list'})
        self.assertTrue(listed['success'])
        self.assertEqual([model['name'] for model in listed['data']], ['demo'])

        model_id = listed['data'][0]['id']
        read = self.request(ws, {'action': 'get', 'id': model_id})
        self.assertTrue(read['success'])
        self.assertEqual(read['data']['name'], 'demo')
        self.assertEqual(read['data']['model_type'], 'regressor')

        predicted = self.request(ws, {'action': 'predict', 'id': model_id, 'features': [2, 3]})
        self.assertTrue(predicted['success'])
        self.assertAlmostEqual(predicted['data']['prediction'], 5)

    def test_invalid_messages_return_errors_without_closing(self):
        ws = self.connect()
        for message in ('not json', json.dumps([1, 2]), json.dumps({'action': 'nope'}),
                        json.dumps({'action': 'get'}), json.dumps({'action': 'predict', 'id': 1})):
            self.assertFalse(self.request(ws, message)['success'])

        self.assertEqual(
            self.request(ws, {'action': 'get', 'id': 999}),
            {'success': False, 'message': 'Model not found'},
        )
        self.assertEqual(
            self.request(ws, {'action': 'predict', 'id': 999, 'features': [2, 3]}),
            {'success': False, 'message': 'Model not found'},
        )
        self.assertTrue(self.request(ws, {'action': 'list'})['success'])

    def test_prediction_feature_validation(self):
        ws = self.connect()
        model_id = self.request(ws, {'action': 'list'})['data'][0]['id']
        for features in ([], [1], ['invalid', 2]):
            response = self.request(ws, {'action': 'predict', 'id': model_id, 'features': features})
            self.assertFalse(response['success'])


if __name__ == '__main__':
    unittest.main()

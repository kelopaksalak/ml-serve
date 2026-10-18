import re
import unittest

from app import create_app, db


class DocumentationTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app('default', {
            'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        })
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def test_ui_and_local_assets(self):
        response = self.client.get('/swagger', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('/openapi.json', html)
        self.assertIn('SwaggerUIBundle', html)
        assets = re.findall(r'(?:src|href)="([^"]+\.(?:css|js))"', html)
        self.assertGreaterEqual(len(assets), 3)
        for asset in assets:
            self.assertTrue(asset.startswith('/swagger/'))
            with self.client.get(asset) as asset_response:
                self.assertEqual(asset_response.status_code, 200, asset)

    def test_spec_matches_api_routes_and_security(self):
        response = self.client.get('/openapi.json')
        self.assertEqual(response.status_code, 200)
        spec = response.json
        self.assertEqual(spec['openapi'], '3.0.3')
        self.assertNotIn('security', spec)
        self.assertNotIn('securitySchemes', spec['components'])
        actual = set()
        for rule in self.app.url_map.iter_rules():
            if rule.rule.startswith('/api/'):
                path = re.sub(r'<(?:int:)?(\w+)>', r'{\1}', rule.rule)
                actual.update((path, method.lower()) for method in rule.methods - {'OPTIONS', 'HEAD'})
        documented = {(path, method) for path, item in spec['paths'].items()
                      for method in item if method in {'get', 'post', 'put', 'delete', 'patch'}}
        self.assertEqual(actual, documented)
        self.assertEqual(len(documented), 4)
        for path, method in documented:
            operation = spec['paths'][path][method]
            self.assertNotIn('security', operation)
            self.assertNotIn('401', operation['responses'])
            if '{id}' in path:
                self.assertEqual(spec['paths'][path]['parameters'][0]['name'], 'id')

        def check_refs(value):
            if isinstance(value, dict):
                if '$ref' in value:
                    target = spec
                    for part in value['$ref'].removeprefix('#/').split('/'):
                        target = target[part]
                for child in value.values():
                    check_refs(child)
            elif isinstance(value, list):
                for child in value:
                    check_refs(child)

        check_refs(spec)

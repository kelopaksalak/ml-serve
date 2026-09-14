# Flask ML Backend - Improvement Roadmap

## Current State

- scikit-learn only
- JWT authentication
- SQLite (dev) / PostgreSQL (prod)
- Single model version
- No monitoring
- No rate limiting

---

## Phase 1: Multi-Framework Support

**Goal:** Support PyTorch, TensorFlow, ONNX, and XGBoost models.

### Changes

| File | Change |
|---|---|
| `app/services/ml_model_service.py` | Add model loader that detects format |
| `app/models/ml_model.py` | Add `framework` column |
| `cli.py` | Update to detect framework from file extension |
| `requirements.txt` | Add optional dependencies |

### Supported Formats

| Extension | Framework | Package |
|---|---|---|
| `.pkl` | scikit-learn, XGBoost | `joblib` |
| `.pt` / `.pth` | PyTorch | `torch` |
| `.h5` / `.keras` | TensorFlow / Keras | `tensorflow` |
| `.onnx` | ONNX | `onnxruntime` |
| `.joblib` | scikit-learn | `joblib` |

### New Model Loader

```python
import os

def load_model(path):
    ext = os.path.splitext(path)[1].lower()

    if ext in ['.pkl', '.joblib']:
        import joblib
        return joblib.load(path)

    elif ext in ['.pt', '.pth']:
        import torch
        return torch.load(path, map_location='cpu')

    elif ext in ['.h5', '.keras']:
        import tensorflow as tf
        return tf.keras.models.load_model(path)

    elif ext == '.onnx':
        import onnxruntime as ort
        return ort.InferenceSession(path)

    else:
        raise ValueError(f"Unsupported format: {ext}")
```

### New Prediction Logic

```python
def predict(self, id, features):
    model_obj = MLModel.query.get(id)
    if not model_obj:
        return None, 'Model not found'

    ml = load_model(model_obj.model_path)
    framework = model_obj.framework

    if framework == 'pytorch':
        import torch
        input_tensor = torch.tensor([features], dtype=torch.float32)
        with torch.no_grad():
            result = ml(input_tensor).numpy()[0]
    elif framework == 'tensorflow':
        import numpy as np
        result = ml.predict(np.array([features]))[0]
    elif framework == 'onnx':
        import numpy as np
        input_name = ml.get_inputs()[0].name
        result = ml.run(None, {input_name: np.array([features], dtype=np.float32)})[0][0]
    else:
        result = ml.predict([features])[0]

    if hasattr(result, 'tolist'):
        result = result.tolist()

    return {'prediction': result}, None
```

### Database Change

```python
# app/models/ml_model.py
class MLModel(db.Model):
    # ... existing columns ...
    framework = db.Column(db.String(50), default='scikit-learn')
```

### New Requirements

```
# Add to requirements.txt (optional)
# torch
# tensorflow
# onnxruntime
# xgboost
```

---

## Phase 2: Model Versioning

**Goal:** Update models without breaking existing predictions.

### Database Change

```python
class MLModel(db.Model):
    # ... existing columns ...
    version = db.Column(db.Integer, default=1)
    is_active = db.Column(db.Boolean, default=True)
```

### Version Flow

```
v1: sentiment_analyzer.pkl (active)
    |
    +-- User uploads new version
    |
v2: sentiment_analyzer.pkl (active)
v1: sentiment_analyzer.pkl (archived)
```

### API Behavior

```
GET /api/ml_model/sentiment_analyzer/predict
  -> Uses latest active version (v2)

GET /api/ml_model/sentiment_analyzer/predict?v=1
  -> Uses specific version (v1)
```

---

## Phase 3: Rate Limiting

**Goal:** Prevent abuse and manage API usage.

### Installation

```bash
pip install flask-limiter
```

### Implementation

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Per-endpoint limits
@ml_model_bp.route('/api/ml_model/<int:id>/predict', methods=['POST'])
@require_auth
@limiter.limit("10 per minute")
def predict(id):
    # ...
```

### Tiered Limits

| Tier | Limit | Use Case |
|---|---|---|
| Free | 100/day | Testing |
| Basic | 1,000/day | Small apps |
| Pro | 10,000/day | Production |
| Enterprise | Custom | High volume |

---

## Phase 4: Prediction Logging & Monitoring

**Goal:** Track usage, errors, and performance.

### New Table

```python
class PredictionLog(db.Model):
    __tablename__ = 'prediction_logs'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('ml_models.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    input_features = db.Column(db.Text)  # JSON
    prediction = db.Column(db.Text)      # JSON
    latency_ms = db.Column(db.Float)
    status = db.Column(db.String(20))    # success/error
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Logging Decorator

```python
import time
import json
from functools import wraps

def log_prediction(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = fn(*args, **kwargs)
            latency = (time.time() - start) * 1000

            log = PredictionLog(
                model_id=kwargs.get('id'),
                user_id=get_jwt_identity(),
                input_features=json.dumps(request.json.get('features')),
                prediction=json.dumps(result[0].get('data')),
                latency_ms=latency,
                status='success'
            )
            db.session.add(log)
            db.session.commit()

            return result
        except Exception as e:
            log = PredictionLog(
                model_id=kwargs.get('id'),
                user_id=get_jwt_identity(),
                status='error',
                error_message=str(e)
            )
            db.session.add(log)
            db.session.commit()
            raise
    return wrapper
```

### Stats Endpoint

```
GET /api/ml_model/<id>/stats
```

Response:

```json
{
  "total_predictions": 1523,
  "success_rate": 98.5,
  "avg_latency_ms": 45.2,
  "last_24h": 342
}
```

---

## Phase 5: API Key Authentication

**Goal:** Allow external developers to use the API without JWT.

### New Table

```python
class APIKey(db.Model):
    __tablename__ = 'api_keys'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100))
    rate_limit = db.Column(db.Integer, default=1000)  # per day
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Auth Middleware Update

```python
def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # Check API key first
        api_key = request.headers.get('X-API-Key')
        if api_key:
            key = APIKey.query.filter_by(key=api_key, is_active=True).first()
            if key:
                return fn(*args, **kwargs)

        # Fall back to JWT
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    return wrapper
```

### Usage

```bash
# JWT (existing)
curl -H "Authorization: Bearer <token>" /api/ml_model/1/predict

# API Key (new)
curl -H "X-API-Key: your-api-key-here" /api/ml_model/1/predict
```

---

## Phase 6: Batch Predictions

**Goal:** Process multiple inputs in one request.

### New Endpoint

```
POST /api/ml_model/<id>/predict/batch
```

Request:

```json
{
  "inputs": [
    {"features": [1.0, 2.0]},
    {"features": [3.0, 4.0]},
    {"features": [5.0, 6.0]}
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "predictions": [3, 7, 11],
    "count": 3,
    "latency_ms": 12.5
  }
}
```

### Implementation

```python
@ml_model_bp.route('/api/ml_model/<int:id>/predict/batch', methods=['POST'])
@require_auth
def predict_batch(id):
    schema = BatchPredictRequestSchema()
    errors = schema.validate(request.json)
    if errors:
        return jsonify({'success': False, 'message': errors}), 400

    data = schema.load(request.json)
    ml = load_model_service(id)

    predictions = []
    for item in data['inputs']:
        result = ml.predict([item['features']])[0]
        if hasattr(result, 'tolist'):
            result = result.tolist()
        predictions.append(result)

    return jsonify({
        'success': True,
        'data': {
            'predictions': predictions,
            'count': len(predictions)
        }
    })
```

---

## Phase 7: Model Health Checks

**Goal:** Monitor if models are working correctly.

### Health Check Endpoint

```
GET /api/ml_model/<id>/health
```

Response:

```json
{
  "status": "healthy",
  "model_loaded": true,
  "last_prediction": "2026-09-15T10:30:00",
  "avg_latency_ms": 45.2,
  "error_rate": 0.5
}
```

### Auto-Health Check

```python
@app.route('/api/health', methods=['GET'])
def health_check():
    models = MLModel.query.all()
    status = {
        'api': 'healthy',
        'database': 'connected',
        'models': {}
    }

    for model in models:
        try:
            ml = load_model(model.model_path)
            status['models'][model.name] = 'loaded'
        except Exception as e:
            status['models'][model.name] = f'error: {str(e)}'

    return jsonify(status)
```

---

## Phase 8: Swagger/OpenAPI Documentation

**Goal:** Auto-generated API docs.

### Installation

```bash
pip install flask-smorest
```

### Implementation

```python
from flask_smorest import Api

api = Api(app)
api.spec.title = "Flask ML Backend API"
api.spec.version = "1.0"
api.spec.description = "API for serving ML models"
```

### Access Docs

```
http://localhost:5000/docs
```

---

## Implementation Order

| Phase | Effort | Impact | Dependencies |
|---|---|---|---|
| Phase 1: Multi-Framework | Medium | High | None |
| Phase 2: Versioning | Low | High | None |
| Phase 3: Rate Limiting | Low | Medium | None |
| Phase 4: Monitoring | Medium | High | Phase 2 |
| Phase 5: API Keys | Medium | Medium | Phase 3 |
| Phase 6: Batch | Low | Medium | Phase 1 |
| Phase 7: Health Checks | Low | Low | Phase 4 |
| Phase 8: Swagger | Low | High | None |

---

## Quick Start: Adding Phase 1

1. Add `framework` column to `ml_model.py`
2. Create `app/utils/model_loader.py` with `load_model()` function
3. Update `ml_model_service.py` to use new loader
4. Update `cli.py` to detect framework
5. Add optional dependencies to `requirements.txt`
6. Test with a PyTorch `.pt` file

---

## Notes

- All phases are optional -- add what you need
- Phases can be implemented independently
- Backward compatible -- existing API stays the same
- New features are additive, not breaking changes

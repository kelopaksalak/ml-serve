# Flask ML Backend

A reusable Flask REST API for registering scikit-learn models and serving predictions to web applications, mobile apps, desktop software, and other services.

Register multiple models and access each through its model ID. Clients send numeric features over HTTP and receive JSON predictions, so the backend can be used independently of a particular application or programming language.

## Current implementation

Requests pass through controllers, Marshmallow schemas, services, and SQLAlchemy models. All model endpoints are public. SQLite is the default database. Model files are loaded with joblib.

The CLI registers metadata in the database. It does not generate source files. Registration refers to an existing file in `ml_models/`; it is not a file-upload endpoint. Only load trusted model files because pickle-based formats can execute code.

## Local setup (PowerShell)

```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python test_model/generate_fake_model.py
python cli.py create-model fake_model --desc "Two-input regression demo"
python run.py
```

The demo generator writes `ml_models/fake_model.pkl`. It predicts the sum of two inputs, approximately: `[2, 3]` produces `5`. Use it to verify the API before registering your own trained models.

CLI commands:

```powershell
python cli.py create-model MODEL_NAME --desc "Description"
python cli.py list-models
```


## API contract

### Interactive Swagger documentation

Start the server with `python run.py`, then open http://127.0.0.1:5000/swagger/.
For Docker, apply source changes with `docker compose up --build -d`.
The OpenAPI 3.0 specification is available at `/openapi.json`.

Expand any model endpoint, click **Try it out**, enter its parameters, and click **Execute**. No login or token is needed.

Swagger serves its JavaScript and CSS locally through the pinned `flask-swagger-ui`
dependency. The external spec validator is disabled. Requests from **Try it out** execute real API operations.
The schema lives in `app/openapi.py`; update it when changing API contracts.
The integration follows the [flask-swagger-ui documentation](https://github.com/sveint/flask-swagger-ui).

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/ml_model` | List models |
| GET | `/api/ml_model/<id>` | Read model metadata |
| POST | `/api/ml_model` | Register an existing local model |
| POST | `/api/ml_model/<id>/predict` | Predict from an ordered numeric list |

Model registration request:

```json
{"name": "fake_model", "description": "Demo", "model_type": "regressor"}
```

`model_type` is optional; scikit-learn regressors are detected automatically. Names may contain letters, numbers, underscores and hyphens. Metadata `features` is a JSON-encoded string of feature names, or `"[]"` if the estimator has no feature names. Send prediction inputs in the training feature order.

Prediction request to `/api/ml_model/<id>/predict`:

```json
{"features": [2.0, 3.0]}
```

Prediction response:

```json
{"success": true, "data": {"prediction": 5.0}}
```

The API returns the model's raw prediction, which may be a numeric value, a class label, or an array depending on the estimator. Invalid payloads and model-processing errors return 400; missing model IDs return 404.

## Connecting any client

Any client capable of sending HTTP requests can call the API. Set `Content-Type: application/json`, send the feature list, and read the result from `data.prediction`.

For example, from JavaScript:

```javascript
const modelId = 1; // Replace with an ID returned by GET /api/ml_model.
const response = await fetch(`http://localhost:5000/api/ml_model/${modelId}/predict`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ features: [2.0, 3.0] }),
});

const result = await response.json();
if (!response.ok) {
  throw new Error(JSON.stringify(result.message ?? result));
}
console.log(result.data.prediction);
```

This example works in a JavaScript server runtime with `fetch` or a browser using the same origin as the API. Cross-origin browser access requires CORS configuration or a same-origin proxy; CORS is not currently configured.

## Using your own models

1. Train a scikit-learn estimator or pipeline outside this backend and export it with `joblib.dump()`.
2. Place the trusted `.pkl` file in `ml_models/`, using a name such as `price_predictor.pkl`.
3. Register it with `python cli.py create-model price_predictor` or `POST /api/ml_model`.
4. Find its ID using `GET /api/ml_model` and send requests to its prediction endpoint.

Models must accept a two-dimensional numeric input and provide a `predict()` method. Each request supplies one sample. Match the feature count, ordering, and preprocessing used during training. If preprocessing is needed, export a compatible pipeline along with the estimator. Keep the serving library versions compatible with those used to train the model.

## Configuration and deployment

`FLASK_ENV` selects `development` or `production`. `DATABASE_URL` is read from the environment or local `.env`.

```powershell
docker compose up --build -d
```

The Docker entry point is `gunicorn --bind 0.0.0.0:5000 run:app`. Compose mounts `ml_models/` and `instance/`. Keep the model files and their registered paths accessible in the deployment environment; register models there when moving from Windows to Docker.

PostgreSQL is optional and requires an installed driver and a matching SQLAlchemy `DATABASE_URL`. The default requirements do not include that driver. The app calls `db.create_all()` at startup; migration tooling is not configured, and `flask db upgrade` is not supported. Existing table alterations require a separate migration plan.

## Tests

```powershell
./venv/Scripts/python.exe -m unittest discover -s tests -v
```

Tests use an in-memory database and a temporary trained model. They do not modify the existing database or model files.

## Current scope

The backend provides model registration, metadata lookup, and single-sample inference. Model training and application-specific interpretation of predictions belong to the integrating project. File uploads, update/delete endpoints, batch prediction, confidence scores, model versioning, and multi-framework support are not currently implemented.

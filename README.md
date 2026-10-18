# Flask ML Backend

A Flask API for registering local scikit-learn model files and serving predictions.

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

The demo generator writes `ml_models/fake_model.pkl`. It predicts the sum of two inputs, approximately: `[2, 3]` produces `5`. It is not an adaptive difficulty model.

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

The API currently returns a raw prediction. It does not return confidence or `continue` / `repeat` / `advance`. Invalid payloads and model-processing errors return 400; missing model IDs return 404.

## Unity response parsing

The response values are nested inside `data`. These DTOs match the numeric demo:

```csharp
[System.Serializable]
public class PredictionData { public float prediction; }

[System.Serializable]
public class PredictionResponse
{
    public bool success;
    public PredictionData data;
}
```

After checking the HTTP request succeeded:

```csharp
PredictionResponse result = JsonUtility.FromJson<PredictionResponse>(predictionJson);
float prediction = result.data.prediction;
```

A classifier with string labels requires a corresponding prediction DTO. The Unity client itself is not present in this repository.

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

## Planned functionality

The VR adaptive-learning design is in `../../ml_model_unity.md`. Unity data collection, training on real session data, confidence-based difficulty decisions, update/delete endpoints, model versioning, monitoring, and multi-framework support are not implemented. `IMPROVEMENTS.md`, if present locally, describes future ideas rather than current features.

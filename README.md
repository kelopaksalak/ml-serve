# Flask ML Backend

A reusable Flask backend for registering scikit-learn models and serving predictions to web apps, mobile apps, desktop software, and other services.

Register multiple models and access each through its model ID. Clients send ordered numeric features over **HTTP** or a persistent **WebSocket** and receive JSON predictions. The backend is independent of any particular client language.

- REST API with Swagger UI
- WebSocket channel for `list`, `get`, and `predict`
- SQLite by default, PostgreSQL optional
- CLI for registering and listing models
- Docker and local development setups
- Unit/integration tests

---

## 1. Clone the repository

```powershell
git clone https://github.com/kelopaksalak/ml-serve.git
cd ml-serve
```

Model files (`ml_models/*.pkl`) and the SQLite database (`instance/`) are gitignored, so a fresh clone starts empty. You will generate a demo model below, or add your own.

## 2. Requirements

Choose **one** setup:

| Option | Needs |
|---|---|
| Docker (Option A) | Docker Desktop (or Docker Engine + Compose) |
| Local Python (Option B) | Python 3.11+ and `pip` |

Git is required for cloning. Commands below use PowerShell; macOS/Linux equivalents are shown where they differ.

---

## 3. Setup and run

### Option A — Docker (no local Python needed)

Build and start the container:

```powershell
docker compose up --build -d
```

Check that it is running:

```powershell
docker compose ps
docker compose logs -f web      # Ctrl+C to stop following logs
```

The API is now at http://localhost:5000.

Because the database and model folder are mounted from the host, generate and register the demo model **inside the running container**:

```powershell
docker compose exec web python test_model/generate_fake_model.py
docker compose exec web python cli.py create-model fake_model --desc "Two-input regression demo"
```

To stop the container:

```powershell
docker compose down
```

Rebuild after changing source files:

```powershell
docker compose up --build -d
```

### Option B — Local Python

**Windows (PowerShell):**

```powershell
python -m venv venv
./venv/Scripts/Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
python test_model/generate_fake_model.py
python cli.py create-model fake_model --desc "Two-input regression demo"
python run.py
```

If PowerShell blocks activation, run once in the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python test_model/generate_fake_model.py
python cli.py create-model fake_model --desc "Two-input regression demo"
python run.py
```

The server listens on http://127.0.0.1:5000. The demo model predicts the sum of two inputs, so `[2, 3]` produces approximately `5`.

> `python test_model/generate_fake_model.py` creates `ml_models/fake_model.pkl`. Registration only records metadata; it does not upload or generate model files.

---

## 4. Verify it works

### Swagger UI

Open http://localhost:5000/swagger/

Expand an endpoint, click **Try it out**, fill in the parameters, and click **Execute**. No login or token is needed. The raw OpenAPI 3.0.3 spec is at http://localhost:5000/openapi.json.

### List registered models

PowerShell:

```powershell
Invoke-RestMethod http://localhost:5000/api/ml_model
```

Bash:

```bash
curl -s http://localhost:5000/api/ml_model
```

### Predict with the demo model

Use the `id` returned by the list call (`1` in a fresh database):

PowerShell:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:5000/api/ml_model/1/predict -ContentType 'application/json' -Body '{"features":[2,3]}'
```

Bash:

```bash
curl -s -X POST http://localhost:5000/api/ml_model/1/predict \
  -H 'Content-Type: application/json' \
  -d '{"features":[2,3]}'
```

Response:

```json
{"success": true, "data": {"prediction": 5.0}}
```

### WebSocket

See the [WebSocket channel](#websocket-channel) section. Quick check with Postman: **New → WebSocket**, connect to `ws://localhost:5000/ws/ml_model`, choose **JSON** or **Text**, send `{"action":"list"}`, and click **Send**.

---

## 5. CLI commands

The CLI is `cli.py` (click). Run it from the project root, or with `docker compose exec web` in Docker.

| Command | Purpose |
|---|---|
| `python cli.py create-model NAME --desc "Description"` | Register an existing `ml_models/NAME.pkl` |
| `python cli.py list-models` | List registered models as `id. name (type)` |

```powershell
python cli.py create-model fake_model --desc "Two-input regression demo"
python cli.py list-models
```

Docker:

```powershell
docker compose exec web python cli.py create-model fake_model --desc "Demo"
docker compose exec web python cli.py list-models
```

`create-model` only registers metadata for a file that already exists in `ml_models/`. It validates names with the same rules as the API (letters, numbers, `_`, `-`) and rejects duplicates. Only load trusted pickle-based model files: loading them can execute code.

---

## 6. HTTP API

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/ml_model` | List models |
| GET | `/api/ml_model/<id>` | Read model metadata |
| POST | `/api/ml_model` | Register an existing local model |
| POST | `/api/ml_model/<id>/predict` | Predict from an ordered numeric list |

All model endpoints are public.

### Register a model

```json
{"name": "fake_model", "description": "Demo", "model_type": "regressor"}
```

`model_type` is optional (`classifier` or `regressor`); scikit-learn regressors are detected automatically. `features` metadata is a JSON-encoded string of feature names, or `"[]"` when the estimator has no feature names. Send prediction inputs in the training feature order.

### Predict

```json
{"features": [2.0, 3.0]}
```

```json
{"success": true, "data": {"prediction": 5.0}}
```

The API returns the model's raw prediction, which may be a number, a class label, or an array depending on the estimator. Invalid payloads and model-processing errors return `400`; missing model IDs return `404`.

### Calling it from JavaScript

```javascript
const modelId = 1; // Replace with an ID from GET /api/ml_model.
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

This works in a JavaScript server runtime with `fetch`, or in a browser using the same origin as the API. Cross-origin browser access requires CORS configuration, which is not currently set up.

---

## WebSocket channel

Endpoint: `ws://localhost:5000/ws/ml_model`

It serves the same operations as the read/predict HTTP endpoints over one persistent connection. Send one JSON object per message and receive one JSON envelope back, in order.

| Request | Response `data` |
|---|---|
| `{"action": "list"}` | Array of model metadata |
| `{"action": "get", "id": 1}` | Model metadata |
| `{"action": "predict", "id": 1, "features": [2.0, 3.0]}` | `{"prediction": 5.0}` |

Successful replies use `{"success": true, "data": ...}`. Errors use `{"success": false, "message": ...}` and keep the connection open, so a client can correct the request and continue. Unknown `id` values return `{"success": false, "message": "Model not found"}`.

### JavaScript

```javascript
const socket = new WebSocket("ws://localhost:5000/ws/ml_model");
socket.addEventListener("open", () => {
  socket.send(JSON.stringify({ action: "predict", id: 1, features: [2.0, 3.0] }));
});
socket.addEventListener("message", (event) => {
  const result = JSON.parse(event.data);
  if (!result.success) {
    throw new Error(JSON.stringify(result.message));
  }
  console.log(result.data.prediction);
});
```

### Python

`simple-websocket` is installed with `flask-sock`, so it is available in the same environment:

```python
import json
from simple_websocket import Client

ws = Client.connect("ws://localhost:5000/ws/ml_model")
ws.send(json.dumps({"action": "list"}))
print(ws.receive(timeout=5))

ws.send(json.dumps({"action": "predict", "id": 1, "features": [2.0, 3.0]}))
print(ws.receive(timeout=5))
ws.close()
```

### Postman

**New → WebSocket**, URL `ws://localhost:5000/ws/ml_model`, click **Connect**, select **JSON** (or **Text**) as the message format, paste a request, and click **Send**.

### Notes

- The WebSocket is not shown in Swagger/OpenAPI: OpenAPI 3.0 cannot describe `ws://` endpoints. Use Postman or a client library.
- To keep idle connections alive, set the optional app config:
  ```python
  app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
  ```
- Same-origin rules apply as for HTTP.

---

## Using your own models

### Where model files live

All model files must be stored in the `ml_models/` folder at the project root. The folder is gitignored, so it may be empty or missing after a fresh clone; create it if needed.

The server only reads from `ml_models/`. A `.pkl` file anywhere else (for example `test_model/fake_model.pkl`, which ships as a sample) is ignored.

The filename must be `<name>.pkl`, where `<name>` is exactly the name you register:

| You register with | The file must be |
|---|---|
| `python cli.py create-model price_predictor` | `ml_models/price_predictor.pkl` |
| `POST /api/ml_model` with `{"name": "price_predictor"}` | `ml_models/price_predictor.pkl` |

Registration does **not** copy, move, or upload the file. It records the file's absolute path in the database and loads the file from that path on every prediction. That path differs between a local run and Docker (`/app/ml_models/...` inside the container), which is why the Docker setup generates and registers the demo model inside the container.

### Steps

1. Train a scikit-learn estimator or pipeline outside this backend and export it with `joblib.dump()`.
2. Place the trusted `.pkl` file in `ml_models/`, for example `ml_models/price_predictor.pkl`.
3. Register it with `python cli.py create-model price_predictor` or `POST /api/ml_model`.
4. Find its ID with `GET /api/ml_model`, then send requests to its prediction endpoint (HTTP or WebSocket).

Models must accept a two-dimensional numeric input and provide a `predict()` method. Each request supplies one sample. Match the feature count, ordering, and preprocessing used during training. If preprocessing is needed, export a compatible pipeline along with the estimator. Keep the serving library versions compatible with those used to train the model.

---

## Project structure

```text
ml-serve/
├── app/
│   ├── __init__.py              # Application factory
│   ├── routes.py                # Registers HTTP blueprints
│   ├── openapi.py               # OpenAPI spec + Swagger UI
│   ├── websocket.py             # flask-sock setup
│   ├── controllers/             # HTTP and WebSocket handlers
│   ├── services/                # Model registration and prediction logic
│   ├── dto/                     # Marshmallow request/response schemas
│   ├── models/                  # SQLAlchemy models
│   └── database.py              # SQLAlchemy extension
├── tests/                       # unittest suite
├── test_model/
│   └── generate_fake_model.py   # Creates the demo .pkl
├── ml_models/                   # Model files (gitignored)
├── instance/                    # SQLite database (gitignored)
├── cli.py                       # create-model / list-models
├── config.py                    # development / production config
├── run.py                       # Development entry point
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

Request flow: controller → Marshmallow schema → service → SQLAlchemy model. WebSocket messages use the same service layer.

---

## Configuration

Local configuration is read from `.env` (copy `.env.example`):

```dotenv
FLASK_ENV=development
DATABASE_URL=sqlite:///ml_backend.db
```

- `FLASK_ENV`: `development` (debug on) or `production` (debug off).
- `DATABASE_URL`: SQLAlchemy URL. The default SQLite file is `instance/ml_backend.db`.
- PostgreSQL is optional and requires an installed driver plus a matching `DATABASE_URL`. The default requirements do not include that driver.
- The app calls `db.create_all()` at startup. Migration tooling is not configured, and `flask db upgrade` is not supported. Changing existing tables requires a separate migration plan.

### Docker deployment

`docker-compose.yml` runs:

```text
gunicorn --bind 0.0.0.0:5000 --threads 100 run:app
```

The threads let multiple HTTP and WebSocket clients be served at once; each open WebSocket holds one thread. Compose mounts `ml_models/` and `instance/` from the host. Keep model files and their registered paths accessible in the deployment environment, and register models there when moving between machines.

```powershell
docker compose up --build -d     # build and start
docker compose logs -f web       # follow logs
docker compose down              # stop
```

---

## Tests

Local:

```powershell
python -m unittest discover -s tests -v
```

In Docker (tests are excluded from the image by `.dockerignore`, so mount them):

```powershell
docker compose run --rm -v "${PWD}/tests:/app/tests" web python -m unittest discover -s tests -v
```

The suite uses an in-memory or temporary database and a temporary trained model. It does not modify your existing database or model files. It covers HTTP routes, the OpenAPI/Swagger contract, and the WebSocket protocol (list, get, predict, and error handling).

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `python` opens the Microsoft Store or is not found (Windows) | Install Python 3.11+ and disable the App Execution Alias for `python.exe`, or use the `py` launcher. |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` then activate again. |
| `Model file not found in ml_models/` | Run `python test_model/generate_fake_model.py` or place your `.pkl` there; register using the file's base name. |
| `/api/ml_model` returns an empty list | No model is registered yet. Generate the demo and run `create-model`, or `POST /api/ml_model`. |
| Port 5000 already in use | Stop the conflicting process, or change the published port in `docker-compose.yml` / the port in `run.py`. |
| Swagger page is blank | Use the trailing slash `http://localhost:5000/swagger/` and check `http://localhost:5000/openapi.json`. |
| WebSocket connects but closes immediately | Send **text/JSON** messages (not binary). Ensure the server is the Flask dev server or the thread-based gunicorn command above. |
| Source changes do not appear in Docker | Rebuild: `docker compose up --build -d`. |

---

## Security

Only load trusted model files. The project uses joblib/pickle-based formats, which can execute arbitrary code when loaded. Do not accept model files from untrusted sources.

---

## Current scope

The backend provides model registration, metadata lookup, and single-sample inference over HTTP and WebSocket. Model training and application-specific interpretation of predictions belong to the integrating project. File uploads, update/delete endpoints, batch prediction, confidence scores, model versioning, and multi-framework support are not currently implemented.

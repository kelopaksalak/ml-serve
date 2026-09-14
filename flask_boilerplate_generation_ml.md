# Flask Backend ML Model API - Boilerplate Generation System

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [CLI Tool](#cli-tool)
5. [Authentication](#authentication)
6. [Database](#database)
7. [Deployment](#deployment)
8. [Docker](#docker)
9. [Unity Integration](#unity-integration)
10. [Quick Start](#quick-start)

---

## Overview

A Flask backend with MVC architecture for serving scikit-learn ML models with auto-generated boilerplate.

### Key Features

- **Auto-generated boilerplate** via CLI tool
- **JWT authentication** for Unity VR/AR clients
- **SQLite** for development, **PostgreSQL** for production
- **Docker** support for professional deployment
- **MVC + Service + DTO** architecture

---

## Architecture

### MVC + Service + DTO Pattern

```
Request → Controller → DTO Validation → Service → Response DTO
```

### Components

| Layer | Purpose |
|-------|---------|
| **Controller** | Handles HTTP requests/responses |
| **Service** | Business logic |
| **DTO** | Request/Response validation (Marshmallow) |
| **Model** | SQLAlchemy database models |
| **Middleware** | Authentication decorators |

---

## Project Structure

```
ml_flask_backend/
├── ml_models/                          # Developer drops .pkl files here
│   ├── sentiment_analyzer.pkl
│   └── house_price_predictor.pkl
├── app/
│   ├── __init__.py                     # App factory
│   ├── models/                         # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── base.py                     # Base model
│   │   ├── user.py                     # User model (auth)
│   │   └── ml_model.py                 # ML model metadata
│   ├── controllers/                    # Blueprints
│   │   ├── __init__.py
│   │   ├── auth_controller.py          # Login/Register
│   │   └── ml_model_controller.py      # CRUD + Predict
│   ├── services/                       # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py             # JWT + User logic
│   │   └── ml_model_service.py         # ML operations
│   ├── dto/                            # Request/Response DTOs
│   │   ├── __init__.py
│   │   ├── base_dto.py                 # Common response format
│   │   ├── auth_dto.py                 # Login/Register schemas
│   │   └── ml_model_dto.py             # Model-specific schemas
│   ├── middleware/                      # Auth decorator
│   │   └── auth_middleware.py
│   ├── routes.py                       # Auto-registered routes
│   └── database.py                     # SQLite config
├── cli.py                              # CLI for scaffolding
├── config.py                           # Configuration
├── requirements.txt                    # Dependencies
├── run.py                              # Entry point
├── Dockerfile                          # Docker configuration
├── docker-compose.yml                  # Docker Compose
├── .env.example                        # Environment variables template
└── flask_boilerplate_generation_ml.md  # This documentation
```

---

## CLI Tool

### Installation

```bash
pip install click pyyaml scikit-learn marshmallow flask-sqlalchemy flask-jwt-extended
```

### Usage Commands

```bash
# Generate ML model scaffolding
python cli.py create-model sentiment_analyzer

# Generate with custom description
python cli.py create-model sentiment_analyzer --desc "Sentiment analysis model"

# List all registered models
python cli.py list-models

# Create initial admin user
python cli.py create-user --username admin --password secret123
```

### What CLI Generates

When you run `python cli.py create-model sentiment_analyzer`, it:

1. Loads `ml_models/sentiment_analyzer.pkl`
2. Introspects model features from `model.feature_names_in_`
3. Generates:
   - `app/controllers/sentiment_analyzer_controller.py`
   - `app/services/sentiment_analyzer_service.py`
   - `app/dto/sentiment_analyzer_dto.py`
   - `app/models/sentiment_analyzer.py`
4. Auto-registers routes in `routes.py`

### CLI Template Example

```python
# Controller template
from flask import Blueprint, request, jsonify
from app.dto.{name}_dto import {Name}RequestSchema, {Name}ResponseSchema
from app.services.{name}_service import {Name}Service
from app.middleware.auth_middleware import require_auth

{name}_bp = Blueprint('{name}_bp', __name__)
{name}_service = {Name}Service()

@{name}_bp.route('/api/{name}', methods=['GET'])
@require_auth
def get_all():
    models = {name}_service.get_all()
    return jsonify({Name}ResponseSchema().dump(models, many=True))

@{name}_bp.route('/api/{name}/<int:id>', methods=['GET'])
@require_auth
def get_by_id(id):
    model = {name}_service.get_by_id(id)
    return jsonify({Name}ResponseSchema().dump(model))

@{name}_bp.route('/api/{name}', methods=['POST'])
@require_auth
def create():
    schema = {Name}RequestSchema()
    data = schema.load(request.json)
    model = {name}_service.create(data)
    return jsonify({Name}ResponseSchema().dump(model)), 201

@{name}_bp.route('/api/{name}/<int:id>/predict', methods=['POST'])
@require_auth
def predict(id):
    schema = {Name}RequestSchema()
    data = schema.load(request.json)
    result = {name}_service.predict(id, data)
    return jsonify({'prediction': result})
```

---

## Authentication

### JWT Flow

```
Unity Client                    Flask Backend
     │                               │
     │  POST /api/auth/login         │
     │  {username, password}         │
     │  ──────────────────────────►  │
     │                               │  Validate credentials
     │                               │  Generate JWT token
     │  Return JWT token             │
     │  ◄──────────────────────────  │
     │                               │
     │  POST /api/ml_model/predict   │
     │  Header: Authorization: Bearer <token>
     │  ──────────────────────────►  │
     │                               │  Verify JWT token
     │                               │  Run prediction
     │  Return prediction result     │
     │  ◄──────────────────────────  │
```

### Endpoints

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/api/auth/register` | No | Create new user |
| POST | `/api/auth/login` | No | Get JWT token |
| GET | `/api/auth/me` | Yes | Get current user info |
| GET | `/api/ml_model` | Yes | List all models |
| GET | `/api/ml_model/<id>` | Yes | Get specific model |
| POST | `/api/ml_model` | Yes | Upload new model |
| PUT | `/api/ml_model/<id>` | Yes | Update model |
| DELETE | `/api/ml_model/<id>` | Yes | Delete model |
| POST | `/api/ml_model/<id>/predict` | Yes | Run prediction |

### JWT Configuration

```python
# config.py
class Config:
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
```

---

## Database

### SQLite (Development)

```python
# config.py
class DevelopmentConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///ml_backend.db'
```

### PostgreSQL (Production)

```python
# config.py
class ProductionConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Example: postgresql://user:pass@localhost/ml_backend
```

### Tables

| Table | Columns | Purpose |
|-------|---------|---------|
| **users** | id, username, password_hash, created_at | User authentication |
| **ml_models** | id, name, description, model_type, features, model_path, created_by, created_at, updated_at | ML model metadata |

### Model Definitions

```python
# app/models/user.py
from app.database import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

```python
# app/models/ml_model.py
from app.database import db

class MLModel(db.Model):
    __tablename__ = 'ml_models'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    model_type = db.Column(db.String(50))  # classifier/regressor
    features = db.Column(db.Text)  # JSON array of feature names
    model_path = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## Deployment

### Render (Recommended)

#### render.yaml

```yaml
services:
  - type: web
    name: ml-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app
    plan: free
    envVars:
      - key: FLASK_ENV
        value: production
      - key: SECRET_KEY
        generateValue: true
      - key: JWT_SECRET_KEY
        generateValue: true
```

#### Deployment Steps

1. Push to GitHub
2. Go to [render.com](https://render.com)
3. Sign up with GitHub
4. Click "New Web Service"
5. Select your repository
6. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Instance Type: Free
7. Click "Create Web Service"

#### Free Tier Limits

| Feature | Limit |
|---------|-------|
| Instance Hours | 750 hrs/month |
| Cold Start | 30-50 seconds |
| Filesystem | Ephemeral |
| PostgreSQL | 30 days free |

### Migration Path

```
Development: SQLite (quick iteration)
Production: PostgreSQL (when scaling needed)
```

#### SQLite → PostgreSQL Migration

```bash
# 1. Install PostgreSQL driver
pip install psycopg2-binary

# 2. Create PostgreSQL database
createdb ml_backend

# 3. Set environment variable
export DATABASE_URL="postgresql://user:password@localhost/ml_backend"

# 4. Run migrations
flask db upgrade

# Done! Same code, different database
```

---

## Docker

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - DATABASE_URL=sqlite:///ml_backend.db
    volumes:
      - ./ml_models:/app/ml_models
      - ./instance:/app/instance
    restart: unless-stopped

  # Optional: PostgreSQL for production
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ml_backend
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Docker Commands

```bash
# Build image
docker build -t ml-backend .

# Run container
docker run -p 5000:5000 -v ./ml_models:/app/ml_models ml-backend

# Run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

### Why Docker for Your Project

| Benefit | Description |
|---------|-------------|
| **Consistency** | Same environment everywhere |
| **Portability** | Deploy to any platform |
| **Isolation** | No dependency conflicts |
| **Professional** | Industry standard |
| **Scalability** | Easy to scale with Kubernetes |

---

## Unity Integration

### C# Example

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;

public class MLBackendClient : MonoBehaviour
{
    private string baseURL = "http://your-flask-api.com";
    private string jwtToken;

    [System.Serializable]
    public class LoginRequest
    {
        public string username;
        public string password;
    }

    [System.Serializable]
    public class LoginResponse
    {
        public string token;
        public string message;
    }

    [System.Serializable]
    public class PredictionRequest
    {
        public float[] features;
    }

    [System.Serializable]
    public class PredictionResponse
    {
        public float prediction;
        public float confidence;
    }

    // Login to get JWT token
    public IEnumerator Login(string username, string password)
    {
        LoginRequest loginData = new LoginRequest
        {
            username = username,
            password = password
        };

        string json = JsonUtility.ToJson(loginData);
        
        UnityWebRequest request = new UnityWebRequest($"{baseURL}/api/auth/login", "POST");
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            LoginResponse response = JsonUtility.FromJson<LoginResponse>(request.downloadHandler.text);
            jwtToken = response.token;
            Debug.Log("Login successful!");
        }
        else
        {
            Debug.LogError("Login failed: " + request.error);
        }
    }

    // Call prediction endpoint
    public IEnumerator Predict(int modelId, float[] features, System.Action<PredictionResponse> callback)
    {
        PredictionRequest predRequest = new PredictionRequest
        {
            features = features
        };

        string json = JsonUtility.ToJson(predRequest);

        UnityWebRequest request = new UnityWebRequest($"{baseURL}/api/ml_model/{modelId}/predict", "POST");
        byte[] bodyRaw = System.Text.Encoding.UTF8.GetBytes(json);
        request.uploadHandler = new UploadHandlerRaw(bodyRaw);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");
        request.SetRequestHeader("Authorization", $"Bearer {jwtToken}");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            PredictionResponse response = JsonUtility.FromJson<PredictionResponse>(request.downloadHandler.text);
            callback?.Invoke(response);
        }
        else
        {
            Debug.LogError("Prediction failed: " + request.error);
        }
    }
}
```

### Unity Usage Example

```csharp
public class MLManager : MonoBehaviour
{
    private MLBackendClient apiClient;

    void Start()
    {
        apiClient = GetComponent<MLBackendClient>();
        StartCoroutine(apiClient.Login("admin", "password123"));
    }

    public void MakePrediction()
    {
        float[] features = new float[] { 1.0f, 2.5f, 3.0f };
        StartCoroutine(apiClient.Predict(1, features, (response) =>
        {
            Debug.Log($"Prediction: {response.prediction}, Confidence: {response.confidence}");
        }));
    }
}
```

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd ml_flask_backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Create admin user
python cli.py create-user --username admin --password secret123
```

### 3. Add ML Model

```bash
# Drop pkl file into ml_models/ folder
cp /path/to/your/model.pkl ml_models/sentiment_analyzer.pkl

# Generate boilerplate
python cli.py create-model sentiment_analyzer
```

### 4. Run Locally

```bash
python run.py
```

### 5. Deploy to Render

```bash
git add .
git commit -m "Initial commit"
git push origin main

# Go to render.com and deploy
```

### 6. Run with Docker

```bash
docker-compose up -d
```

---

## Configuration

### Environment Variables (.env)

```bash
# .env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///ml_backend.db
JWT_SECRET_KEY=your-jwt-secret-here
JWT_EXPIRATION_HOURS=24
```

### config.py

```python
import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///ml_backend.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.environ.get('JWT_EXPIRATION_HOURS', 24)))

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
```

---

## Best Practices

| Area | Practice |
|------|----------|
| **Security** | Never commit secrets, use environment variables |
| **Database** | Use migrations (Flask-Migrate) |
| **Testing** | Write unit tests for services |
| **Logging** | Use Flask's built-in logging |
| **Error Handling** | Use try-except with proper HTTP responses |
| **Code Style** | Follow PEP 8, use Black formatter |
| **Documentation** | Keep README and docs updated |

---

## License

MIT License

<div align="center">

# Flask ML Backend

A Flask backend for serving scikit-learn models through REST APIs, with CLI-based boilerplate generation for new models.

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com)

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Technology Stack](#technology-stack)
4. [Architecture](#architecture)
5. [Project Structure](#project-structure)
6. [How the ML Model System Works](#how-the-ml-model-system-works)
7. [CLI Tool](#cli-tool)
8. [Authentication](#authentication)
9. [Database](#database)
10. [Configuration](#configuration)
11. [Local Development](#local-development)
12. [Docker](#docker)
13. [Troubleshooting](#troubleshooting)
14. [Contributing](#contributing)

---

## Overview

A Flask backend that lets you serve scikit-learn `.pkl` models through a REST API. Drop a model file, run one CLI command, and it generates all the boilerplate code needed to expose a prediction endpoint with JWT authentication.

Works with any HTTP client -- web apps, mobile apps, Unity, or any other platform.

---

## Features

- CLI tool for scaffolding new ML model endpoints
- scikit-learn model support via `.pkl` files
- JWT authentication
- User registration and login
- ML model CRUD operations
- Prediction endpoint
- SQLite (dev) / PostgreSQL (prod)
- Docker support
- MVC + Service + DTO architecture

---

## Technology Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Core language |
| **Flask** | REST API framework |
| **scikit-learn** | ML model loading and prediction |
| **SQLAlchemy** | Database ORM |
| **Marshmallow** | Request/response validation |
| **Flask-JWT-Extended** | JWT authentication |
| **Click** | CLI tool |
| **Gunicorn** | Production server |
| **Docker** | Containerized deployment |

---

## Architecture

MVC + Service + DTO pattern:

```
Request --> Controller --> DTO Validation --> Service --> Model/ML --> Response
```

| Layer | Responsibility |
|---|---|
| **Controller** | HTTP routes and responses |
| **DTO** | Input/output validation |
| **Service** | Business logic |
| **Model** | Database entities |
| **Middleware** | JWT auth decorator |

---

## Project Structure

```
ml_flask_backend/
|-- ml_models/                  # Drop .pkl files here
|-- app/
|   |-- __init__.py             # App factory
|   |-- database.py             # SQLAlchemy instance
|   |-- routes.py               # Blueprint registration
|   |-- models/                 # Database models
|   |-- controllers/            # Route handlers
|   |-- services/               # Business logic
|   |-- dto/                    # Validation schemas
|   +-- middleware/              # Auth decorator
|-- cli.py                      # CLI tool
|-- config.py                   # Configuration
|-- run.py                      # Entry point
|-- requirements.txt
|-- Dockerfile
+-- docker-compose.yml
```

---

## How the ML Model System Works

1. Place your `.pkl` file in `ml_models/`
2. Run `python cli.py create-model <name>`
3. CLI reads model features and saves metadata to database
4. API endpoints become available
5. Client sends features, gets prediction back

---

## CLI Tool

```bash
# Create a user
python cli.py create-user --username admin --password <your-password>

# Register a model
python cli.py create-model <model-name> --desc "Description"

# List all models
python cli.py list-models
```

---

## Authentication

1. Register: `POST /api/auth/register`
2. Login: `POST /api/auth/login` -- returns JWT token
3. Send token with requests: `Authorization: Bearer <token>`
4. Protected endpoints verify the token automatically

---

## Database

**Development:** SQLite (auto-created, no setup needed)

**Production:** PostgreSQL via `DATABASE_URL` env variable

### Tables

**users** -- id, username, password_hash, created_at

**ml_models** -- id, name, description, model_type, features, model_path, created_by, created_at, updated_at

---

## Configuration

Create a `.env` file:

```bash
FLASK_ENV=development
SECRET_KEY=<your-secret-key>
DATABASE_URL=sqlite:///ml_backend.db
JWT_SECRET_KEY=<your-jwt-secret>
```

| Variable | Default |
|---|---|
| `FLASK_ENV` | `development` |
| `SECRET_KEY` | `dev-secret-key` |
| `DATABASE_URL` | `sqlite:///ml_backend.db` |
| `JWT_SECRET_KEY` | `jwt-secret-key` |

---

## Local Development

```bash
# Clone
git clone <repository-url>
cd ml_flask_backend

# Virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux

# Install
pip install -r requirements.txt

# Create user
python cli.py create-user --username admin --password <your-password>

# Run
python run.py
```

Server runs at `http://127.0.0.1:5000`.

---

## Docker

```bash
docker build -t ml-backend .
docker run -p 5000:5000 ml-backend
```

Or with Docker Compose:

```bash
docker compose up -d
docker compose down
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `ModuleNotFoundError: flask_jwt_extended` | Run `pip install -r requirements.txt` |
| `NoReferencedTableError` foreign key | Ensure `User` model is imported before `db.create_all()` |
| Model not found when registering | Check `.pkl` file is in `ml_models/` and name matches |
| `Schema.dump() missing argument` | Use `Schema().dump(data)` not `Schema.dump(data)` |
| JWT token expired | Re-login (tokens expire after 24h) |

---

## Contributing

1. Create a feature branch
2. Make your changes
3. Test locally
4. Commit and push
5. Open a pull request

# ModelGate

ModelGate is a FastAPI-based API gateway for machine learning services. It provides:

- user authentication with JWT access tokens
- API key management for model access
- model registry and version management
- prediction forwarding to remote model services
- Redis-backed prediction caching
- usage tracking and analytics

The goal of the project is to give you a single backend for managing ML models, serving predictions, and collecting usage metrics in one place.

## Features

### Authentication
- register and login with a `username` and password
- JWT bearer-token authentication for protected routes
- dependency-based route protection with FastAPI

### API Keys
- create and revoke API keys
- validate API keys when calling prediction routes
- track usage per key and per model version

### Model Registry
- create models under an authenticated user
- manage model versions
- route predictions by model name
- pick the latest model version automatically when no version is provided

### Prediction Gateway
- forward requests to a model service `service_url`
- cache successful predictions in Redis
- return cached results when available
- record latency, cache hit status, and response status code

### Analytics
- dashboard overview
- usage history
- latency stats
- top models
- per-model analytics
- per-version analytics
- API key analytics

## Tech Stack

- **FastAPI** for the HTTP API
- **SQLAlchemy 2.x async** for database access
- **PostgreSQL** for persistent storage
- **Redis** for prediction caching
- **httpx** for forwarding prediction requests to upstream model services
- **JWT** for authentication
- **pwdlib** for password hashing

## Project Structure

```text
ModelGate/
├── app/
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── redis.py
│   ├── schemas.py
│   ├── services/
│   │   ├── cache.py
│   │   └── model_queries.py
│   └── routers/
│       ├── analytics.py
│       ├── apikeys.py
│       ├── auth.py
│       ├── model_queries.py
│       ├── predict.py
│       ├── registry.py
│       ├── users.py
│       └── versions.py
└── README.md
```

## Core Flow

1. A user registers and logs in.
2. The user creates one or more API keys.
3. The user registers a model and one or more versions.
4. A client calls the prediction endpoint with:
   - `X-API-Key`
   - model name
   - optional version
   - request payload
5. ModelGate:
   - validates the API key
   - resolves the model and version
   - checks Redis for a cached prediction
   - forwards the request to the upstream model service when needed
   - stores successful responses in Redis
   - writes usage data to the database
6. Analytics endpoints summarize usage across models, versions, and API keys.

## API Overview

### Auth
- `POST /auth/register`
- `POST /auth/login`

### Users
- `GET /users/me`
- `GET /users/{id}`
- `PATCH /users/{id}`
- `DELETE /users/{id}`

### API Keys
- `POST /apikeys/create`
- `GET /apikeys/`
- `DELETE /apikeys/{key_id}`

### Models
- `POST /models/`
- `GET /models/`
- `GET /models/{model_id}`
- `PATCH /models/{model_id}`

### Model Versions
- `POST /models/{model_id}/versions/`
- `GET /models/{model_id}/versions/`
- `GET /models/{model_id}/versions/latest`
- `GET /models/{model_id}/versions/{version}`
- `PATCH /models/{model_id}/versions/{version}`
- `DELETE /models/{model_id}/versions/{version}`

### Predictions
- `POST /predict/{model_name}`

Headers:
- `X-API-Key: <your_api_key>`

Query parameters:
- `version` optional; if omitted, the latest active version is used

### Analytics
- `GET /analytics/dashboard`
- `GET /analytics/usage`
- `GET /analytics/top-models`
- `GET /analytics/latency`
- `GET /analytics/models/{model_id}`
- `GET /analytics/models/{model_id}/versions`
- `GET /analytics/apikeys`

## Data Model Summary

### User
Stores user accounts and authentication data.

### APIKey
Stores hashed API keys linked to a user.

### ModelRegistry
Stores the model metadata, including owner and task type.

### ModelVersions
Stores version-specific deployment data such as:
- version label
- service URL
- artifact URI
- status

### APIUsage
Stores request metrics such as:
- user
- API key
- model version
- latency
- status code
- cache hit flag

## Getting Started

## Prerequisites

Make sure you have:
- Python 3.11+ recommended
- PostgreSQL running locally or remotely
- Redis running locally or remotely

## 1. Clone the repository

```bash
git clone <your-repo-url>
cd ModelGate
```

## 2. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3. Install dependencies

Install the packages your project needs. If you already have a requirements file, use it. Otherwise install the main runtime dependencies:

```bash
pip install fastapi uvicorn sqlalchemy asyncpg pydantic pydantic-settings python-dotenv pwdlib pyjwt httpx redis
```

If your project uses additional packages for development or migration tooling, install those as well.

## 4. Configure environment variables

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/modelgate
SECRET_KEY=change-this-to-a-long-random-string
REDIS_URL=redis://localhost:6379/0
```

If your `app/config.py` expects more settings, add them there too.

## 5. Start PostgreSQL and Redis

Make sure both services are running before starting the API.

Examples:

```bash
# PostgreSQL
sudo service postgresql start

# Redis
sudo service redis-server start
```

Or run them with Docker if that is how your environment is set up.

## 6. Run the FastAPI app

From the project root:

```bash
uvicorn app.main:app --reload
```

The API should now be available at:

```text
http://127.0.0.1:8000
```

Interactive docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 7. Register and log in

### Register

Send a request to:

```http
POST /auth/register
```

Example payload:

```json
{
  "username": "alice",
  "password": "securepassword",
  "role": "user"
}
```

### Log in

Send a request to:

```http
POST /auth/login
```

Use form data fields:
- `username`
- `password`

You will receive a JWT access token.

## 8. Create an API key

After logging in, create an API key:

```http
POST /apikeys/create
```

This route is protected by JWT authentication.

The response returns the raw key once, so store it securely.

## 9. Register a model and version

Create a model with the authenticated user, then add a model version pointing at an upstream inference service.

Example model version data:

```json
{
  "version": "v1",
  "service_url": "https://your-model-service.example.com/predict",
  "artifact_uri": "s3://your-bucket/model-artifact",
  "status": "ACTIVE"
}
```

## 10. Call predictions

Send a prediction request to:

```http
POST /predict/{model_name}
```

Required header:

```http
X-API-Key: pk_live_...
```

Optional query parameter:

```http
?version=v1
```

If you omit `version`, ModelGate uses the latest active version.

## Example Prediction Request

```http
POST /predict/my-model?version=v1
X-API-Key: pk_live_example
Content-Type: application/json
```

Body:

```json
{
  "input": {
    "text": "Hello world"
  }
}
```

## Caching Behavior

Prediction caching works like this:

- cache key is based on:
  - model name
  - version
  - request payload
- Redis is checked before hitting the upstream service
- if a cached response exists, it is returned immediately
- if not, the request is forwarded to the upstream service
- successful responses are stored in Redis
- usage metrics record whether the response was cached

## Development Notes

- Protected routes use JWT-based authentication.
- Prediction requests use API keys, not JWT.
- The project is still evolving, so some routes may be intentionally minimal while the structure is being completed.
- For production, replace placeholder defaults with secure secrets and add migrations with Alembic.

## Next Steps

Recommended follow-up work:
- add test coverage for auth, models, versions, and predictions
- add API key-level usage analytics if you want per-key request breakdowns
- add cache invalidation when versions are updated or deleted
- improve response models for analytics endpoints if you want stricter typing

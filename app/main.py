# python3 -m venv .venv
# source .venv/bin/activate

# uvicorn app.main:app = runs FastAPI app in web server
# uvicorn app.main:app --reload = runs FastAPI app in web server with auto-reload

from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import engine, Base
from app.routers import users, auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="MLserve", lifespan=lifespan)

try:
    app.include_router(users.router)
except Exception as e:
    print(f"failed to include users router: {e}")

try:
    app.include_router(auth.router)
except Exception as e:
    print(f"failed to include auth router: {e}")

# -- FastAPI path -- similar to route
@app.get("/") 
# decorator that makes the method GET to FastAPI
# "/" refers to path where the function returns
async def root(): # name of func doesnt matter
    return {"message": "API is running"}


# @app.post("/apikeys")
# async def create_apikey():
#     key = 'pk_live_' + secrets.token_hex(16)
#     return {"key": key}

# @app.get("/apikeys")
# async def get_apikeys():
#     return {}

# @app.get("/api_usage")
# async def get_api_usage():
#     return {}

# @app.delete("/apikeys/{key}")
# async def delete_apikey(key: str):
#     return {}

# @app.get("/models")
# async def get_models():
#     return {}

# @app.post("/models/")
# async def register_model():
#     return {}

# @app.patch("/models/{id}")
# async def update_model(id: int, fields: dict):
#     return {}

# @app.post("/models/{id}/versions")
# async def add_model_version(id: int, version: str):
#     return {}

# @app.patch("/models/{id}/versions/{version}")
# async def update_model_version(id: int, version: str, fields: dict):
#     return {}

# @app.post("/predict/{model}")
# async def predict(model: str, data: dict):
#     return {"prediction": "", "cached": ""}


# @app.get("/analytics/top-users")
# async def get_top_users():
#     return {}

# @app.get("/analytics/models")
# async def get_models_analytics():
#     return {}

# @app.get("/analytics/latency")
# async def get_latency_analytics():
#     return {}

# @app.get("/analytics/cache")
# async def get_cache_analytics():
#     return {}

# python3 -m venv .venv
# source .venv/bin/activate

# uvicorn app.main:app = runs FastAPI app in web server
# uvicorn app.main:app --reload = runs FastAPI app in web server with auto-reload

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI

from app.database import Base, engine
from app.routers import apikeys, auth, predict, registry, users, versions


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="ModelGate", lifespan=lifespan)

try:
    app.include_router(auth.router)
    from app.routers.auth import get_current_user

    app.include_router(users.router, dependencies=[Depends(get_current_user)])
    app.include_router(apikeys.router, dependencies=[Depends(get_current_user)])
    app.include_router(registry.router, dependencies=[Depends(get_current_user)])
    app.include_router(predict.router, dependencies=[Depends(get_current_user)])
    app.include_router(versions.router, dependencies=[Depends(get_current_user)])

except Exception as e:
    print(f"failed to include router: {e}")


# -- FastAPI path -- similar to route
@app.get("/")
# decorator that makes the method GET to FastAPI
# "/" refers to path where the function returns
async def root():  # name of func doesnt matter
    return {"message": "API is running"}

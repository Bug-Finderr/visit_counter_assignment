from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from .core.config import settings
from .api.v1.api import api_router
from .api.v1.endpoints.counter import redis_manager

app = FastAPI(title="Visit Counter Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def health_check():
    return {"status": "healthy"}


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# ready while at least 1 shard answers. 1 shard down hits every pod the same way, pulling pods out would turn a partial outage into a full one
@app.get("/readyz")
def readyz(response: Response):
    down = redis_manager.unreachable_nodes()
    ready = len(down) < len(redis_manager.redis_clients)
    if not ready: response.status_code = 503
    return {"ready": ready, "down": down}


@app.get("/version")
async def version():
    return {"version": settings.GIT_SHA}


app.include_router(api_router, prefix=settings.API_PREFIX)

Instrumentator(excluded_handlers=["/metrics", "/healthz", "/readyz"]).instrument(app).expose(app)

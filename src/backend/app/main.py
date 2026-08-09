import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

# PyInstaller with console=False on Windows sets sys.stdout/stderr to None;
# uvicorn's DefaultFormatter calls sys.stdout.isatty() and crashes without this.
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w")

from docker.errors import APIError, DockerException, NotFound
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from app.api import router
from app.api.ws import router as ws_router
from app.core.config import settings
from app.core.database import engine
from app.core.process import monitor_parent
from app.core.version import APP_VERSION
from app.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    parent_pid = os.environ.get("DOCKORE_PARENT_PID")
    monitor_task = None
    if parent_pid:
        try:
            monitor_task = asyncio.create_task(monitor_parent(int(parent_pid)))
        except ValueError:
            pass
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    if monitor_task:
        monitor_task.cancel()


app = FastAPI(
    title="Dockore",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFound)
async def docker_not_found_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.exception_handler(APIError)
async def docker_api_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.exception_handler(DockerException)
async def docker_error_handler(request, exc):
    return JSONResponse(status_code=502, content={"detail": str(exc)})


app.include_router(router, prefix="/api")
app.include_router(ws_router)


def run_server() -> None:
    import uvicorn

    reload = os.environ.get("DOCKORE_RELOAD", "") in ("1", "true", "yes")
    uvicorn.run(
        "app.main:app" if reload else app,
        host=settings.dockore_host,
        port=settings.dockore_port,
        reload=reload,
    )


if __name__ == "__main__":
    run_server()

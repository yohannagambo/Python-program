from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.api import auth, devices, files, monitoring, security
from backend.app.config import settings
from backend.app.database import SessionLocal, init_db
from backend.app.api.auth import ensure_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    with SessionLocal() as db:
        ensure_admin(db)

    yield


app = FastAPI(
    title=settings.app_name,
    description="Authorized Windows endpoint monitoring and management API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Device-Token"],
)

prefix = settings.api_prefix

app.include_router(auth.router, prefix=prefix)
app.include_router(devices.router, prefix=prefix)
app.include_router(files.router, prefix=prefix)
app.include_router(monitoring.router, prefix=prefix)
app.include_router(security.router, prefix=prefix)


@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "application": settings.app_name,
        "environment": settings.environment,
    }


dashboard_dir = Path(__file__).resolve().parents[2] / "dashboard"

if dashboard_dir.exists():
    app.mount(
        "/dashboard",
        StaticFiles(directory=dashboard_dir, html=True),
        name="dashboard",
    )

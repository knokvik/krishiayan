from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from krishiayan import __version__
from krishiayan.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Soil intelligence brain: raw probe packets → fertilizer what/when, crop condition, weather, tool insights.",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["system"])
def healthz() -> dict:
    return {"status": "ok", "service": settings.app_name, "version": __version__}


@app.get("/", tags=["system"])
def root() -> dict:
    return {
        "name": settings.app_name,
        "version": __version__,
        "docs": "/docs",
        "health": "/healthz",
    }

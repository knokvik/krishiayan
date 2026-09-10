from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from krishiayan import __version__
from krishiayan.api.routes import auth, farms, ingest, weather
from krishiayan.core.config import get_settings
from krishiayan.core.db import SessionLocal, init_db
from krishiayan.services.crops import seed_crops

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = SessionLocal()
    try:
        seed_crops(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title=settings.app_name,
    version=__version__,
    description="Soil intelligence brain: raw probe packets → fertilizer what/when, crop condition, weather, tool insights.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(farms.router)
app.include_router(ingest.router)
app.include_router(weather.router)


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

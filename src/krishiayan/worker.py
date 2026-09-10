"""Optional Celery worker. Inference stays synchronous if Redis is down."""

from celery import Celery

from krishiayan.core.config import get_settings

settings = get_settings()
celery_app = Celery("krishiayan", broker=settings.celery_broker_url, backend=settings.redis_url)
celery_app.conf.task_always_eager = settings.app_env == "test"


@celery_app.task(name="krishiayan.fetch_weather")
def fetch_weather_task(field_id: str) -> str:
    from krishiayan.core.db import SessionLocal
    from krishiayan.models.entities import Field
    from krishiayan.services.weather import weather_for_field

    db = SessionLocal()
    try:
        field = db.get(Field, field_id)
        if field is None:
            return "missing"
        weather_for_field(db, field, force=True)
        return "ok"
    finally:
        db.close()

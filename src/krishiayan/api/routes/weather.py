from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from krishiayan.api.deps import get_current_user
from krishiayan.api.routes.farms import _owned_field
from krishiayan.core.db import get_db
from krishiayan.models.entities import User
from krishiayan.services.weather import weather_for_field

router = APIRouter(prefix="/v1", tags=["weather"])


@router.get("/fields/{field_id}/weather")
def field_weather(
    field_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    field = _owned_field(db, user, field_id)
    try:
        return weather_for_field(db, field)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"weather upstream failed: {exc}") from exc

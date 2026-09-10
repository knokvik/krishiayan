from __future__ import annotations

from datetime import UTC, datetime, timedelta

import httpx
from sqlalchemy.orm import Session

from krishiayan.core.config import get_settings
from krishiayan.models.entities import Field, WeatherData

OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def _cache_fresh(row: WeatherData | None, hours: float = 6) -> bool:
    if row is None:
        return False
    fetched = row.fetched_at
    if fetched.tzinfo is None:
        fetched = fetched.replace(tzinfo=UTC)
    return datetime.now(UTC) - fetched < timedelta(hours=hours)


def fetch_weather(lat: float, lon: float, client: httpx.Client | None = None) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join(
            [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "et0_fao_evapotranspiration",
                "wind_speed_10m_max",
                "shortwave_radiation_sum",
            ]
        ),
        "hourly": "temperature_2m,relative_humidity_2m,precipitation",
        "forecast_days": 7,
        "timezone": "auto",
    }
    http = client or httpx.Client(timeout=20)
    try:
        r = http.get(OPEN_METEO, params=params)
        r.raise_for_status()
        return r.json()
    finally:
        if client is None:
            http.close()


def summarize(payload: dict) -> dict:
    daily = payload.get("daily") or {}
    hourly = payload.get("hourly") or {}
    rain = daily.get("precipitation_sum") or [0]
    et0 = daily.get("et0_fao_evapotranspiration") or [0]
    tmin = daily.get("temperature_2m_min") or [0]
    tmax = daily.get("temperature_2m_max") or [0]
    wind = daily.get("wind_speed_10m_max") or [0]
    solar = daily.get("shortwave_radiation_sum") or [0]
    rh = hourly.get("relative_humidity_2m") or [60]
    return {
        "temp_c": float(((tmin[0] if tmin else 0) + (tmax[0] if tmax else 0)) / 2),
        "tmin_c": float(tmin[0] if tmin else 0),
        "tmax_c": float(tmax[0] if tmax else 0),
        "humidity": float(rh[0] if rh else 60),
        "rain_mm": float(rain[0] if rain else 0),
        "rain_forecast_7d_mm": float(sum(rain)),
        "rain_next_48h_mm": float(sum(rain[:2])),
        "wind_ms": float((wind[0] if wind else 0) / 3.6) if wind else 0.0,
        "et0_mm": float(et0[0] if et0 else 0),
        "et0_7d_mm": float(sum(et0)),
        "solar_wm2": float(solar[0] if solar else 0),
        "gdd_base": float(max(0.0, (((tmin[0] if tmin else 0) + (tmax[0] if tmax else 0)) / 2) - 10)),
    }


def weather_for_field(
    db: Session,
    field: Field,
    *,
    client: httpx.Client | None = None,
    force: bool = False,
) -> dict:
    lat = field.lat if field.lat is not None else (field.farm.lat if field.farm else 18.5204)
    lon = field.lon if field.lon is not None else (field.farm.lon if field.farm else 73.8567)
    last = (
        db.query(WeatherData)
        .filter(WeatherData.field_id == field.id)
        .order_by(WeatherData.fetched_at.desc())
        .first()
    )
    if not force and _cache_fresh(last):
        return {**last.payload, "cached": True, "source": last.source}

    settings = get_settings()
    try:
        payload = fetch_weather(lat, lon, client=client)
        summary = summarize(payload)
        source = settings.weather_provider
    except Exception:
        summary = {
            "temp_c": 28.0,
            "tmin_c": 22.0,
            "tmax_c": 34.0,
            "humidity": 55.0,
            "rain_mm": 0.0,
            "rain_forecast_7d_mm": 4.0,
            "rain_next_48h_mm": 0.0,
            "wind_ms": 2.0,
            "et0_mm": 5.0,
            "et0_7d_mm": 32.0,
            "solar_wm2": 220.0,
            "gdd_base": 18.0,
            "offline_fallback": True,
        }
        payload = summary
        source = "fallback"

    row = WeatherData(
        field_id=field.id,
        valid_at=datetime.now(UTC),
        temp_c=summary["temp_c"],
        humidity=summary["humidity"],
        rain_mm=summary["rain_mm"],
        rain_forecast_7d_mm=summary["rain_forecast_7d_mm"],
        wind_ms=summary["wind_ms"],
        et0_mm=summary["et0_mm"],
        solar_wm2=summary["solar_wm2"],
        source=source,
        payload=summary,
    )
    db.add(row)
    db.commit()
    return {**summary, "cached": False, "source": source, "raw_keys": list(payload)[:8]}

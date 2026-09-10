from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from krishiayan.models.entities import SensorReading


@dataclass
class AnomalyResult:
    score: float
    is_anomaly: bool
    reasons: list[str]


def score_reading(
    *,
    moisture: float | None,
    temp: float | None,
    ec: float | None,
    ph: float | None,
    battery: float | None,
    device_id: str,
    db: Session | None = None,
) -> AnomalyResult:
    reasons: list[str] = []
    score = 0.0

    def flag(cond: bool, reason: str, w: float) -> None:
        nonlocal score
        if cond:
            reasons.append(reason)
            score += w

    flag(moisture is not None and not (0 <= moisture <= 80), "moisture_out_of_range", 0.4)
    flag(temp is not None and not (-5 <= temp <= 55), "temperature_out_of_range", 0.3)
    flag(ec is not None and not (0 <= ec <= 20), "ec_out_of_range", 0.3)
    flag(ph is not None and not (3.5 <= ph <= 10.5), "ph_out_of_range", 0.3)
    flag(battery is not None and battery < 3.2, "battery_low", 0.15)

    if db is not None and moisture is not None:
        prev = (
            db.query(SensorReading)
            .filter(SensorReading.device_id == device_id, SensorReading.soil_moisture.is_not(None))
            .order_by(SensorReading.captured_at.desc())
            .limit(8)
            .all()
        )
        if prev:
            last = prev[0].soil_moisture
            if last is not None and abs(moisture - last) > 35:
                reasons.append("moisture_jump")
                score += 0.25

    score = min(1.0, score)
    return AnomalyResult(score=score, is_anomaly=score >= 0.4, reasons=reasons)

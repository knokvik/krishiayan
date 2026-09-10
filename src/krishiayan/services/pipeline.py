from __future__ import annotations

from sqlalchemy.orm import Session

from krishiayan.agronomy.recommend import build_recommendations
from krishiayan.ml.infer import load_registry, predict_scan
from krishiayan.models.entities import Crop, Device, Field, ProcessedScan, Recommendation, SensorReading
from krishiayan.schemas.ingest import ProbePacket
from krishiayan.services.features import build_features
from krishiayan.services.ingest import ingest_packet
from krishiayan.services.weather import weather_for_field


def process_reading(db: Session, reading: SensorReading, language: str = "en") -> tuple[ProcessedScan, list[Recommendation]]:
    packet = ProbePacket.model_validate(reading.payload)
    feats = build_features(packet)
    field = db.get(Field, reading.field_id) if reading.field_id else None
    weather = {}
    crop = None
    if field is not None:
        try:
            weather = weather_for_field(db, field)
        except Exception:
            weather = {"et0_mm": 5.0, "rain_forecast_7d_mm": 0.0, "rain_next_48h_mm": 0.0, "temp_c": feats.temp_c}
        crop = field.crop or (db.get(Crop, field.crop_id) if field.crop_id else None)

    nutrients = predict_scan(feats, weather=weather, registry=load_registry())
    scan = ProcessedScan(
        reading_id=reading.id,
        field_id=reading.field_id,
        model_version=nutrients.get("model_version", "unfitted"),
        n_mgkg=nutrients.get("n_mgkg"),
        p_mgkg=nutrients.get("p_mgkg"),
        k_mgkg=nutrients.get("k_mgkg"),
        ph=nutrients.get("ph"),
        ec_dsm=feats.ec_dsm,
        moisture_pct=feats.moisture_pct,
        temp_c=feats.temp_c,
        soc_pct=nutrients.get("soc_pct"),
        texture=feats.texture,
        n_lo=nutrients.get("n_lo"),
        n_hi=nutrients.get("n_hi"),
        p_lo=nutrients.get("p_lo"),
        p_hi=nutrients.get("p_hi"),
        k_lo=nutrients.get("k_lo"),
        k_hi=nutrients.get("k_hi"),
        confidence=nutrients.get("confidence", "medium"),
        features={**feats.as_dict(), "weather": weather, "stress": nutrients.get("stress")},
    )
    db.add(scan)
    db.flush()

    recs: list[Recommendation] = []
    if crop is not None and field is not None:
        cards = build_recommendations(
            nutrients=nutrients,
            feats=feats,
            crop_spec=crop.spec,
            crop_code=crop.code,
            weather=weather,
            sowing=field.sowing_date,
            area_ha=field.area_ha,
            language=language,
            stress=nutrients.get("stress") or "healthy",
        )
        crop_payload = next((c["payload"] for c in cards if c["kind"] == "crop"), {})
        scan.soil_health = crop_payload.get("soil_health")
        scan.water_stress = crop_payload.get("water_stress")
        for card in cards:
            rec = Recommendation(
                field_id=field.id,
                scan_id=scan.id,
                kind=card["kind"],
                priority=card["priority"],
                title=card["title"],
                body=card["body"],
                payload=card["payload"],
                language=language,
            )
            db.add(rec)
            recs.append(rec)
    db.commit()
    db.refresh(scan)
    return scan, recs


def ingest_and_process(db: Session, packet: ProbePacket, language: str = "en") -> dict:
    reading = ingest_packet(db, packet)
    scan, recs = process_reading(db, reading, language=language)
    return {
        "reading_id": reading.id,
        "scan_id": scan.id,
        "is_anomaly": reading.is_anomaly,
        "metrics": {
            "n_mgkg": scan.n_mgkg,
            "p_mgkg": scan.p_mgkg,
            "k_mgkg": scan.k_mgkg,
            "ph": scan.ph,
            "ec_dsm": scan.ec_dsm,
            "moisture_pct": scan.moisture_pct,
            "temp_c": scan.temp_c,
            "soc_pct": scan.soc_pct,
            "texture": scan.texture,
            "soil_health": scan.soil_health,
            "confidence": scan.confidence,
            "n_interval": [scan.n_lo, scan.n_hi],
            "model_version": scan.model_version,
        },
        "recommendations": [
            {"id": r.id, "kind": r.kind, "priority": r.priority, "title": r.title, "payload": r.payload} for r in recs
        ],
        "tool": _tool_insight(db, packet.device_id, reading),
    }


def _tool_insight(db: Session, hardware_id: str, reading: SensorReading) -> dict:
    device = db.query(Device).filter(Device.hardware_id == hardware_id).first()
    optical = (reading.payload or {}).get("layers") or []
    snr_bad = False
    if optical:
        layer0 = optical[0]
        raw = (layer0.get("optical_660") or 0)
        ok = (layer0.get("extraction") or {}).get("filtrate_ok", True)
        snr_bad = (not ok) or raw < 0.005
    batt = reading.battery_level
    weeks = None
    if batt is not None:
        weeks = round(max(0.0, (batt - 3.3) / 0.12), 1)
    return {
        "hardware_id": hardware_id,
        "battery_v": batt,
        "battery_weeks_est": weeks,
        "last_seen": reading.captured_at.isoformat() if reading.captured_at else None,
        "firmware": device.firmware_version if device else None,
        "probe_tip_dirty": snr_bad,
        "anomaly": reading.is_anomaly,
        "anomaly_score": reading.anomaly_score,
    }

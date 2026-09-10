from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.orm import Session

from krishiayan.models.entities import Device, Field, SensorReading
from krishiayan.schemas.ingest import ProbePacket
from krishiayan.services.anomaly import score_reading
from krishiayan.services.features import build_features


def ingest_packet(db: Session, packet: ProbePacket) -> SensorReading:
    captured = packet.captured_at or datetime.now(UTC)
    if captured.tzinfo is None:
        captured = captured.replace(tzinfo=UTC)
    scan_id = packet.scan_id or uuid4().hex
    field_id = packet.field_id or packet.plot_id
    device = db.query(Device).filter(Device.hardware_id == packet.device_id).first()
    if device is not None:
        if field_id is None:
            field_id = device.field_id
        device.last_seen = captured
        device.battery_v = packet.battery_v or packet.battery_level
        device.firmware_version = packet.firmware_version or device.firmware_version
    elif field_id:
        field = db.get(Field, field_id)
        if field is not None:
            device = Device(
                hardware_id=packet.device_id,
                field_id=field_id,
                firmware_version=packet.firmware_version,
                last_seen=captured,
                battery_v=packet.battery_v or packet.battery_level,
            )
            db.add(device)

    feats = build_features(packet)
    battery = packet.battery_v if packet.battery_v is not None else packet.battery_level
    anom = score_reading(
        moisture=feats.moisture_pct,
        temp=feats.temp_c,
        ec=feats.ec_dsm,
        ph=feats.ph,
        battery=battery,
        device_id=packet.device_id,
        db=db,
    )
    gps = packet.gps
    reading = SensorReading(
        device_id=packet.device_id,
        field_id=field_id,
        scan_id=scan_id,
        captured_at=captured,
        payload=packet.model_dump(mode="json"),
        soil_moisture=feats.moisture_pct,
        soil_temperature=feats.temp_c,
        electrical_conductivity=feats.ec_dsm,
        ph=feats.ph,
        soc_proxy=feats.soc_proxy if feats.soc_proxy is not None else feats.nir_index,
        battery_level=battery,
        lat=gps.lat if gps else None,
        lon=gps.lon if gps else None,
        anomaly_score=anom.score,
        is_anomaly=anom.is_anomaly,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    reading._features = feats  # type: ignore[attr-defined]
    reading._anomaly_reasons = anom.reasons  # type: ignore[attr-defined]
    return reading

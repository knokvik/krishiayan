from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from krishiayan.core.db import get_db
from krishiayan.schemas.ingest import ProbePacket
from krishiayan.services.ingest import ingest_packet

router = APIRouter(prefix="/v1/ingest", tags=["ingest"])


def _to_out(reading) -> dict:
    return {
        "id": reading.id,
        "scan_id": reading.scan_id,
        "device_id": reading.device_id,
        "field_id": reading.field_id,
        "captured_at": reading.captured_at.isoformat() if reading.captured_at else None,
        "soil_moisture": reading.soil_moisture,
        "soil_temperature": reading.soil_temperature,
        "electrical_conductivity": reading.electrical_conductivity,
        "ph": reading.ph,
        "soc_proxy": reading.soc_proxy,
        "anomaly_score": reading.anomaly_score,
        "is_anomaly": reading.is_anomaly,
        "features": getattr(reading, "_features", None).as_dict()
        if getattr(reading, "_features", None)
        else None,
        "anomaly_reasons": getattr(reading, "_anomaly_reasons", []),
    }


@router.post("/scan")
def ingest_scan(packet: ProbePacket, db: Session = Depends(get_db)) -> dict:
    try:
        reading = ingest_packet(db, packet)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_out(reading)


@router.post("/batch")
def ingest_batch(packets: list[ProbePacket], db: Session = Depends(get_db)) -> dict:
    out = []
    for p in packets:
        out.append(_to_out(ingest_packet(db, p)))
    return {"count": len(out), "readings": out}


@router.post("/file")
async def ingest_file(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    import json

    raw = await file.read()
    data = json.loads(raw)
    if isinstance(data, dict):
        data = [data]
    packets = [ProbePacket.model_validate(x) for x in data]
    return ingest_batch(packets, db)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from krishiayan.api.deps import get_current_user
from krishiayan.api.routes.farms import _owned_field
from krishiayan.core.db import get_db
from krishiayan.models.entities import Device, ProcessedScan, Recommendation, SensorReading, User
from krishiayan.schemas.ingest import ProbePacket
from krishiayan.services.pipeline import ingest_and_process
from krishiayan.sim.probe import packet_from_truth
from krishiayan.sim.world import sample_world

router = APIRouter(prefix="/v1", tags=["dashboard"])


@router.post("/pipeline/scan")
def pipeline_scan(packet: ProbePacket, db: Session = Depends(get_db), process: bool = True) -> dict:
    if not process:
        from krishiayan.services.ingest import ingest_packet

        reading = ingest_packet(db, packet)
        return {"reading_id": reading.id, "scan_id": reading.scan_id, "processed": False}
    return ingest_and_process(db, packet)


@router.post("/simulate")
def simulate(
    scenario: str = "pune-wheat-n-deficient",
    field_id: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    if field_id:
        field = _owned_field(db, user, field_id)
        field_id = field.id
    import numpy as np

    rng = np.random.default_rng(7)
    truth = sample_world(rng, scenario=scenario)
    pkt = packet_from_truth(truth, rng, field_id=field_id)
    out = ingest_and_process(db, pkt, language=user.language)
    out["sim"] = True
    out["planted"] = {"crop": truth.crop, "n": truth.root().n, "p": truth.root().p, "k": truth.root().k}
    return out


@router.get("/fields/{field_id}/latest")
def latest(field_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _owned_field(db, user, field_id)
    scan = (
        db.query(ProcessedScan)
        .filter(ProcessedScan.field_id == field_id)
        .order_by(ProcessedScan.created_at.desc())
        .first()
    )
    if scan is None:
        raise HTTPException(status_code=404, detail="No scans yet")
    recs = (
        db.query(Recommendation)
        .filter(Recommendation.scan_id == scan.id)
        .order_by(Recommendation.priority)
        .all()
    )
    return {
        "scan": {
            "id": scan.id,
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
            "n_lo": scan.n_lo,
            "n_hi": scan.n_hi,
            "model_version": scan.model_version,
            "created_at": scan.created_at.isoformat() if scan.created_at else None,
        },
        "recommendations": [
            {"id": r.id, "kind": r.kind, "priority": r.priority, "title": r.title, "body": r.body, "payload": r.payload}
            for r in recs
        ],
        "next_action": recs[0].title if recs else None,
    }


@router.get("/fields/{field_id}/history")
def history(field_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    _owned_field(db, user, field_id)
    scans = (
        db.query(ProcessedScan)
        .filter(ProcessedScan.field_id == field_id)
        .order_by(ProcessedScan.created_at.asc())
        .limit(90)
        .all()
    )
    return {
        "points": [
            {
                "t": s.created_at.isoformat() if s.created_at else None,
                "n": s.n_mgkg,
                "p": s.p_mgkg,
                "k": s.k_mgkg,
                "moisture": s.moisture_pct,
                "soc": s.soc_pct,
                "health": s.soil_health,
            }
            for s in scans
        ]
    }


@router.get("/fields/{field_id}/recommendations")
def recs(field_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[dict]:
    _owned_field(db, user, field_id)
    rows = (
        db.query(Recommendation)
        .filter(Recommendation.field_id == field_id)
        .order_by(Recommendation.created_at.desc())
        .limit(50)
        .all()
    )
    return [
        {"id": r.id, "kind": r.kind, "priority": r.priority, "title": r.title, "payload": r.payload, "created_at": str(r.created_at)}
        for r in rows
    ]


@router.get("/devices/{hardware_id}/health")
def device_health(hardware_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    device = db.query(Device).filter(Device.hardware_id == hardware_id).first()
    if device is None:
        raise HTTPException(status_code=404, detail="Unknown device")
    last = (
        db.query(SensorReading)
        .filter(SensorReading.device_id == hardware_id)
        .order_by(SensorReading.captured_at.desc())
        .first()
    )
    return {
        "hardware_id": hardware_id,
        "field_id": device.field_id,
        "firmware": device.firmware_version,
        "battery_v": device.battery_v,
        "last_seen": device.last_seen.isoformat() if device.last_seen else None,
        "last_anomaly": last.is_anomaly if last else None,
    }

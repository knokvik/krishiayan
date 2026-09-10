#!/usr/bin/env python3
"""Seed a demo farmer, farm, field, device, and one simulated scan."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from krishiayan.core.db import SessionLocal, init_db  # noqa: E402
from krishiayan.core.security import hash_password  # noqa: E402
from krishiayan.models.entities import Crop, Device, Farm, Field, User  # noqa: E402
from krishiayan.schemas.ingest import ProbePacket  # noqa: E402
from krishiayan.services.crops import seed_crops  # noqa: E402
from krishiayan.services.pipeline import ingest_and_process  # noqa: E402
from krishiayan.sim.probe import packet_from_truth  # noqa: E402
from krishiayan.sim.world import sample_world  # noqa: E402
import numpy as np  # noqa: E402


def main() -> None:
    init_db()
    db = SessionLocal()
    seed_crops(db)
    user = db.query(User).filter(User.email == "farmer@example.com").first()
    if user is None:
        user = User(
            email="farmer@example.com",
            hashed_password=hash_password("soilguide"),
            full_name="Demo Farmer",
            language="en",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    farm = db.query(Farm).filter(Farm.owner_id == user.id).first()
    if farm is None:
        farm = Farm(owner_id=user.id, name="Alandi demo farm", village="Alandi")
        db.add(farm)
        db.commit()
        db.refresh(farm)
    wheat = db.query(Crop).filter(Crop.code == "wheat").first()
    field = db.query(Field).filter(Field.farm_id == farm.id).first()
    if field is None:
        field = Field(
            farm_id=farm.id,
            name="Wheat plot",
            area_ha=1.0,
            soil_class="black_cotton",
            crop_id=wheat.id if wheat else None,
            lat=farm.lat,
            lon=farm.lon,
        )
        db.add(field)
        db.commit()
        db.refresh(field)
    if db.query(Device).filter(Device.hardware_id == "KA-PROBE-0001").first() is None:
        db.add(Device(hardware_id="KA-PROBE-0001", field_id=field.id, firmware_version="0.3.2"))
        db.commit()
    rng = np.random.default_rng(7)
    truth = sample_world(rng, scenario="pune-wheat-n-deficient")
    pkt = packet_from_truth(truth, rng, device_id="KA-PROBE-0001", field_id=field.id)
    out = ingest_and_process(db, ProbePacket.model_validate(pkt.model_dump()), language="en")
    print("seeded farmer@example.com / soilguide")
    print("field", field.id, "next", out["recommendations"][0]["title"] if out["recommendations"] else None)


if __name__ == "__main__":
    main()

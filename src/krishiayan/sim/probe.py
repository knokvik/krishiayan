from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import numpy as np

from krishiayan.schemas.ingest import Gps, Layer, ProbePacket
from krishiayan.services.calibrate import factory_cal
from krishiayan.services.correct import moisture_correction_gain
from krishiayan.sim.world import SOIL_CLASSES, SoilTruth


def _adc(physical: float, name: str, rng: np.random.Generator) -> float:
    spec = factory_cal()[name]
    if name == "moisture":
        raw = physical * spec["scale"] + spec["offset"]
    else:
        raw = physical / spec["scale"] + spec["offset"]
    return float(raw + rng.normal(0, 8))


def _rgb_for(value: float, lo: float, hi: float, rng: np.random.Generator) -> list[int]:
    t = float(np.clip((value - lo) / (hi - lo), 0, 1))
    g = int(40 + 180 * t + rng.normal(0, 6))
    r = int(30 + 40 * (1 - t) + rng.normal(0, 5))
    b = int(20 + 30 * (1 - t) + rng.normal(0, 5))
    return [int(np.clip(r, 0, 255)), int(np.clip(g, 0, 255)), int(np.clip(b, 0, 255))]


def packet_from_truth(
    truth: SoilTruth,
    rng: np.random.Generator,
    device_id: str = "KA-PROBE-SIM",
    field_id: str | None = None,
) -> ProbePacket:
    eis0 = SOIL_CLASSES[truth.soil_class]["eis"]
    layers: list[Layer] = []
    for L in truth.layers:
        gain = moisture_correction_gain(L.moisture)
        # True optical tracks SOC; hardware collapses it in wet soil.
        true_660 = 0.08 + 0.22 * L.soc + 0.00025 * L.n
        collapsed = true_660 / gain * float(rng.uniform(0.94, 1.06))
        nir = {
            "nm_1700": float(0.05 + 0.18 * L.soc + rng.normal(0, 0.01)),
            "nm_1940": float(0.04 + 0.12 * L.soc + 0.002 * L.moisture / 10 + rng.normal(0, 0.01)),
            "nm_2100": float(0.03 + 0.16 * L.soc + rng.normal(0, 0.01)),
            "nm_2300": float(0.02 + 0.10 * L.soc + rng.normal(0, 0.008)),
        }
        eis = [float(np.clip(eis0 + rng.normal(0, 0.04), 0.05, 1.2)) for _ in range(6)]
        layers.append(
            Layer(
                depth_cm=L.depth_cm,
                moisture_raw=_adc(L.moisture, "moisture", rng),
                temp_raw=L.temp + float(rng.normal(0, 0.15)),
                ec_raw=L.ec + float(rng.normal(0, 0.03)),
                eis_real=eis,
                optical_660=float(max(0.01, collapsed)),
                optical_nir=nir,
                colorimetric_rgb={
                    "n": _rgb_for(L.n, 80, 420, rng),
                    "p": _rgb_for(L.p, 5, 40, rng),
                    "k": _rgb_for(L.k, 80, 320, rng),
                },
                extraction={"turbidity_660": float(max(0.01, collapsed)), "filtrate_ok": True},
                ph=float(L.ph + rng.normal(0, 0.08)),
                soc_proxy=float(L.soc + rng.normal(0, 0.05)),
            )
        )
    return ProbePacket(
        schema_version="1.0.0",
        device_id=device_id,
        firmware_version="0.3.2-sim",
        scan_id=uuid4().hex,
        captured_at=datetime.now(UTC),
        gps=Gps(lat=18.5204 + float(rng.normal(0, 0.01)), lon=73.8567 + float(rng.normal(0, 0.01))),
        field_id=field_id,
        battery_v=float(rng.uniform(3.6, 4.15)),
        flags={"extraction_ran": True, "sim": True},
        layers=layers,
    )

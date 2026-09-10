from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from krishiayan.core.config import ROOT

CAL_PATH = ROOT / "data" / "fixtures" / "factory_cal.json"


@lru_cache
def factory_cal() -> dict:
    return json.loads(CAL_PATH.read_text())


def _curve(raw: float | None, name: str) -> float | None:
    if raw is None:
        return None
    spec = factory_cal()[name]
    # If the probe already sent physical units, keep them.
    if raw <= spec.get("physical_max", 80) and name == "moisture":
        return float(max(0.0, min(80.0, raw)))
    if name == "temperature" and -10 <= raw <= 60:
        return float(raw)
    if name == "ec" and 0 <= raw <= 20:
        return float(raw)
    value = (raw - spec["offset"]) * spec["scale"] if name != "moisture" else (raw - spec["offset"]) / spec["scale"]
    if name == "moisture":
        return float(max(0.0, min(80.0, value)))
    if name == "temperature":
        return float(max(-5.0, min(55.0, value)))
    if name == "ec":
        return float(max(0.0, min(20.0, value)))
    return float(value)


def moisture_pct(raw: float | None, already: float | None = None) -> float | None:
    if already is not None:
        return float(max(0.0, min(80.0, already)))
    return _curve(raw, "moisture")


def temp_c(raw: float | None, already: float | None = None) -> float | None:
    if already is not None:
        return float(already)
    return _curve(raw, "temperature")


def ec_dsm(raw: float | None, already: float | None = None) -> float | None:
    if already is not None:
        return float(max(0.0, already))
    return _curve(raw, "ec")


def density_factor(texture: str) -> float:
    return float(factory_cal()["density_by_texture"].get(texture, 1.0))

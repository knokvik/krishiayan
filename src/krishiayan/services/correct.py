"""Moisture-adaptive optical correction — the Krishiayan IP.

Traditional 2-propanol + NaCl turbidity collapses above ~30% moisture
(~33% recovery). The probe measures moisture in situ and restores the
optical channel before ML sees it.

    corrected = raw * (1 + 0.035 m + 0.012 m²) * density_factor
"""

from __future__ import annotations

from krishiayan.services.calibrate import density_factor


def moisture_correction_gain(moisture_pct: float) -> float:
    m = max(0.0, float(moisture_pct))
    return 1.0 + 0.035 * m + 0.012 * (m**2)


def correct_optical(raw: float | None, moisture_pct: float, texture: str = "loam") -> float | None:
    if raw is None:
        return None
    return float(raw) * moisture_correction_gain(moisture_pct) * density_factor(texture)


def texture_from_eis(eis_real: list[float], moisture_pct: float | None = None) -> str:
    """Cheap texture proxy from EIS magnitude. Clay holds more low-frequency impedance."""
    if not eis_real:
        return "loam"
    mag = sum(abs(x) for x in eis_real) / len(eis_real)
    if mag > 0.85:
        return "clay"
    if mag > 0.65:
        return "black_cotton"
    if mag < 0.28:
        return "sand"
    if mag < 0.42:
        return "sandy_loam"
    return "loam"


def nir_organics_index(optical_nir: dict[str, float], corrected_660: float | None) -> float:
    """Weighted C-H / organics index from 1700–2300 nm plus turbidity."""
    if not optical_nir:
        return float(corrected_660 or 0.0)
    keys = sorted(optical_nir)
    vals = [optical_nir[k] for k in keys]
    base = sum(vals) / max(1, len(vals))
    if corrected_660 is not None:
        return 0.6 * base + 0.4 * corrected_660
    return base

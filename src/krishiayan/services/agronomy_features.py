"""Derived agronomic indices from soil + weather + crop stage."""

from __future__ import annotations

from datetime import UTC, datetime


def growing_degree_days(sowing: datetime | None, mean_temp: float, base_temp: float, today: datetime | None = None) -> float:
    if sowing is None:
        return 0.0
    today = today or datetime.now(UTC)
    if sowing.tzinfo is None:
        sowing = sowing.replace(tzinfo=UTC)
    days = max(0, (today - sowing).days)
    return float(max(0.0, mean_temp - base_temp) * days)


def moisture_deficit(moisture_pct: float, lo: float, hi: float) -> float:
    """0 = in band, positive = too dry, negative = too wet."""
    if moisture_pct < lo:
        return lo - moisture_pct
    if moisture_pct > hi:
        return hi - moisture_pct
    return 0.0


def water_stress_index(moisture_pct: float, lo: float, hi: float, et0_mm: float, rain_48h: float) -> float:
    """0 = none, 1 = severe. Rain in next 48h reduces stress; high ET0 raises it."""
    if moisture_pct > hi:
        return float(min(1.0, (moisture_pct - hi) / 20.0))  # waterlogging encoded as >0 with flag elsewhere
    deficit = max(0.0, lo - moisture_pct)
    raw = deficit / max(lo, 1.0)
    raw += max(0.0, et0_mm - 4.0) / 10.0
    raw -= min(0.4, rain_48h / 40.0)
    return float(min(1.0, max(0.0, raw)))


def nutrient_index(n: float, p: float, k: float, crit: dict) -> dict:
    def ratio(val: float, c: float) -> float:
        return float(min(1.5, val / max(c, 1e-6)))

    return {
        "n": ratio(n, crit["n"]),
        "p": ratio(p, crit["p"]),
        "k": ratio(k, crit["k"]),
    }


def soil_health_score(
    *,
    moisture_pct: float,
    ph: float,
    ec: float,
    soc: float,
    n_idx: float,
    p_idx: float,
    k_idx: float,
) -> float:
    """0–100 composite. Honest, not a lab certificate."""
    ph_score = 1.0 - min(1.0, abs(ph - 6.7) / 2.5)
    moist_score = 1.0 - min(1.0, abs(moisture_pct - 24) / 24)
    salt_score = 1.0 - min(1.0, max(0.0, ec - 1.5) / 4.0)
    soc_score = min(1.0, soc / 1.2)
    nut = (min(1.0, n_idx) + min(1.0, p_idx) + min(1.0, k_idx)) / 3
    score = 100 * (0.15 * ph_score + 0.15 * moist_score + 0.15 * salt_score + 0.25 * soc_score + 0.30 * nut)
    return float(round(score, 1))

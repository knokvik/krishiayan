from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

SOIL_CLASSES = {
    "black_cotton": {"eis": 0.72, "soc": 0.9, "ph": 7.4, "ec": 0.7},
    "laterite": {"eis": 0.48, "soc": 0.55, "ph": 5.8, "ec": 0.4},
    "alluvial": {"eis": 0.40, "soc": 0.70, "ph": 7.0, "ec": 0.5},
    "sandy_loam": {"eis": 0.32, "soc": 0.40, "ph": 6.6, "ec": 0.35},
    "clay": {"eis": 0.88, "soc": 1.1, "ph": 7.2, "ec": 0.8},
    "saline": {"eis": 0.60, "soc": 0.50, "ph": 8.1, "ec": 3.2},
}

DEPTHS = (8.0, 25.0, 50.0, 80.0)
CROPS = ["wheat", "rice", "maize", "soybean", "cotton", "onion", "tomato", "tur"]


@dataclass
class LayerTruth:
    depth_cm: float
    n: float
    p: float
    k: float
    ph: float
    soc: float
    moisture: float
    temp: float
    ec: float


@dataclass
class SoilTruth:
    soil_class: str
    crop: str
    stage_day: int
    rain_7d_mm: float
    et0_mm: float
    layers: list[LayerTruth] = field(default_factory=list)
    plot_id: str = "sim"

    def root(self) -> LayerTruth:
        for L in self.layers:
            if 15 <= L.depth_cm <= 45:
                return L
        return self.layers[1] if len(self.layers) > 1 else self.layers[0]


def sample_world(rng: np.random.Generator, scenario: str | None = None) -> SoilTruth:
    soil = rng.choice(list(SOIL_CLASSES))
    crop = rng.choice(CROPS)
    base = SOIL_CLASSES[soil]
    n0 = float(rng.uniform(80, 420))
    p0 = float(rng.uniform(5, 40))
    k0 = float(rng.uniform(80, 320))
    moisture0 = float(rng.uniform(8, 48))
    temp0 = float(rng.uniform(18, 38))
    rain = float(rng.uniform(0, 80))
    et0 = float(rng.uniform(2, 7))

    if scenario == "pune-wheat-n-deficient":
        soil, crop = "black_cotton", "wheat"
        n0, p0, k0 = 110.0, 18.0, 180.0
        moisture0, temp0, rain, et0 = 16.0, 28.0, 2.0, 5.5
        base = SOIL_CLASSES[soil]
    elif scenario == "wet-soil":
        moisture0 = 38.0
        rain = 55.0
    elif scenario == "saline":
        soil = "saline"
        base = SOIL_CLASSES[soil]
        k0, moisture0 = 220.0, 22.0

    layers = []
    for i, d in enumerate(DEPTHS):
        # N mobile — declines with depth; P stratified near surface; K deeper
        n = n0 * (1.0 - 0.12 * i) * float(rng.uniform(0.92, 1.08))
        p = p0 * (1.0 - 0.18 * i) * float(rng.uniform(0.92, 1.08))
        k = k0 * (1.0 + 0.06 * i) * float(rng.uniform(0.92, 1.08))
        layers.append(
            LayerTruth(
                depth_cm=d,
                n=max(40.0, n),
                p=max(3.0, p),
                k=max(50.0, k),
                ph=float(np.clip(base["ph"] + rng.normal(0, 0.15), 4.8, 9.0)),
                soc=float(max(0.2, base["soc"] * (1.0 - 0.08 * i) * rng.uniform(0.9, 1.1))),
                moisture=float(np.clip(moisture0 + i * 2.0 + rng.normal(0, 1.5), 5, 55)),
                temp=float(temp0 - 0.4 * i + rng.normal(0, 0.4)),
                ec=float(max(0.1, base["ec"] * rng.uniform(0.85, 1.15))),
            )
        )
    return SoilTruth(
        soil_class=soil,
        crop=crop,
        stage_day=int(rng.integers(5, 80)),
        rain_7d_mm=rain,
        et0_mm=et0,
        layers=layers,
    )

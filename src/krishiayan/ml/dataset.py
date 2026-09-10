from __future__ import annotations

import numpy as np
import pandas as pd

from krishiayan.ml.columns import FEATURE_COLS
from krishiayan.services.features import build_features
from krishiayan.sim.probe import packet_from_truth
from krishiayan.sim.world import sample_world


def stress_label(truth) -> str:
    root = truth.root()
    if root.ec >= 2.4:
        return "salinity"
    if root.moisture >= 46:
        return "waterlogging"
    if root.moisture <= 12:
        return "water_stress"
    if root.temp >= 36:
        return "heat"
    if root.n < 160:
        return "n_stress"
    if root.p < 10:
        return "p_stress"
    if root.k < 110:
        return "k_stress"
    return "healthy"


def yield_index(truth) -> float:
    root = truth.root()
    n = min(1.0, root.n / 250)
    p = min(1.0, root.p / 18)
    k = min(1.0, root.k / 160)
    water = 1.0 - min(1.0, abs(root.moisture - 24) / 24)
    salt = 1.0 - min(1.0, max(0.0, root.ec - 1.5) / 4)
    return float(np.clip(0.35 * n + 0.2 * p + 0.2 * k + 0.15 * water + 0.10 * salt, 0, 1))


def make_dataframe(n: int = 2400, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        scenario = None
        if i % 17 == 0:
            scenario = "wet-soil"
        elif i % 19 == 0:
            scenario = "pune-wheat-n-deficient"
        elif i % 23 == 0:
            scenario = "saline"
        truth = sample_world(rng, scenario=scenario)
        pkt = packet_from_truth(truth, rng, device_id=f"KA-SIM-{i % 40:03d}")
        feats = build_features(pkt)
        row = feats.model_row()
        row["rain_7d_mm"] = truth.rain_7d_mm
        row["et0_mm"] = truth.et0_mm
        root = truth.root()
        row["n_mgkg"] = root.n
        row["p_mgkg"] = root.p
        row["k_mgkg"] = root.k
        row["soc_pct"] = root.soc
        row["ph_hat"] = root.ph
        row["yield_index"] = yield_index(truth)
        row["stress"] = stress_label(truth)
        row["optical_660_raw"] = feats.optical_660_raw
        row["plot_id"] = f"plot-{i}"
        row["soil_class"] = truth.soil_class
        row["crop"] = truth.crop
        row["wet"] = float(root.moisture > 30)
        rows.append(row)
    df = pd.DataFrame(rows)
    for c in FEATURE_COLS:
        if c not in df:
            df[c] = 0.0
    return df

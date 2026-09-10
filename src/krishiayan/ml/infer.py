from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from krishiayan.core.config import get_settings
from krishiayan.ml.columns import FEATURE_COLS
from krishiayan.services.features import ScanFeatures


class ModelRegistry:
    def __init__(self, path: Path | None = None):
        settings = get_settings()
        self.path = path or (settings.model_path / "bundle.joblib")
        self.bundle = None
        if self.path.exists():
            self.bundle = joblib.load(self.path)

    @property
    def ready(self) -> bool:
        return self.bundle is not None

    @property
    def version(self) -> str:
        if not self.ready:
            return "unfitted"
        return "xgb-v1"


def _confidence(width: float, typical: float) -> str:
    rel = width / max(typical, 1e-6)
    if rel < 0.25:
        return "high"
    if rel < 0.5:
        return "medium"
    return "low"


@lru_cache
def load_registry() -> ModelRegistry:
    return ModelRegistry()


def predict_scan(feats: ScanFeatures, weather: dict | None = None, registry: ModelRegistry | None = None) -> dict:
    registry = registry or load_registry()
    weather = weather or {}
    row = feats.model_row()
    row["rain_7d_mm"] = float(weather.get("rain_forecast_7d_mm") or weather.get("rain_7d_mm") or 0)
    row["et0_mm"] = float(weather.get("et0_mm") or 4.0)
    X = pd.DataFrame([row], columns=FEATURE_COLS).fillna(0)

    if not registry.ready:
        # Honest fallback: colorimetric/EC heuristics, wide intervals.
        n = 80 + 450 * row["color_n"]
        p = 4 + 45 * row["color_p"]
        k = 70 + 280 * row["color_k"]
        soc = max(0.2, 0.4 + 1.6 * row["nir_index"])
        return {
            "n_mgkg": n,
            "p_mgkg": p,
            "k_mgkg": k,
            "soc_pct": soc,
            "ph": feats.ph or 6.8,
            "n_lo": n * 0.6,
            "n_hi": n * 1.4,
            "p_lo": p * 0.6,
            "p_hi": p * 1.4,
            "k_lo": k * 0.6,
            "k_hi": k * 1.4,
            "yield_index": 0.5,
            "stress": "unknown",
            "stress_proba": {},
            "confidence": "low",
            "model_version": "heuristic-fallback",
        }

    out: dict = {"model_version": registry.version, "stress_proba": {}}
    heads = registry.bundle["heads"]
    typical = {"n_mgkg": 250, "p_mgkg": 18, "k_mgkg": 160, "soc_pct": 0.8, "ph_hat": 6.8, "yield_index": 0.6}
    confs = []
    for name, spec in heads.items():
        model = spec["model"]
        if spec["kind"] == "classifier":
            proba = model.predict_proba(X)[0]
            le = spec.get("label_encoder")
            classes = list(le.classes_) if le is not None else list(spec.get("classes") or [])
            idx = int(np.argmax(proba))
            out["stress"] = str(classes[idx] if classes else idx)
            out["stress_proba"] = {str(c): round(float(p), 4) for c, p in zip(classes, proba, strict=False)}
            continue
        pred = float(model.predict(X)[0])
        q = float(spec.get("q90") or 0)
        key = "ph" if name == "ph_hat" else name
        out[key] = pred
        out[f"{key}_lo" if key != "ph" else "ph_lo"] = pred - q
        out[f"{key}_hi" if key != "ph" else "ph_hi"] = pred + q
        confs.append(_confidence(2 * q, typical.get(name, abs(pred) or 1)))
    # normalize names
    if "n_mgkg" in out:
        out["n_lo"] = out.get("n_mgkg_lo", out["n_mgkg"] - 20)
        out["n_hi"] = out.get("n_mgkg_hi", out["n_mgkg"] + 20)
        out["p_lo"] = out.get("p_mgkg_lo", out["p_mgkg"] - 3)
        out["p_hi"] = out.get("p_mgkg_hi", out["p_mgkg"] + 3)
        out["k_lo"] = out.get("k_mgkg_lo", out["k_mgkg"] - 20)
        out["k_hi"] = out.get("k_mgkg_hi", out["k_mgkg"] + 20)
    out["confidence"] = min(confs, key=["high", "medium", "low"].index) if confs else "medium"
    out["ph"] = out.get("ph", feats.ph or 6.8)
    return out

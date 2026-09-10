from pathlib import Path

import numpy as np

from krishiayan.ml.dataset import make_dataframe
from krishiayan.ml.infer import ModelRegistry, predict_scan
from krishiayan.services.features import build_features
from krishiayan.sim.probe import packet_from_truth
from krishiayan.sim.world import sample_world

BUNDLE = Path("models/artifacts/bundle.joblib")


def test_dataset_has_required_columns():
    df = make_dataframe(n=40, seed=1)
    assert len(df) == 40
    assert df["n_mgkg"].between(40, 500).all()
    assert set(df["stress"]).issubset(
        {"healthy", "water_stress", "n_stress", "p_stress", "k_stress", "salinity", "heat", "waterlogging"}
    )


def test_trained_bundle_predicts_low_n_scenario():
    if not BUNDLE.exists():
        import ml.train as T

        T.train(n_samples=600)
    rng = np.random.default_rng(3)
    truth = sample_world(rng, scenario="pune-wheat-n-deficient")
    pkt = packet_from_truth(truth, rng)
    feats = build_features(pkt)
    reg = ModelRegistry(BUNDLE)
    out = predict_scan(feats, weather={"rain_forecast_7d_mm": 2, "et0_mm": 5.5}, registry=reg)
    assert out["n_mgkg"] < 220
    assert out["n_lo"] < out["n_mgkg"] < out["n_hi"]
    assert out["model_version"] != "unfitted"

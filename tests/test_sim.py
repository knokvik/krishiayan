import numpy as np

from krishiayan.services.features import build_features
from krishiayan.sim.probe import packet_from_truth
from krishiayan.sim.world import sample_world


def test_wet_soil_raw_is_collapsed_then_features_restore():
    rng = np.random.default_rng(0)
    truth = sample_world(rng, scenario="wet-soil")
    pkt = packet_from_truth(truth, rng)
    feats = build_features(pkt)
    assert feats.moisture_pct > 30
    assert feats.optical_660_corr > feats.optical_660_raw * 5


def test_n_deficient_scenario_is_low_n():
    rng = np.random.default_rng(1)
    truth = sample_world(rng, scenario="pune-wheat-n-deficient")
    assert truth.crop == "wheat"
    assert truth.root().n < 150

from krishiayan.agronomy.recommend import build_recommendations
from krishiayan.services.crops import CROP_SPECS
from krishiayan.services.features import ScanFeatures


def _feats(**kw):
    base = dict(
        moisture_pct=16.0,
        temp_c=28.0,
        ec_dsm=0.7,
        ph=6.6,
        texture="black_cotton",
        optical_660_raw=0.1,
        optical_660_corr=0.3,
        nir_index=0.4,
        color_n=0.2,
        color_p=0.4,
        color_k=0.4,
        depth_cm=25,
        soc_proxy=0.7,
        moisture_gain=8.0,
    )
    base.update(kw)
    return ScanFeatures(**base)


def _wheat():
    return next(c for c in CROP_SPECS if c["code"] == "wheat")["spec"]


def test_low_n_recommends_urea():
    cards = build_recommendations(
        nutrients={"n_mgkg": 110, "p_mgkg": 18, "k_mgkg": 180, "n_lo": 90, "n_hi": 130, "soc_pct": 0.8, "ph": 6.6},
        feats=_feats(),
        crop_spec=_wheat(),
        crop_code="wheat",
        weather={"rain_next_48h_mm": 0, "rain_forecast_7d_mm": 2, "et0_mm": 5.5, "temp_c": 28},
        sowing=None,
        area_ha=1.0,
        language="en",
        stress="n_stress",
    )
    urea = [c for c in cards if c.get("payload", {}).get("what") == "urea"]
    assert urea, cards
    assert urea[0]["payload"]["how_much_kg_acre"] > 5
    assert urea[0]["payload"]["do_not"] is False


def test_rain_blocks_urea():
    cards = build_recommendations(
        nutrients={"n_mgkg": 110, "p_mgkg": 18, "k_mgkg": 180, "soc_pct": 0.8, "ph": 6.6},
        feats=_feats(),
        crop_spec=_wheat(),
        crop_code="wheat",
        weather={"rain_next_48h_mm": 42, "rain_forecast_7d_mm": 55, "et0_mm": 3, "temp_c": 26},
        sowing=None,
        area_ha=1.0,
        stress="n_stress",
    )
    skip = [c for c in cards if c["payload"].get("do_not")]
    assert skip


def test_hindi_card_exists():
    cards = build_recommendations(
        nutrients={"n_mgkg": 110, "p_mgkg": 18, "k_mgkg": 180, "soc_pct": 0.8, "ph": 6.6},
        feats=_feats(),
        crop_spec=_wheat(),
        crop_code="wheat",
        weather={"rain_next_48h_mm": 0, "rain_forecast_7d_mm": 0, "et0_mm": 5, "temp_c": 28},
        sowing=None,
        area_ha=1.0,
        language="hi",
        stress="n_stress",
    )
    assert any("यूरिया" in c["title"] or "नाइट्रोजन" in c["title"] for c in cards)

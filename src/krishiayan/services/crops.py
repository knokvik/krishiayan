"""Seed ICAR-oriented crop specs used by the agronomy engine."""

from sqlalchemy.orm import Session

from krishiayan.models.entities import Crop

CROP_SPECS: list[dict] = [
    {
        "code": "wheat",
        "name_en": "Wheat",
        "name_hi": "गेहूँ",
        "name_mr": "गहू",
        "season": "rabi",
        "duration_days": 120,
        "spec": {
            "yield_q_ha": 40,
            "nr": {"n": 2.2, "p": 0.9, "k": 1.6},
            "cs": {"n": 0.45, "p": 0.35, "k": 0.30},
            "cf": {"n": 0.55, "p": 0.40, "k": 0.60},
            "critical": {"n": 250, "p": 15, "k": 150, "ph": [6.0, 7.5], "moisture": [18, 32]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 0.5, "p_frac": 1.0, "k_frac": 0.5},
                {"stage": "tillering", "day": 25, "n_frac": 0.25, "p_frac": 0.0, "k_frac": 0.0},
                {"stage": "stem_elongation", "day": 45, "n_frac": 0.25, "p_frac": 0.0, "k_frac": 0.5},
            ],
            "base_temp_c": 5.0,
        },
    },
    {
        "code": "rice",
        "name_en": "Rice",
        "name_hi": "धान",
        "name_mr": "भात",
        "season": "kharif",
        "duration_days": 130,
        "spec": {
            "yield_q_ha": 50,
            "nr": {"n": 1.8, "p": 0.8, "k": 1.9},
            "cs": {"n": 0.40, "p": 0.30, "k": 0.28},
            "cf": {"n": 0.50, "p": 0.35, "k": 0.55},
            "critical": {"n": 280, "p": 12, "k": 140, "ph": [5.5, 7.0], "moisture": [30, 60]},
            "splits": [
                {"stage": "transplant", "day": 0, "n_frac": 0.4, "p_frac": 1.0, "k_frac": 0.5},
                {"stage": "tillering", "day": 21, "n_frac": 0.3, "p_frac": 0.0, "k_frac": 0.0},
                {"stage": "panicle", "day": 50, "n_frac": 0.3, "p_frac": 0.0, "k_frac": 0.5},
            ],
            "base_temp_c": 10.0,
        },
    },
    {
        "code": "maize",
        "name_en": "Maize",
        "name_hi": "मक्का",
        "name_mr": "मका",
        "season": "kharif",
        "duration_days": 100,
        "spec": {
            "yield_q_ha": 45,
            "nr": {"n": 2.4, "p": 1.0, "k": 2.0},
            "cs": {"n": 0.42, "p": 0.32, "k": 0.30},
            "cf": {"n": 0.52, "p": 0.38, "k": 0.58},
            "critical": {"n": 260, "p": 14, "k": 160, "ph": [5.8, 7.2], "moisture": [20, 35]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 0.4, "p_frac": 1.0, "k_frac": 0.5},
                {"stage": "knee_high", "day": 25, "n_frac": 0.3, "p_frac": 0.0, "k_frac": 0.0},
                {"stage": "tasseling", "day": 50, "n_frac": 0.3, "p_frac": 0.0, "k_frac": 0.5},
            ],
            "base_temp_c": 8.0,
        },
    },
    {
        "code": "soybean",
        "name_en": "Soybean",
        "name_hi": "सोयाबीन",
        "name_mr": "सोयाबीन",
        "season": "kharif",
        "duration_days": 100,
        "spec": {
            "yield_q_ha": 20,
            "nr": {"n": 1.2, "p": 1.1, "k": 1.8},
            "cs": {"n": 0.55, "p": 0.35, "k": 0.30},
            "cf": {"n": 0.45, "p": 0.40, "k": 0.55},
            "critical": {"n": 180, "p": 16, "k": 150, "ph": [6.0, 7.5], "moisture": [18, 32]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 1.0, "p_frac": 1.0, "k_frac": 1.0},
            ],
            "base_temp_c": 10.0,
        },
    },
    {
        "code": "cotton",
        "name_en": "Cotton",
        "name_hi": "कपास",
        "name_mr": "कापूस",
        "season": "kharif",
        "duration_days": 160,
        "spec": {
            "yield_q_ha": 18,
            "nr": {"n": 4.5, "p": 1.6, "k": 4.0},
            "cs": {"n": 0.40, "p": 0.30, "k": 0.28},
            "cf": {"n": 0.50, "p": 0.35, "k": 0.55},
            "critical": {"n": 220, "p": 12, "k": 140, "ph": [6.0, 8.0], "moisture": [16, 28]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 0.3, "p_frac": 1.0, "k_frac": 0.5},
                {"stage": "square", "day": 40, "n_frac": 0.4, "p_frac": 0.0, "k_frac": 0.0},
                {"stage": "boll", "day": 80, "n_frac": 0.3, "p_frac": 0.0, "k_frac": 0.5},
            ],
            "base_temp_c": 12.0,
        },
    },
    {
        "code": "sugarcane",
        "name_en": "Sugarcane",
        "name_hi": "गन्ना",
        "name_mr": "ऊस",
        "season": "annual",
        "duration_days": 360,
        "spec": {
            "yield_q_ha": 800,
            "nr": {"n": 0.18, "p": 0.06, "k": 0.22},
            "cs": {"n": 0.35, "p": 0.28, "k": 0.25},
            "cf": {"n": 0.48, "p": 0.32, "k": 0.50},
            "critical": {"n": 240, "p": 14, "k": 160, "ph": [6.0, 7.5], "moisture": [22, 40]},
            "splits": [
                {"stage": "planting", "day": 0, "n_frac": 0.3, "p_frac": 1.0, "k_frac": 0.4},
                {"stage": "tillering", "day": 60, "n_frac": 0.4, "p_frac": 0.0, "k_frac": 0.3},
                {"stage": "grand_growth", "day": 150, "n_frac": 0.3, "p_frac": 0.0, "k_frac": 0.3},
            ],
            "base_temp_c": 12.0,
        },
    },
    {
        "code": "onion",
        "name_en": "Onion",
        "name_hi": "प्याज़",
        "name_mr": "कांदा",
        "season": "rabi",
        "duration_days": 120,
        "spec": {
            "yield_q_ha": 250,
            "nr": {"n": 0.35, "p": 0.18, "k": 0.40},
            "cs": {"n": 0.40, "p": 0.32, "k": 0.30},
            "cf": {"n": 0.50, "p": 0.38, "k": 0.55},
            "critical": {"n": 200, "p": 18, "k": 180, "ph": [6.0, 7.0], "moisture": [20, 30]},
            "splits": [
                {"stage": "transplant", "day": 0, "n_frac": 0.4, "p_frac": 1.0, "k_frac": 0.5},
                {"stage": "bulb", "day": 40, "n_frac": 0.6, "p_frac": 0.0, "k_frac": 0.5},
            ],
            "base_temp_c": 7.0,
        },
    },
    {
        "code": "tomato",
        "name_en": "Tomato",
        "name_hi": "टमाटर",
        "name_mr": "टोमॅटो",
        "season": "rabi",
        "duration_days": 110,
        "spec": {
            "yield_q_ha": 300,
            "nr": {"n": 0.30, "p": 0.12, "k": 0.45},
            "cs": {"n": 0.38, "p": 0.30, "k": 0.28},
            "cf": {"n": 0.50, "p": 0.35, "k": 0.55},
            "critical": {"n": 220, "p": 20, "k": 180, "ph": [6.0, 7.0], "moisture": [22, 35]},
            "splits": [
                {"stage": "transplant", "day": 0, "n_frac": 0.3, "p_frac": 1.0, "k_frac": 0.3},
                {"stage": "flowering", "day": 30, "n_frac": 0.4, "p_frac": 0.0, "k_frac": 0.4},
                {"stage": "fruit", "day": 55, "n_frac": 0.3, "p_frac": 0.0, "k_frac": 0.3},
            ],
            "base_temp_c": 10.0,
        },
    },
    {
        "code": "tur",
        "name_en": "Pigeon pea",
        "name_hi": "अरहर",
        "name_mr": "तूर",
        "season": "kharif",
        "duration_days": 160,
        "spec": {
            "yield_q_ha": 12,
            "nr": {"n": 1.5, "p": 1.2, "k": 1.4},
            "cs": {"n": 0.55, "p": 0.35, "k": 0.30},
            "cf": {"n": 0.40, "p": 0.40, "k": 0.55},
            "critical": {"n": 160, "p": 14, "k": 130, "ph": [6.0, 7.5], "moisture": [16, 28]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 1.0, "p_frac": 1.0, "k_frac": 1.0},
            ],
            "base_temp_c": 10.0,
        },
    },
    {
        "code": "groundnut",
        "name_en": "Groundnut",
        "name_hi": "मूंगफली",
        "name_mr": "भुईमूग",
        "season": "kharif",
        "duration_days": 110,
        "spec": {
            "yield_q_ha": 18,
            "nr": {"n": 1.4, "p": 1.0, "k": 1.6},
            "cs": {"n": 0.52, "p": 0.34, "k": 0.30},
            "cf": {"n": 0.42, "p": 0.38, "k": 0.55},
            "critical": {"n": 170, "p": 15, "k": 140, "ph": [6.0, 7.0], "moisture": [16, 28]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 1.0, "p_frac": 1.0, "k_frac": 1.0},
            ],
            "base_temp_c": 12.0,
        },
    },
    {
        "code": "jowar",
        "name_en": "Sorghum",
        "name_hi": "ज्वार",
        "name_mr": "ज्वारी",
        "season": "kharif",
        "duration_days": 110,
        "spec": {
            "yield_q_ha": 25,
            "nr": {"n": 2.0, "p": 0.9, "k": 1.7},
            "cs": {"n": 0.42, "p": 0.32, "k": 0.30},
            "cf": {"n": 0.50, "p": 0.36, "k": 0.55},
            "critical": {"n": 200, "p": 12, "k": 140, "ph": [5.8, 7.5], "moisture": [14, 26]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 0.5, "p_frac": 1.0, "k_frac": 0.5},
                {"stage": "boot", "day": 35, "n_frac": 0.5, "p_frac": 0.0, "k_frac": 0.5},
            ],
            "base_temp_c": 10.0,
        },
    },
    {
        "code": "chana",
        "name_en": "Chickpea",
        "name_hi": "चना",
        "name_mr": "हरभरा",
        "season": "rabi",
        "duration_days": 110,
        "spec": {
            "yield_q_ha": 16,
            "nr": {"n": 1.6, "p": 1.1, "k": 1.5},
            "cs": {"n": 0.55, "p": 0.35, "k": 0.30},
            "cf": {"n": 0.42, "p": 0.40, "k": 0.55},
            "critical": {"n": 170, "p": 16, "k": 140, "ph": [6.0, 7.5], "moisture": [14, 24]},
            "splits": [
                {"stage": "sowing", "day": 0, "n_frac": 1.0, "p_frac": 1.0, "k_frac": 1.0},
            ],
            "base_temp_c": 5.0,
        },
    },
]


def seed_crops(db: Session) -> None:
    existing = {c.code for c in db.query(Crop).all()}
    for spec in CROP_SPECS:
        if spec["code"] in existing:
            continue
        db.add(
            Crop(
                code=spec["code"],
                name_en=spec["name_en"],
                name_hi=spec["name_hi"],
                name_mr=spec["name_mr"],
                season=spec["season"],
                duration_days=spec["duration_days"],
                spec=spec["spec"],
            )
        )
    db.commit()

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta

from krishiayan.core.config import ROOT
from krishiayan.services.agronomy_features import (
    growing_degree_days,
    moisture_deficit,
    nutrient_index,
    soil_health_score,
    water_stress_index,
)

PRICES = json.loads((ROOT / "data" / "icar" / "fertilizer_prices.json").read_text())

COPY = {
    "en": {
        "urea": "Apply {kg_acre:.0f} kg urea per acre ({bags:.1f} bags) {when}.",
        "dap": "Apply {kg_acre:.0f} kg DAP per acre {when} to rebuild phosphorus.",
        "mop": "Apply {kg_acre:.0f} kg MOP per acre {when} for potassium.",
        "skip_n": "Do not apply urea now — {reason}",
        "irrigate": "Soil moisture is low — irrigate within {hours} hours.",
        "wait_rain": "Rain is coming ({mm:.0f} mm in 48 h) — hold irrigation.",
        "waterlog": "Soil is too wet — stop irrigation and drain if you can.",
        "n_stress": "Crop is under nitrogen stress.",
        "healthy": "Crop condition looks good. Keep the current plan.",
        "lime": "pH is low — apply agricultural lime so nutrients can unlock.",
        "gypsum": "pH is high / sodic risk — gypsum will help more than more NPK.",
        "next3": "in the next 3 days",
        "today": "today",
        "stage": "at {stage}",
    },
    "hi": {
        "urea": "अगले आवेदन में {kg_acre:.0f} किलो यूरिया प्रति एकड़ डालें ({when})।",
        "dap": "फॉस्फोरस के लिए {kg_acre:.0f} किलो DAP प्रति एकड़ डालें ({when})।",
        "mop": "पोटैशियम के लिए {kg_acre:.0f} किलो MOP प्रति एकड़ डालें ({when})।",
        "skip_n": "अभी यूरिया न डालें — {reason}",
        "irrigate": "नमी कम है — {hours} घंटे में सिंचाई करें।",
        "wait_rain": "बारिश आ रही है ({mm:.0f} मिमी / 48 घंटे) — सिंचाई रोकें।",
        "waterlog": "खेत गीला है — सिंचाई बंद करें।",
        "n_stress": "फसल में नाइट्रोजन की कमी है।",
        "healthy": "फसल की हालत अच्छी है।",
        "lime": "pH कम है — चूना डालें।",
        "gypsum": "pH अधिक है — जिप्सम डालें।",
        "next3": "अगले 3 दिनों में",
        "today": "आज",
        "stage": "{stage} अवस्था में",
    },
    "mr": {
        "urea": "एकराला {kg_acre:.0f} किलो युरिया टाका ({when})।",
        "dap": "फॉस्फरससाठी एकराला {kg_acre:.0f} किलो DAP टाका ({when})।",
        "mop": "पोटॅशियमसाठी एकराला {kg_acre:.0f} किलो MOP टाका ({when})।",
        "skip_n": "आता युरिया टाकू नका — {reason}",
        "irrigate": "ओलावा कमी आहे — {hours} तासांत पाणी द्या.",
        "wait_rain": "पाऊस येतोय ({mm:.0f} मिमी / ४८ तास) — पाणी थांबवा.",
        "waterlog": "शेत ओले आहे — पाणी बंद करा.",
        "n_stress": "पिकात नायट्रोजनची कमतरता आहे.",
        "healthy": "पिकाची स्थिती चांगली आहे.",
        "lime": "pH कमी आहे — चुना टाका.",
        "gypsum": "pH जास्त आहे — जिप्सम टाका.",
        "next3": "पुढील ३ दिवसांत",
        "today": "आज",
        "stage": "{stage} अवस्थेत",
    },
}


def _t(lang: str, key: str, **kw) -> str:
    table = COPY.get(lang) or COPY["en"]
    return table.get(key, COPY["en"][key]).format(**kw)


def _stcr(req: float, soil: float, cs: float, cf: float, cap: float) -> float:
    dose = (req - cs * soil) / max(cf, 1e-3)
    return float(max(0.0, min(cap, dose)))


def _product(kg_ha_nutrient: float, grade: float) -> float:
    if grade <= 0:
        return 0.0
    return kg_ha_nutrient / grade


def _current_split(spec: dict, sowing: datetime | None) -> dict:
    splits = spec.get("splits") or [{"stage": "sowing", "day": 0, "n_frac": 1, "p_frac": 1, "k_frac": 1}]
    if sowing is None:
        return splits[0]
    if sowing.tzinfo is None:
        sowing = sowing.replace(tzinfo=UTC)
    day = max(0, (datetime.now(UTC) - sowing).days)
    chosen = splits[0]
    for s in splits:
        if day >= s["day"]:
            chosen = s
    return chosen


def build_recommendations(
    *,
    nutrients: dict,
    feats,
    crop_spec: dict,
    crop_code: str,
    weather: dict,
    sowing: datetime | None,
    area_ha: float,
    language: str = "en",
    stress: str = "healthy",
) -> list[dict]:
    lang = language if language in COPY else "en"
    crit = crop_spec["critical"]
    nr, cs, cf = crop_spec["nr"], crop_spec["cs"], crop_spec["cf"]
    target = crop_spec["yield_q_ha"]
    n, p, k = nutrients["n_mgkg"], nutrients["p_mgkg"], nutrients["k_mgkg"]
    ph = nutrients.get("ph") or feats.ph or 6.8
    moisture = feats.moisture_pct
    rain48 = float(weather.get("rain_next_48h_mm") or 0)
    rain7 = float(weather.get("rain_forecast_7d_mm") or 0)
    et0 = float(weather.get("et0_mm") or 4)
    split = _current_split(crop_spec, sowing)
    stage = split["stage"]

    n_ha = _stcr(nr["n"] * target, n, cs["n"], cf["n"], cap=180) * split.get("n_frac", 1)
    p_ha = _stcr(nr["p"] * target, p, cs["p"], cf["p"], cap=80) * split.get("p_frac", 1)
    k_ha = _stcr(nr["k"] * target, k, cs["k"], cf["k"], cap=80) * split.get("k_frac", 1)

    # Prefer DAP for P, leftover N as urea, K as MOP
    dap_ha = _product(p_ha, PRICES["dap"]["p"])
    n_from_dap = dap_ha * PRICES["dap"]["n"]
    urea_ha = _product(max(0.0, n_ha - n_from_dap), PRICES["urea"]["n"])
    mop_ha = _product(k_ha, PRICES["mop"]["k"])

    idx = nutrient_index(n, p, k, crit)
    health = soil_health_score(
        moisture_pct=moisture,
        ph=ph,
        ec=feats.ec_dsm,
        soc=nutrients.get("soc_pct") or 0.6,
        n_idx=idx["n"],
        p_idx=idx["p"],
        k_idx=idx["k"],
    )
    wsi = water_stress_index(moisture, crit["moisture"][0], crit["moisture"][1], et0, rain48)
    deficit = moisture_deficit(moisture, crit["moisture"][0], crit["moisture"][1])
    gdd = growing_degree_days(sowing, float(weather.get("temp_c") or feats.temp_c), crop_spec.get("base_temp_c", 10))

    cards: list[dict] = []
    when = _t(lang, "next3")
    if rain48 >= 20:
        cards.append(
            {
                "kind": "fertilizer",
                "priority": 1,
                "title": _t(lang, "skip_n", reason=f"{rain48:.0f} mm rain / 48 h"),
                "body": _t(lang, "skip_n", reason=f"{rain48:.0f} mm rain / 48 h"),
                "payload": {
                    "what": "urea",
                    "how_much_kg_ha": 0,
                    "how_much_kg_acre": 0,
                    "when": None,
                    "do_not": True,
                    "reason": "heavy_rain_forecast",
                },
            }
        )
    elif urea_ha >= 8:
        kg_acre = urea_ha / 2.471
        bags = kg_acre / PRICES["urea"]["bag_kg"]
        window_start = datetime.now(UTC).date().isoformat()
        window_end = (datetime.now(UTC) + timedelta(days=3)).date().isoformat()
        cards.append(
            {
                "kind": "fertilizer",
                "priority": 1 if idx["n"] < 0.85 else 2,
                "title": _t(lang, "urea", kg_acre=kg_acre, bags=bags, when=when),
                "body": _t(lang, "n_stress") if idx["n"] < 0.85 else _t(lang, "urea", kg_acre=kg_acre, bags=bags, when=when),
                "payload": {
                    "what": "urea",
                    "how_much_kg_ha": round(urea_ha, 1),
                    "how_much_kg_acre": round(kg_acre, 1),
                    "bags": round(bags, 2),
                    "when": {"start": window_start, "end": window_end, "stage": stage},
                    "how": "broadcast_then_light_irrigation",
                    "cost_inr": round(urea_ha * PRICES["urea"]["inr_per_kg"] * area_ha, 0),
                    "do_not": False,
                    "why": f"Root-zone N is {n:.0f} mg/kg (CI {nutrients.get('n_lo', n):.0f}–{nutrients.get('n_hi', n):.0f}).",
                },
            }
        )

    if dap_ha >= 8 and rain48 < 25:
        kg_acre = dap_ha / 2.471
        cards.append(
            {
                "kind": "fertilizer",
                "priority": 2,
                "title": _t(lang, "dap", kg_acre=kg_acre, when=_t(lang, "stage", stage=stage)),
                "body": _t(lang, "dap", kg_acre=kg_acre, when=_t(lang, "stage", stage=stage)),
                "payload": {
                    "what": "dap",
                    "how_much_kg_ha": round(dap_ha, 1),
                    "how_much_kg_acre": round(kg_acre, 1),
                    "when": {"stage": stage},
                    "cost_inr": round(dap_ha * PRICES["dap"]["inr_per_kg"] * area_ha, 0),
                },
            }
        )
    if mop_ha >= 8:
        kg_acre = mop_ha / 2.471
        cards.append(
            {
                "kind": "fertilizer",
                "priority": 3,
                "title": _t(lang, "mop", kg_acre=kg_acre, when=_t(lang, "stage", stage=stage)),
                "body": _t(lang, "mop", kg_acre=kg_acre, when=_t(lang, "stage", stage=stage)),
                "payload": {
                    "what": "mop",
                    "how_much_kg_ha": round(mop_ha, 1),
                    "how_much_kg_acre": round(kg_acre, 1),
                    "when": {"stage": stage},
                    "cost_inr": round(mop_ha * PRICES["mop"]["inr_per_kg"] * area_ha, 0),
                },
            }
        )

    if ph < 5.8:
        cards.append({"kind": "amendment", "priority": 2, "title": _t(lang, "lime"), "body": _t(lang, "lime"), "payload": {"what": "lime"}})
    if ph > 8.2 or feats.ec_dsm >= 2.0:
        cards.append({"kind": "amendment", "priority": 2, "title": _t(lang, "gypsum"), "body": _t(lang, "gypsum"), "payload": {"what": "gypsum"}})

    if moisture > crit["moisture"][1] + 8:
        cards.append({"kind": "irrigation", "priority": 1, "title": _t(lang, "waterlog"), "body": _t(lang, "waterlog"), "payload": {"action": "stop"}})
    elif rain48 >= 15:
        cards.append(
            {
                "kind": "irrigation",
                "priority": 2,
                "title": _t(lang, "wait_rain", mm=rain48),
                "body": _t(lang, "wait_rain", mm=rain48),
                "payload": {"action": "wait", "rain_48h_mm": rain48},
            }
        )
    elif deficit > 0:
        hours = 24 if wsi > 0.5 else 48
        cards.append(
            {
                "kind": "irrigation",
                "priority": 1 if wsi > 0.45 else 2,
                "title": _t(lang, "irrigate", hours=hours),
                "body": _t(lang, "irrigate", hours=hours),
                "payload": {"action": "irrigate", "hours": hours, "mm": round(deficit * 0.8, 1)},
            }
        )

    condition = "good"
    if stress in {"n_stress", "p_stress", "k_stress", "water_stress", "salinity", "heat", "waterlogging"}:
        condition = "stress" if wsi > 0.5 or idx["n"] < 0.7 else "watch"
    title = _t(lang, "n_stress") if stress == "n_stress" else _t(lang, "healthy")
    cards.append(
        {
            "kind": "crop",
            "priority": 2 if condition != "good" else 4,
            "title": title,
            "body": title,
            "payload": {
                "condition": condition,
                "stress": stress,
                "soil_health": health,
                "gdd": round(gdd, 1),
                "nutrient_index": idx,
                "water_stress": round(wsi, 3),
                "rain_7d_mm": rain7,
            },
        }
    )
    cards.sort(key=lambda c: c["priority"])
    return cards

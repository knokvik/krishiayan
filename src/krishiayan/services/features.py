"""Canonical feature vector built from a calibrated, moisture-corrected scan."""

from __future__ import annotations

from dataclasses import dataclass, field

from krishiayan.schemas.ingest import Layer, ProbePacket
from krishiayan.services.calibrate import ec_dsm, moisture_pct, temp_c
from krishiayan.services.correct import correct_optical, nir_organics_index, texture_from_eis


def _rgb_ratio(rgb: list[int] | None) -> float:
    if not rgb or len(rgb) < 3:
        return 0.0
    s = sum(rgb) or 1
    # colorimetric: more of the target channel vs others
    return rgb[1] / s


@dataclass
class ScanFeatures:
    moisture_pct: float
    temp_c: float
    ec_dsm: float
    ph: float | None
    texture: str
    optical_660_raw: float
    optical_660_corr: float
    nir_index: float
    color_n: float
    color_p: float
    color_k: float
    depth_cm: float
    soc_proxy: float | None
    moisture_gain: float
    layers: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "moisture_pct": self.moisture_pct,
            "temp_c": self.temp_c,
            "ec_dsm": self.ec_dsm,
            "ph": self.ph,
            "texture": self.texture,
            "optical_660_raw": self.optical_660_raw,
            "optical_660_corr": self.optical_660_corr,
            "nir_index": self.nir_index,
            "color_n": self.color_n,
            "color_p": self.color_p,
            "color_k": self.color_k,
            "depth_cm": self.depth_cm,
            "soc_proxy": self.soc_proxy,
            "moisture_gain": self.moisture_gain,
        }

    def model_row(self) -> dict:
        tex = {
            "sand": 0,
            "sandy_loam": 1,
            "loam": 2,
            "laterite": 3,
            "black_cotton": 4,
            "clay": 5,
            "saline": 6,
        }
        return {
            "moisture_pct": self.moisture_pct,
            "temp_c": self.temp_c,
            "ec_dsm": self.ec_dsm,
            "ph": self.ph if self.ph is not None else 6.8,
            "texture_i": tex.get(self.texture, 2),
            "optical_660_corr": self.optical_660_corr,
            "nir_index": self.nir_index,
            "color_n": self.color_n,
            "color_p": self.color_p,
            "color_k": self.color_k,
            "depth_cm": self.depth_cm,
            "moisture_gain": self.moisture_gain,
        }


def layer_features(layer: Layer) -> dict:
    m = moisture_pct(layer.moisture_raw, layer.soil_moisture) or 20.0
    t = temp_c(layer.temp_raw, layer.soil_temperature) or 28.0
    e = ec_dsm(layer.ec_raw, layer.electrical_conductivity) or 0.6
    texture = texture_from_eis(layer.eis_real, m)
    raw_660 = layer.optical_660
    if layer.extraction and layer.extraction.turbidity_660 is not None:
        raw_660 = layer.extraction.turbidity_660
    raw_660 = float(raw_660 or 0.0)
    corr_660 = correct_optical(raw_660, m, texture) or 0.0
    nir = nir_organics_index(layer.optical_nir, corr_660)
    rgb = layer.colorimetric_rgb or {}
    from krishiayan.services.correct import moisture_correction_gain

    return {
        "depth_cm": layer.depth_cm,
        "moisture_pct": m,
        "temp_c": t,
        "ec_dsm": e,
        "ph": layer.ph,
        "texture": texture,
        "optical_660_raw": raw_660,
        "optical_660_corr": corr_660,
        "nir_index": nir,
        "color_n": _rgb_ratio(rgb.get("n")),
        "color_p": _rgb_ratio(rgb.get("p")),
        "color_k": _rgb_ratio(rgb.get("k")),
        "soc_proxy": layer.soc_proxy,
        "moisture_gain": moisture_correction_gain(m),
    }


def build_features(packet: ProbePacket) -> ScanFeatures:
    layers = [layer_features(L) for L in packet.normalized_layers()]
    # Root-zone weighted (20–45 cm preferred, else mean)
    root = [x for x in layers if 15 <= x["depth_cm"] <= 50] or layers
    def avg(key: str) -> float:
        vals = [x[key] for x in root if x.get(key) is not None]
        return float(sum(vals) / max(1, len(vals)))

    phs = [x["ph"] for x in root if x.get("ph") is not None]
    ph = float(sum(phs) / len(phs)) if phs else packet.ph
    textures = [x["texture"] for x in root]
    texture = max(set(textures), key=textures.count)
    return ScanFeatures(
        moisture_pct=avg("moisture_pct"),
        temp_c=avg("temp_c"),
        ec_dsm=avg("ec_dsm"),
        ph=ph,
        texture=texture,
        optical_660_raw=avg("optical_660_raw"),
        optical_660_corr=avg("optical_660_corr"),
        nir_index=avg("nir_index"),
        color_n=avg("color_n"),
        color_p=avg("color_p"),
        color_k=avg("color_k"),
        depth_cm=avg("depth_cm"),
        soc_proxy=packet.soc_proxy or packet.organics,
        moisture_gain=avg("moisture_gain"),
        layers=layers,
    )

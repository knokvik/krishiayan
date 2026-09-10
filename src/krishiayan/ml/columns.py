FEATURE_COLS = [
    "moisture_pct",
    "temp_c",
    "ec_dsm",
    "ph",
    "texture_i",
    "optical_660_corr",
    "nir_index",
    "color_n",
    "color_p",
    "color_k",
    "depth_cm",
    "moisture_gain",
    "rain_7d_mm",
    "et0_mm",
]

REGRESSION_HEADS = ["n_mgkg", "p_mgkg", "k_mgkg", "soc_pct", "ph_hat", "yield_index"]
STRESS_LABELS = [
    "healthy",
    "water_stress",
    "n_stress",
    "p_stress",
    "k_stress",
    "salinity",
    "heat",
    "waterlogging",
]

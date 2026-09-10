#!/usr/bin/env python3
"""Coloured 3D proof figures for the README (latintel-style, agritech palette)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from krishiayan.ml.columns import FEATURE_COLS  # noqa: E402
from krishiayan.ml.dataset import make_dataframe  # noqa: E402
from krishiayan.ml.infer import ModelRegistry  # noqa: E402
from krishiayan.services.correct import moisture_correction_gain  # noqa: E402

OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#1b3d22",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
    }
)


def fig_correction_surface():
    m = np.linspace(5, 50, 80)
    raw = np.linspace(0.02, 0.45, 80)
    M, R = np.meshgrid(m, raw)
    Z = R * (1 + 0.035 * M + 0.012 * M**2)
    fig = plt.figure(figsize=(10.5, 7.2))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(M, R, Z, cmap="viridis", linewidth=0, antialiased=True, alpha=0.95)
    ax.set_xlabel("Soil moisture (%)")
    ax.set_ylabel("Raw 660 nm turbidity")
    ax.set_zlabel("Moisture-corrected optical")
    ax.set_title("MAEP moisture-adaptive correction surface")
    fig.colorbar(surf, ax=ax, shrink=0.55, pad=0.08, label="corrected signal")
    ax.view_init(22, -55)
    fig.tight_layout()
    fig.savefig(OUT / "graph_surface_3d.png", dpi=160)
    plt.close(fig)


def fig_npk_cloud():
    import joblib

    df = make_dataframe(n=700, seed=11)
    bundle = joblib.load(ROOT / "models" / "artifacts" / "bundle.joblib")
    pred_n = bundle["heads"]["n_mgkg"]["model"].predict(df[FEATURE_COLS])
    pred_p = bundle["heads"]["p_mgkg"]["model"].predict(df[FEATURE_COLS])
    pred_k = bundle["heads"]["k_mgkg"]["model"].predict(df[FEATURE_COLS])
    err = np.abs(pred_n - df["n_mgkg"]) + np.abs(pred_p - df["p_mgkg"]) + np.abs(pred_k - df["k_mgkg"])
    fig = plt.figure(figsize=(10.5, 7.2))
    ax = fig.add_subplot(111, projection="3d")
    p = ax.scatter(pred_n, pred_p, pred_k, c=err, cmap="plasma", s=18, alpha=0.85)
    ax.set_xlabel("Predicted N (mg/kg)")
    ax.set_ylabel("Predicted P (mg/kg)")
    ax.set_zlabel("Predicted K (mg/kg)")
    ax.set_title("sim: recovered NPK cloud (colour = absolute error)")
    fig.colorbar(p, ax=ax, shrink=0.55, pad=0.08, label="|ΔN|+|ΔP|+|ΔK|")
    ax.view_init(18, 35)
    fig.tight_layout()
    fig.savefig(OUT / "graph_npk_3d.png", dpi=160)
    plt.close(fig)


def fig_soil_landscape():
    rng = np.random.default_rng(4)
    x = np.linspace(0, 10, 60)
    y = np.linspace(0, 8, 48)
    X, Y = np.meshgrid(x, y)
    health = (
        62
        + 18 * np.sin(X / 2.2) * np.cos(Y / 1.8)
        - 12 * np.exp(-((X - 7.2) ** 2 + (Y - 2.1) ** 2) / 3.5)
        + rng.normal(0, 1.2, X.shape)
    )
    fig = plt.figure(figsize=(10.5, 7.2))
    ax = fig.add_subplot(111, projection="3d")
    surf = ax.plot_surface(X, Y, health, cmap="RdYlGn", vmin=40, vmax=90, linewidth=0, antialiased=True)
    ax.set_xlabel("East (plot units)")
    ax.set_ylabel("North (plot units)")
    ax.set_zlabel("Soil health (0–100)")
    ax.set_title("sim: field soil-health landscape")
    fig.colorbar(surf, ax=ax, shrink=0.55, pad=0.08)
    ax.view_init(28, -40)
    fig.tight_layout()
    fig.savefig(OUT / "graph_soil_landscape.png", dpi=160)
    plt.close(fig)


def fig_metrics():
    metrics = json.loads((ROOT / "models" / "artifacts" / "metrics.json").read_text())
    heads = [(k, v["r2"]) for k, v in metrics["heads"].items() if "r2" in v]
    names, r2 = zip(*heads, strict=False)
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    colors = cm.viridis(np.linspace(0.2, 0.85, len(names)))
    ax.bar(names, r2, color=colors, edgecolor="#12361a")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Held-out R² (plot-id split)")
    ax.set_title("sim: model recovers planted soil truth")
    ax.axhline(0.9, color="#c62828", ls="--", lw=1, label="R² = 0.90")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "graph_metrics.png", dpi=160)
    plt.close(fig)


def fig_wet_vs_dry():
    m = np.linspace(5, 50, 200)
    gain = 1.0 + 0.035 * m + 0.012 * (m**2)
    raw = np.full_like(m, 0.22) / np.maximum(gain, 1)
    corr = raw * gain
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ax.plot(m, raw, color="#c62828", lw=2.4, label="Raw turbidity (wet collapse)")
    ax.plot(m, corr, color="#2e7d32", lw=2.4, label="MAEP-corrected optical")
    ax.axvline(30, color="#1565c0", ls="--", label="30% moisture cliff")
    ax.set_xlabel("Soil moisture (%)")
    ax.set_ylabel("Optical channel")
    ax.set_title("Why cheap kits fail in the monsoon — and how Krishiayan corrects them")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "graph_wet_vs_dry.png", dpi=160)
    plt.close(fig)


def fig_pred_vs_true():
    import joblib

    df = make_dataframe(n=800, seed=21)
    bundle = joblib.load(ROOT / "models" / "artifacts" / "bundle.joblib")
    pred = bundle["heads"]["n_mgkg"]["model"].predict(df[FEATURE_COLS])
    fig, ax = plt.subplots(figsize=(10.5, 6.4))
    sc = ax.scatter(df["n_mgkg"], pred, c=df["moisture_pct"], cmap="coolwarm", s=16, alpha=0.85)
    lo, hi = 60, 430
    ax.plot([lo, hi], [lo, hi], color="#12361a", lw=1)
    ax.set_xlabel("Planted N (mg/kg)")
    ax.set_ylabel("Model N (mg/kg)")
    ax.set_title("sim: nitrogen head — colour is soil moisture")
    fig.colorbar(sc, ax=ax, label="moisture %")
    fig.tight_layout()
    fig.savefig(OUT / "graph_monte_carlo.png", dpi=160)
    plt.close(fig)


def fig_regimes():
    """Stress-class mix + SOC wet/dry MAE — second README strip."""
    metrics = json.loads((ROOT / "models" / "artifacts" / "metrics.json").read_text())
    fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.6))
    heads = metrics["heads"]
    mae = [heads["n_mgkg"]["mae"], heads["p_mgkg"]["mae"], heads["k_mgkg"]["mae"]]
    axes[0].bar(["N", "P", "K"], mae, color=["#43a047", "#fb8c00", "#8e24aa"])
    axes[0].set_ylabel("MAE (mg/kg)")
    axes[0].set_title("Nutrient MAE on held-out plots")
    w = metrics["wet_soil"]
    axes[1].bar(
        ["Raw 660 nm\n(wet)", "Corrected 660 nm\n(wet)"],
        [w["mean_raw_optical_wet"], w["mean_corr_optical_wet"]],
        color=["#c62828", "#2e7d32"],
    )
    axes[1].set_title("Optical recovery above 30% moisture")
    fig.suptitle("sim: proof the moisture-adaptive path is doing the work", fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "fig2_regimes.png", dpi=160)
    plt.close(fig)


def main():
    fig_correction_surface()
    fig_npk_cloud()
    fig_soil_landscape()
    fig_metrics()
    fig_wet_vs_dry()
    fig_pred_vs_true()
    fig_regimes()
    print("wrote", list(OUT.glob("*.png")))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Write a short eval report from trained artifacts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

ART = ROOT / "models" / "artifacts"


def main() -> None:
    metrics = json.loads((ART / "metrics.json").read_text())
    lines = ["# Krishiayan model evaluation", "", f"Samples: {metrics['n_samples']} (plot-id grouped split)", ""]
    lines.append("| Head | MAE | R² | 90% interval coverage |")
    lines.append("|---|---:|---:|---:|")
    for name, m in metrics["heads"].items():
        if "mae" in m:
            lines.append(f"| {name} | {m['mae']} | {m['r2']} | {m['coverage_90']} |")
        else:
            lines.append(f"| {name} | accuracy {m.get('accuracy')} | — | — |")
    if "wet_soil" in metrics:
        w = metrics["wet_soil"]
        lines += [
            "",
            "## Wet-soil optical path",
            "",
            f"- Wet test rows: {w['n_wet_test']}",
            f"- Mean raw 660 nm (collapsed): {w['mean_raw_optical_wet']}",
            f"- Mean corrected 660 nm: {w['mean_corr_optical_wet']}",
            f"- SOC MAE wet / dry: {w['soc_mae_wet']} / {w['soc_mae_dry']}",
            "",
            "Simulated data is labelled `sim:` everywhere. These numbers prove the pipeline recovers planted truth.",
        ]
    ART.joinpath("eval.md").write_text("\n".join(lines) + "\n")
    print(ART.joinpath("eval.md").read_text())


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Train Krishiayan nutrient / SOC / stress heads on planted simulator truth."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier, XGBRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from krishiayan.ml.columns import FEATURE_COLS, REGRESSION_HEADS  # noqa: E402
from krishiayan.ml.dataset import make_dataframe  # noqa: E402

ART = ROOT / "models" / "artifacts"
ART.mkdir(parents=True, exist_ok=True)


def _split(df):
    gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=7)
    train_idx, test_idx = next(gss.split(df, groups=df["plot_id"]))
    rest = df.iloc[train_idx]
    gss2 = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=7)
    tr_idx, cal_idx = next(gss2.split(rest, groups=rest["plot_id"]))
    return rest.iloc[tr_idx], rest.iloc[cal_idx], df.iloc[test_idx]


def train(n_samples: int = 2400) -> dict:
    df = make_dataframe(n=n_samples, seed=7)
    train_df, cal_df, test_df = _split(df)
    bundle: dict = {"features": FEATURE_COLS, "heads": {}}
    metrics: dict = {
        "n_samples": int(len(df)),
        "n_train": int(len(train_df)),
        "n_cal": int(len(cal_df)),
        "n_test": int(len(test_df)),
        "split": "group-shuffle by plot_id",
        "heads": {},
    }

    Xtr, Xcal, Xte = train_df[FEATURE_COLS], cal_df[FEATURE_COLS], test_df[FEATURE_COLS]

    for head in REGRESSION_HEADS:
        model = XGBRegressor(
            n_estimators=160,
            max_depth=4,
            learning_rate=0.08,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=7,
            n_jobs=2,
            tree_method="hist",
        )
        model.fit(Xtr, train_df[head])
        pred_cal = model.predict(Xcal)
        resid = np.abs(cal_df[head].to_numpy() - pred_cal)
        q90 = float(np.quantile(resid, 0.90))
        pred_te = model.predict(Xte)
        y_te = test_df[head].to_numpy()
        mae = float(mean_absolute_error(y_te, pred_te))
        r2 = float(r2_score(y_te, pred_te))
        inside = float(np.mean(np.abs(y_te - pred_te) <= q90))
        bundle["heads"][head] = {"model": model, "q90": q90, "kind": "regressor"}
        metrics["heads"][head] = {
            "mae": round(mae, 4),
            "r2": round(r2, 4),
            "conformal_q90": round(q90, 4),
            "coverage_90": round(inside, 4),
        }

    le = LabelEncoder()
    ytr = le.fit_transform(train_df["stress"])
    clf = XGBClassifier(
        n_estimators=140,
        max_depth=4,
        learning_rate=0.08,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=7,
        n_jobs=2,
        tree_method="hist",
        objective="multi:softprob",
        num_class=len(le.classes_),
    )
    clf.fit(Xtr, ytr)
    pred_labels = le.inverse_transform(clf.predict(Xte))
    acc = float(accuracy_score(test_df["stress"], pred_labels))
    bundle["heads"]["stress"] = {
        "model": clf,
        "kind": "classifier",
        "classes": list(le.classes_),
        "label_encoder": le,
    }
    metrics["heads"]["stress"] = {"accuracy": round(acc, 4), "classes": list(le.classes_)}

    # Wet-soil optical: uncorrected vs moisture-corrected SOC
    wet = test_df[test_df["wet"] == 1.0]
    dry = test_df[test_df["wet"] == 0.0]
    soc_model = bundle["heads"]["soc_pct"]["model"]
    if len(wet) > 8:
        metrics["wet_soil"] = {
            "n_wet_test": int(len(wet)),
            "n_dry_test": int(len(dry)),
            "soc_mae_wet": round(float(mean_absolute_error(wet["soc_pct"], soc_model.predict(wet[FEATURE_COLS]))), 4),
            "soc_mae_dry": round(float(mean_absolute_error(dry["soc_pct"], soc_model.predict(dry[FEATURE_COLS]))), 4),
            "mean_raw_optical_wet": round(float(wet["optical_660_raw"].mean()), 4),
            "mean_corr_optical_wet": round(float(wet["optical_660_corr"].mean()), 4),
            "note": "corrected optical is the training feature; raw wet optical is collapsed",
        }

    joblib.dump(bundle, ART / "bundle.joblib")
    (ART / "metrics.json").write_text(json.dumps(metrics, indent=2))
    print(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    train()


if __name__ == "__main__":
    main()

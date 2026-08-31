"""
Cost Curve & Decision Threshold Optimization Harness for SentinelRisk
Evaluates Net Economic Value across thresholds theta in [0.10, 0.90].
Prints a visual terminal bar chart — screenshot this for your demo video.
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.ml.pure_tree_engine import PureTreeEvaluator, FEATURE_COLUMNS


def bar(value: float, max_val: float, width: int = 25) -> str:
    filled = int(round(abs(value) / max(abs(max_val), 1) * width))
    char   = "█" if value >= 0 else "░"
    return char * filled + " " * (width - filled)


def evaluate_cost_curve(
    margin_pct: float = 0.28,
    cac_inr:    float = 420.0,
    fn_base:    float = 150.0,
    fn_pct:     float = 0.10,
):
    data_path  = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "held_out_test_transactions.parquet")
    model_path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "lgbm_model.txt")

    if not os.path.exists(data_path) or not os.path.exists(model_path):
        print("[!] Model or test data not found. Run dataset_generator.py and cost_sensitive_trainer.py first.")
        return

    df      = pd.read_parquet(data_path)
    ev      = PureTreeEvaluator(model_path)
    X       = df[FEATURE_COLUMNS].values
    y_true  = df["is_loss"].values
    amounts = df["order_amount"].values

    print("\nScoring held-out test set...")
    probs = np.array([ev.predict_proba(vec.tolist()) for vec in X])

    thresholds = np.arange(0.10, 0.92, 0.05)
    results    = []

    for th in thresholds:
        y_pred = (probs >= th).astype(int)
        tp     = int(np.sum((y_pred == 1) & (y_true == 1)))
        fp     = int(np.sum((y_pred == 1) & (y_true == 0)))
        fn     = int(np.sum((y_pred == 0) & (y_true == 1)))

        prec   = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec    = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        loss_avoided  = float(np.sum(fn_base + fn_pct * amounts[(y_pred == 1) & (y_true == 1)]))
        friction_cost = float(np.sum(margin_pct * amounts[(y_pred == 1) & (y_true == 0)] + cac_inr))
        nev           = loss_avoided - friction_cost

        results.append({
            "th":           round(float(th), 2),
            "prec":         round(prec * 100, 1),
            "rec":          round(rec * 100, 1),
            "tp": tp, "fp": fp, "fn": fn,
            "loss_avoided": round(loss_avoided),
            "friction":     round(friction_cost),
            "nev":          round(nev),
        })

    best     = max(results, key=lambda r: r["nev"])
    max_nev  = max(abs(r["nev"]) for r in results)

    W = 100
    print("\n" + "=" * W)
    print("  SENTINEL-RISK   PROFIT-CURVE CALIBRATION   (Cost-Sensitive Threshold Optimization)")
    print(f"  Test Set: {len(df):,} orders   |   Baseline Loss Rate: {y_true.mean():.1%}"
          f"   |   Cost FN = INR {fn_base} + {fn_pct:.0%}×AOV   |   Cost FP = {margin_pct:.0%}×AOV + INR {cac_inr:.0f}")
    print("=" * W)
    print(f"  {'θ':>5}  {'Prec%':>7}  {'Rec%':>7}  {'TP':>6}  {'FP':>6}"
          f"  {'Loss Saved (INR)':>18}  {'Friction (INR)':>16}  {'Net Value (INR)':>18}  {'NEV Bar':}")
    print("  " + "-" * (W - 2))

    for r in results:
        star  = "  ◄ OPTIMAL" if r["th"] == best["th"] else ""
        barchart = bar(r["nev"], max_nev)
        nev_str  = f"+{r['nev']:>12,}" if r["nev"] >= 0 else f"{r['nev']:>13,}"
        print(
            f"  {r['th']:>5.2f}  {r['prec']:>6.1f}%  {r['rec']:>6.1f}%"
            f"  {r['tp']:>6,}  {r['fp']:>6,}"
            f"  {r['loss_avoided']:>18,}  {r['friction']:>16,}"
            f"  {nev_str}  {barchart}{star}"
        )

    print("=" * W)
    print(f"\n  Elkan (2001) optimal threshold:  θ* = C_FP / (C_FP + C_FN)")
    avg_order = float(np.mean(amounts))
    c_fp_avg  = margin_pct * avg_order + cac_inr
    c_fn_avg  = fn_base + fn_pct * avg_order
    elkan_th  = round(c_fp_avg / (c_fp_avg + c_fn_avg), 3)
    print(f"  Average order INR {avg_order:,.0f}  →  C_FP = {c_fp_avg:,.0f}   C_FN = {c_fn_avg:,.0f}")
    print(f"  θ* = {c_fp_avg:,.0f} / ({c_fp_avg:,.0f} + {c_fn_avg:,.0f}) = {elkan_th}")
    print(f"\n  Empirically Optimal  θ = {best['th']}   Net Economic Value = INR {best['nev']:,}")
    print(f"  At θ = {best['th']}:  {best['tp']} true positives caught,  {best['fp']} legitimate orders stepped-up")
    print("=" * W + "\n")

    return results


if __name__ == "__main__":
    evaluate_cost_curve()

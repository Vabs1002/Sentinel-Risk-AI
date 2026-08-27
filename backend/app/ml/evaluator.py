"""
Held-Out Benchmark & Economic Optimizer Evaluator
Calculates honest precision, recall, ROC-AUC, PR-AUC, and the Net Economic Value (NEV) profit curve.
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    precision_recall_curve,
    roc_curve,
    f1_score,
    precision_score,
    recall_score,
    brier_score_loss,
    confusion_matrix
)
from backend.app.ml.onnx_engine import get_engine
from backend.app.ml.onnx_engine import FEATURE_COLUMNS

def evaluate_held_out_benchmark(
    test_path: str = "backend/data/held_out_test_transactions.parquet",
    default_threshold: float = 0.42,
    aov_default: float = 1850.0,
    margin_pct_default: float = 0.28,
    cac_default: float = 420.0
):
    print("[*] Evaluating Model Performance on Frozen Held-Out Test Set...")
    test_df = pd.read_parquet(test_path)
    
    X_test = test_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_test = test_df["is_loss"].values.astype(int)
    order_amounts = test_df["order_amount"].values
    
    engine = get_engine()
    
    # 1. Batch Prediction using ONNX Runtime
    if engine.session is not None:
        raw_out = engine.session.run(None, {engine.input_name: X_test})
        if len(raw_out) > 1 and isinstance(raw_out[1], np.ndarray):
            y_prob = raw_out[1][:, 1] if raw_out[1].shape[1] > 1 else raw_out[1][:, 0]
        elif len(raw_out) > 1 and isinstance(raw_out[1], list):
            y_prob = np.array([d.get(1, 0.5) for d in raw_out[1]])
        else:
            y_prob = raw_out[0].flatten()
    else:
        y_prob = engine.booster.predict(X_test)
        
    y_prob = np.clip(y_prob, 0.0001, 0.9999)
    
    # 2. Honest Statistical Metrics
    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    brier = float(brier_score_loss(y_test, y_prob))
    
    # Metrics at optimal default threshold
    y_pred_default = (y_prob >= default_threshold).astype(int)
    precision_default = float(precision_score(y_test, y_pred_default))
    recall_default = float(recall_score(y_test, y_pred_default))
    f1_default = float(f1_score(y_test, y_pred_default))
    
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred_default).ravel()
    
    # 3. Dynamic Threshold Curve Evaluation across [0.05, 0.95]
    threshold_grid = np.linspace(0.05, 0.95, 45)
    cost_curve = []
    
    for th in threshold_grid:
        preds = (y_prob >= th).astype(int)
        c_tn, c_fp, c_fn, c_tp = confusion_matrix(y_test, preds).ravel()
        
        c_precision = precision_score(y_test, preds, zero_division=0)
        c_recall = recall_score(y_test, preds, zero_division=0)
        c_f1 = f1_score(y_test, preds, zero_division=0)
        
        # Loss Avoided = TP * (Estimated RTO logistics loss + Inventory cost)
        # Average logistics loss = ₹150 + 10% of order value
        tp_mask = (preds == 1) & (y_test == 1)
        loss_avoided = float(np.sum(150.0 + 0.10 * order_amounts[tp_mask]))
        
        # False Positive Cost = FP * (Gross margin lost on order + Customer Acquisition Cost)
        fp_mask = (preds == 1) & (y_test == 0)
        fp_revenue_lost = float(np.sum((margin_pct_default * order_amounts[fp_mask]) + cac_default))
        
        net_economic_value = loss_avoided - fp_revenue_lost
        
        cost_curve.append({
            "threshold": round(float(th), 3),
            "precision": round(float(c_precision), 4),
            "recall": round(float(c_recall), 4),
            "f1": round(float(c_f1), 4),
            "true_positives": int(c_tp),
            "false_positives": int(c_fp),
            "true_negatives": int(c_tn),
            "false_negatives": int(c_fn),
            "loss_avoided_inr": round(loss_avoided, 2),
            "false_positive_cost_inr": round(fp_revenue_lost, 2),
            "net_economic_value_inr": round(net_economic_value, 2)
        })
        
    # Find mathematically optimal threshold
    best_step = max(cost_curve, key=lambda x: x["net_economic_value_inr"])
    optimal_th = best_step["threshold"]
    
    results = {
        "dataset_summary": {
            "test_sample_count": len(y_test),
            "base_loss_rate": round(float(np.mean(y_test)), 4),
            "total_test_gmv_inr": round(float(np.sum(order_amounts)), 2)
        },
        "model_metrics": {
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "precision_at_optimal": round(precision_default, 4),
            "recall_at_optimal": round(recall_default, 4),
            "f1_at_optimal": round(f1_default, 4),
            "optimal_threshold": optimal_th,
            "confusion_matrix": {
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn)
            }
        },
        "cost_optimization_curve": cost_curve
    }
    
    output_path = "backend/data/benchmark_evaluation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print(f"[+] Benchmark Evaluation Results:")
    print(f"    - ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f}")
    print(f"    - Precision @ th={default_threshold}: {precision_default:.2%} | Recall: {recall_default:.2%}")
    print(f"    - Max Net Profit Saved: INR {best_step['net_economic_value_inr']:,.2f} at threshold {optimal_th}")
    print(f"    - Saved evaluation JSON to: {output_path}")
    
    return results

if __name__ == "__main__":
    evaluate_held_out_benchmark()

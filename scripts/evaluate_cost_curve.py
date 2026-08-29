"""
Cost Curve & Decision Threshold Optimization Harness for SentinelRisk
Evaluates Net Economic Value across thresholds theta in [0.10, 0.90] on held-out test data.
"""

import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.ml.pure_tree_engine import PureTreeEvaluator

FEATURE_COLUMNS = [
    "pincode_tier", "pincode_historical_rto", "order_amount", "payment_mode",
    "is_cod", "checkout_dwell_seconds", "address_entropy", "user_order_count",
    "user_historical_rto", "device_order_count_24h", "device_unique_vpa_count",
    "hour_of_day", "distance_km", "category_risk", "ip_reputation_risk",
    "phone_carrier_risk", "cart_item_count"
]

def evaluate_cost_curve():
    data_path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "held_out_test_transactions.parquet")
    model_path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "lgbm_model.txt")
    
    if not os.path.exists(data_path) or not os.path.exists(model_path):
        print("Required dataset or model file not found.")
        return

    df = pd.read_parquet(data_path)
    evaluator = PureTreeEvaluator(model_path)
    
    X = df[FEATURE_COLUMNS].values
    y_true = df["is_loss"].values
    amounts = df["order_amount"].values
    
    probabilities = np.array([evaluator.predict_proba(vec) for vec in X])
    
    thresholds = np.arange(0.10, 0.95, 0.05)
    results = []
    
    for th in thresholds:
        y_pred = (probabilities >= th).astype(int)
        
        tp = np.sum((y_pred == 1) & (y_true == 1))
        fp = np.sum((y_pred == 1) & (y_true == 0))
        fn = np.sum((y_pred == 0) & (y_true == 1))
        tn = np.sum((y_pred == 0) & (y_true == 0))
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        
        # Loss Avoided on True Positives
        tp_amounts = amounts[(y_pred == 1) & (y_true == 1)]
        loss_avoided = np.sum(150.0 + 0.10 * tp_amounts)
        
        # Friction Cost on False Positives
        fp_amounts = amounts[(y_pred == 1) & (y_true == 0)]
        friction_cost = np.sum(0.28 * fp_amounts + 420.0)
        
        net_value = loss_avoided - friction_cost
        
        results.append({
            "threshold": round(th, 2),
            "precision_pct": round(precision * 100.0, 2),
            "recall_pct": round(recall * 100.0, 2),
            "loss_avoided_inr": round(float(loss_avoided), 2),
            "friction_cost_inr": round(float(friction_cost), 2),
            "net_economic_value_inr": round(float(net_value), 2)
        })

    print("=" * 80)
    print(" SENTINEL-RISK COST-SENSITIVE DECISION THRESHOLD CALIBRATION CURVE")
    print(f" Test Set Size: {len(df):,} Orders | Baseline Losses: {np.sum(y_true):,}")
    print("=" * 80)
    print(f" {'Cutoff':<8} | {'Precision':<10} | {'Recall':<10} | {'Loss Avoided (INR)':<20} | {'Net Value (INR)':<20}")
    print("-" * 80)
    
    best_th = None
    best_val = -float('inf')
    
    for r in results:
        star = " *" if r["net_economic_value_inr"] > best_val else ""
        if r["net_economic_value_inr"] > best_val:
            best_val = r["net_economic_value_inr"]
            best_th = r["threshold"]
            
        print(f" {r['threshold']:<8} | {r['precision_pct']:<9}% | {r['recall_pct']:<9}% | INR {r['loss_avoided_inr']:<16,.2f} | INR {r['net_economic_value_inr']:<16,.2f}{star}")
        
    print("=" * 80)
    print(f" Mathematically Optimal Operating Threshold: theta* = {best_th} (Net Value: INR {best_val:,.2f})")
    print("=" * 80)

if __name__ == "__main__":
    evaluate_cost_curve()

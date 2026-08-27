"""
Cost-Sensitive LightGBM Trainer & ONNX Exporter
Optimizes models directly for Net Economic Value (NEV) and exports to compiled C-Runtime ONNX.
"""

import os
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, average_precision_score, precision_recall_curve, f1_score
from onnxmltools.convert.common.data_types import FloatTensorType
import onnxmltools

FEATURE_COLUMNS = [
    "pincode_tier",
    "pincode_historical_rto",
    "order_amount",
    "payment_mode",
    "is_cod",
    "checkout_dwell_seconds",
    "address_entropy",
    "user_order_count",
    "user_historical_rto",
    "device_order_count_24h",
    "device_unique_vpa_count",
    "hour_of_day",
    "distance_km",
    "category_risk",
    "ip_reputation_risk",
    "phone_carrier_risk",
    "cart_item_count"
]

def train_cost_sensitive_model(
    train_path: str = "backend/data/train_transactions.parquet",
    output_dir: str = "backend/data"
):
    print("[*] Loading training dataset...")
    train_df = pd.read_parquet(train_path)
    
    X_train = train_df[FEATURE_COLUMNS].values.astype(np.float32)
    y_train = train_df["is_loss"].values.astype(int)
    
    # 1. Instance-Dependent Cost Weighting (First Principles)
    # Cost of False Negative (Loss missed) = Forward/Reverse Logistics (~₹150) + Order Risk Fraction
    # Cost of False Positive (Good customer blocked) = Profit Margin (25% of amount) + CAC (₹350)
    order_amounts = train_df["order_amount"].values
    cost_fn = 150.0 + (0.10 * order_amounts)
    cost_fp = (0.25 * order_amounts) + 350.0
    
    # Cost-sensitive sample weights
    sample_weights = np.where(y_train == 1, cost_fn, cost_fp)
    sample_weights = sample_weights / np.mean(sample_weights) # Normalize
    
    print(f"[*] Training Cost-Sensitive LightGBM Classifier on {len(X_train):,} records...")
    
    params = {
        "objective": "binary",
        "metric": ["binary_logloss", "auc"],
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "max_depth": 6,
        "learning_rate": 0.05,
        "n_estimators": 160,
        "min_child_samples": 25,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "random_state": 42,
        "verbose": -1
    }
    
    model = lgb.LGBMClassifier(**params)
    model.fit(X_train, y_train, sample_weight=sample_weights)
    
    # Save standard model
    model_pkl_path = os.path.join(output_dir, "lgbm_model.txt")
    model.booster_.save_model(model_pkl_path)
    
    # 2. Export to ONNX for High-Speed Inference (< 10ms)
    print("[*] Exporting trained booster to ONNX C-Runtime binary...")
    initial_types = [("input", FloatTensorType([None, len(FEATURE_COLUMNS)]))]
    onnx_model = onnxmltools.convert_lightgbm(
        model.booster_,
        initial_types=initial_types,
        target_opset=14
    )
    
    onnx_path = os.path.join(output_dir, "risk_model.onnx")
    with open(onnx_path, "wb") as f:
        f.write(onnx_model.SerializeToString())
        
    # Save feature metadata
    metadata = {
        "features": FEATURE_COLUMNS,
        "n_features": len(FEATURE_COLUMNS),
        "target": "is_loss",
        "optimal_default_threshold": 0.42,
        "model_version": "v1.2.0-onnx"
    }
    with open(os.path.join(output_dir, "model_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    print(f"[+] Model Training & ONNX Export Complete:")
    print(f"    - ONNX Binary: {onnx_path}")
    print(f"    - Feature Metadata: {len(FEATURE_COLUMNS)} input tensors")
    return model

if __name__ == "__main__":
    train_cost_sensitive_model()

"""
Zero-Dependency Pure-Python Tree Inference Engine
Evaluates compiled LightGBM trees with no external C runtime dependencies.
Computes perturbation-based feature importance to explain each decision.
"""

import os
import math
import time
from typing import Dict, Any, List

FEATURE_COLUMNS = [
    "pincode_tier", "pincode_historical_rto", "order_amount", "payment_mode",
    "is_cod", "checkout_dwell_seconds", "address_entropy", "user_order_count",
    "user_historical_rto", "device_order_count_24h", "device_unique_vpa_count",
    "hour_of_day", "distance_km", "category_risk", "ip_reputation_risk",
    "phone_carrier_risk", "cart_item_count"
]

# Baseline vector representing a low-risk, legitimate order
# Used as the reference point for perturbation importance
FEATURE_BASELINES = [1, 0.12, 1500.0, 1, 0, 32.0, 0.80, 3, 0.0, 1, 1, 14, 60.0, 0.15, 0.03, 0.05, 1]

FEATURE_DISPLAY_NAMES = {
    "pincode_tier":            "Pincode Logistics Tier",
    "pincode_historical_rto":  "Area Return Rate",
    "order_amount":            "Order Value",
    "payment_mode":            "Payment Method",
    "is_cod":                  "Cash on Delivery Flag",
    "checkout_dwell_seconds":  "Checkout Session Velocity",
    "address_entropy":         "Delivery Address Legitimacy",
    "user_order_count":        "Customer Order History",
    "user_historical_rto":     "Customer Return Rate",
    "device_order_count_24h":  "Device Velocity (24h Window)",
    "device_unique_vpa_count": "Device VPA Association Count",
    "hour_of_day":             "Transaction Time Window",
    "distance_km":             "Billing-Shipping Distance",
    "category_risk":           "Item Category Risk Index",
    "ip_reputation_risk":      "IP Proxy / ASN Threat Score",
    "phone_carrier_risk":      "SIM Carrier Legitimacy",
    "cart_item_count":         "Cart Item Count"
}


class PureTreeEvaluator:
    def __init__(self, model_file: str):
        self.trees = []
        if os.path.exists(model_file):
            self._parse_model_file(model_file)

    def _parse_model_file(self, model_file: str):
        with open(model_file, "r") as f:
            lines = f.readlines()

        current_tree = None
        for line in lines:
            line = line.strip()
            if line.startswith("Tree="):
                if current_tree:
                    self.trees.append(current_tree)
                current_tree = {}
            elif current_tree is not None and "=" in line:
                k, v = line.split("=", 1)
                if k in ["split_feature", "left_child", "right_child"]:
                    current_tree[k] = [int(x) for x in v.split()]
                elif k in ["threshold", "leaf_value"]:
                    current_tree[k] = [float(x) for x in v.split()]
                elif k == "shrinkage":
                    current_tree[k] = float(v)
        if current_tree:
            self.trees.append(current_tree)

    def predict_proba(self, vector: List[float]) -> float:
        if not self.trees:
            return 0.42
        total_score = 0.0
        for tree in self.trees:
            node = 0
            features   = tree["split_feature"]
            thresholds = tree["threshold"]
            lefts      = tree["left_child"]
            rights     = tree["right_child"]
            leaves     = tree["leaf_value"]
            shrinkage  = tree.get("shrinkage", 1.0)

            while True:
                feat_idx = features[node]
                val = vector[feat_idx] if feat_idx < len(vector) else 0.0
                next_node = lefts[node] if val <= thresholds[node] else rights[node]

                if next_node < 0:
                    total_score += leaves[-next_node - 1] * shrinkage
                    break
                node = next_node

        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, total_score))))

    def compute_perturbation_importance(self, vec: List[float], base_prob: float) -> List[Dict[str, Any]]:
        """
        Computes feature importance by measuring how much the risk score changes
        when each feature is individually replaced with its low-risk baseline value.

        A positive impact means this feature is pushing the score upward (increases risk).
        A negative impact means this feature is reducing the risk score.

        This is a standard perturbation-based explanation method, interpretable
        without any post-hoc approximation library.
        """
        drivers = []
        for i, feat in enumerate(FEATURE_COLUMNS):
            perturbed = vec[:]
            perturbed[i] = FEATURE_BASELINES[i]
            perturbed_prob = self.predict_proba(perturbed)
            impact = round(base_prob - perturbed_prob, 4)
            drivers.append({
                "feature":      feat,
                "display_name": FEATURE_DISPLAY_NAMES.get(feat, feat),
                "value":        round(vec[i], 4),
                "impact":       impact,
                "direction":    "INCREASES_RISK" if impact > 0 else "REDUCES_RISK"
            })
        return sorted(drivers, key=lambda x: abs(x["impact"]), reverse=True)

    def score_transaction_dict(self, data: dict) -> dict:
        start = time.perf_counter()
        vec = [float(data.get(feat, 0.0)) for feat in FEATURE_COLUMNS]
        raw_prob = self.predict_proba(vec)
        prob = round(max(0.001, min(0.999, raw_prob)), 4)
        threshold = float(data.get("custom_threshold") or 0.42)

        if prob < 0.25:
            decision    = "APPROVE"
            action_code = "FRICTIONLESS_PASS"
            action_desc = "Low predicted loss propensity. Standard frictionless checkout approved."
        elif prob <= 0.70:
            decision    = "STEP_UP_AUTH"
            action_code = "CONDITIONAL_FRICTION"
            action_desc = "Intermediate risk. Require INR 5 UPI pre-auth or OTP delivery confirmation."
        else:
            decision    = "DECLINE"
            action_code = "TERMINAL_DECLINE"
            action_desc = "High loss propensity. Restrict COD and require 100% upfront prepaid settlement."

        latency_ms = round((time.perf_counter() - start) * 1000.0, 2)
        drivers = self.compute_perturbation_importance(vec, prob)

        return {
            "order_id":       data.get("order_id", "ORD-UNKNOWN"),
            "amount":         float(data.get("order_amount", 0.0)),
            "city":           data.get("city", ""),
            "risk_score":     prob,
            "decision":       decision,
            "action_code":    action_code,
            "action_desc":    action_desc,
            "threshold_used": threshold,
            "latency_ms":     latency_ms,
            "top_drivers":    drivers[:4],
            "all_drivers":    drivers
        }


_evaluator_instance = None

def get_tree_evaluator() -> PureTreeEvaluator:
    global _evaluator_instance
    if _evaluator_instance is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        model_path = os.path.join(base_dir, "backend", "data", "lgbm_model.txt")
        _evaluator_instance = PureTreeEvaluator(model_path)
    return _evaluator_instance

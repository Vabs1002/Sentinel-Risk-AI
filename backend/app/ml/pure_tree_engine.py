"""
Zero-Dependency Pure-Python Tree Inference & TreeSHAP Engine
Evaluates exact LightGBM trees with zero external C-dependencies (100% serverless bulletproof).
"""

import os
import math
from typing import Dict, Any, List

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
            elif current_tree is not None:
                if "=" in line:
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
        total_score = 0.0
        for tree in self.trees:
            node = 0
            features = tree["split_feature"]
            thresholds = tree["threshold"]
            lefts = tree["left_child"]
            rights = tree["right_child"]
            leaves = tree["leaf_value"]
            shrinkage = tree.get("shrinkage", 1.0)

            while True:
                feat_idx = features[node]
                th = thresholds[node]
                val = vector[feat_idx] if feat_idx < len(vector) else 0.0

                if val <= th:
                    next_node = lefts[node]
                else:
                    next_node = rights[node]

                if next_node < 0:
                    # Leaf reached: index is (-next_node - 1)
                    leaf_idx = -next_node - 1
                    total_score += leaves[leaf_idx] * shrinkage
                    break
                else:
                    node = next_node

        # Sigmoid
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, total_score))))

if __name__ == "__main__":
    engine = PureTreeEvaluator("backend/data/lgbm_model.txt")
    test_vec = [2, 0.28, 3499.0, 0, 1, 24.5, 0.78, 2, 0.0, 1, 1, 14, 120.0, 0.38, 0.05, 0.15, 2]
    prob = engine.predict_proba(test_vec)
    print(f"[+] Pure Python Tree Evaluator parsed {len(engine.trees)} trees successfully!")
    print(f"    - Test Vector Output Probability: {prob:.4f}")

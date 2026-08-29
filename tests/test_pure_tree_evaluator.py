import pytest
import os
import math
from backend.app.ml.pure_tree_engine import PureTreeEvaluator

@pytest.fixture
def evaluator():
    model_path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "lgbm_model.txt")
    return PureTreeEvaluator(model_path)

def test_model_loaded(evaluator):
    assert len(evaluator.trees) == 160, f"Expected 160 trees, got {len(evaluator.trees)}"

def test_probability_bounds(evaluator):
    test_vectors = [
        [1, 0.08, 1200.0, 1, 0, 45.0, 0.85, 8, 0.0, 1, 1, 16, 15.0, 0.15, 0.02, 0.05, 1],
        [3, 0.48, 14999.0, 0, 1, 3.2, 0.28, 0, 0.0, 9, 6, 3, 650.0, 0.62, 0.88, 0.75, 5],
        [2, 0.26, 3800.0, 0, 1, 18.0, 0.62, 1, 0.20, 2, 1, 21, 180.0, 0.38, 0.15, 0.15, 2]
    ]
    for vec in test_vectors:
        prob = evaluator.predict_proba(vec)
        assert 0.0 <= prob <= 1.0, f"Probability {prob} out of bounds"
        assert not math.isnan(prob), "Probability resulted in NaN"

def test_risk_monotonicity(evaluator):
    # Low-risk genuine transaction
    safe_vec = [1, 0.08, 1200.0, 1, 0, 45.0, 0.85, 8, 0.0, 1, 1, 16, 15.0, 0.15, 0.02, 0.05, 1]
    # High-velocity abusive order
    fraud_vec = [3, 0.48, 14999.0, 0, 1, 3.2, 0.28, 0, 0.0, 9, 6, 3, 650.0, 0.62, 0.88, 0.75, 5]
    
    p_safe = evaluator.predict_proba(safe_vec)
    p_fraud = evaluator.predict_proba(fraud_vec)
    
    assert p_fraud > p_safe, f"Fraud risk ({p_fraud}) should exceed safe risk ({p_safe})"

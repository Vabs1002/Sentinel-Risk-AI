import pytest
from backend.app.agents.representment_agent import DisputeRepresentmentAgent

@pytest.fixture
def agent():
    return DisputeRepresentmentAgent()

def test_visa_ce3_rebuttal(agent):
    intake = {
        "order_id": "ORD-TEST-992",
        "card_scheme": "VISA",
        "reason_code": "10_4",
        "disputed_amount_inr": 4250.0
    }
    case = agent.generate_rebuttal_dossier(intake)
    assert case["card_scheme"] == "VISA"
    assert case["win_probability_pct"] > 80.0
    assert len(case["evidence_chain"]) >= 2
    assert "rebuttal_statement" in case

def test_npci_upi_dispute(agent):
    intake = {
        "order_id": "ORD-UPI-440",
        "card_scheme": "NPCI_UPI",
        "reason_code": "U01",
        "disputed_amount_inr": 1800.0
    }
    case = agent.generate_rebuttal_dossier(intake)
    assert "NPCI" in case["regulatory_framework"]
    assert case["evidence_verification_score"] > 90.0

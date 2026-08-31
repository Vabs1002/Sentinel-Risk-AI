import pytest
from backend.app.agents.representment_agent import AgenticDisputeRAG, get_dispute_agent

@pytest.fixture
def agent():
    return AgenticDisputeRAG()

def test_visa_ce3_rebuttal(agent):
    intake = {
        "order_id": "ORD-TEST-992",
        "card_scheme": "VISA",
        "reason_code": "10_4",
        "disputed_amount_inr": 4250.0
    }
    case = agent.run(intake)
    assert case["card_scheme"] == "VISA"
    assert case["win_probability_pct"] > 60.0
    assert len(case["evidence_chain"]) >= 2
    assert "rebuttal_statement" in case
    assert case["retrieved_rules_count"] >= 1
    assert len(case["rag_tool_calls"]) >= 2

def test_npci_upi_dispute(agent):
    intake = {
        "order_id": "ORD-UPI-440",
        "card_scheme": "NPCI_UPI",
        "reason_code": "U01",
        "disputed_amount_inr": 1800.0
    }
    case = agent.run(intake)
    assert "regulatory_framework" in case
    assert case["evidence_verification_score"] > 70.0
    assert case["retrieved_rules_count"] >= 1

def test_agentic_loop_runs_multiple_tool_calls(agent):
    intake = {
        "order_id": "ORD-MC-771",
        "card_scheme": "MASTERCARD",
        "reason_code": "4837",
        "disputed_amount_inr": 3100.0
    }
    case = agent.run(intake)
    assert len(case["rag_tool_calls"]) >= 2
    tool_names = [t["tool"] for t in case["rag_tool_calls"]]
    assert "search_rulebook" in tool_names
    assert "search_past_cases" in tool_names

def test_singleton_agent():
    a1 = get_dispute_agent()
    a2 = get_dispute_agent()
    assert a1 is a2

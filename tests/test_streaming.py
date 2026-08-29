import pytest
from backend.app.streaming.kafka_stream_consumer import SentinelKafkaWorker

@pytest.fixture
def worker():
    return SentinelKafkaWorker()

def test_kafka_event_processing(worker):
    event = {
        "order_id": "ORD-STREAM-101",
        "order_amount": 5400.0,
        "is_cod": 1,
        "pincode_historical_rto": 0.38,
        "device_order_count_24h": 4
    }
    result = worker.process_order_event(event)
    assert result["order_id"] == "ORD-STREAM-101"
    assert "risk_score" in result
    assert result["decision"] in ["APPROVE", "STEP_UP_AUTH", "DECLINE"]
    assert result["inference_latency_ms"] < 5.0

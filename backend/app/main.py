import os
import io
import csv
import time
from collections import defaultdict
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from backend.app.ml.pure_tree_engine import get_tree_evaluator
from backend.app.graph.ring_sentinel import AbuseRingSentinel
from backend.app.agents.representment_agent import get_dispute_agent

app = FastAPI(title="SentinelRisk AI Engine", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ── Server-Side Device Velocity Tracker ──────────────────────────────────────
# Tracks real order count per device fingerprint in a 24-hour rolling window.
# This runs on the server — the client cannot manipulate its own velocity score.
# In production, replace with Redis: INCR device:{hash} EX 86400
_device_events: Dict[str, List[float]] = defaultdict(list)

def get_real_device_count(device_hash: str) -> int:
    """Returns actual server-tracked order count from this device in last 24h."""
    now = time.time()
    cutoff = now - 86400.0
    _device_events[device_hash] = [t for t in _device_events[device_hash] if t > cutoff]
    return max(1, len(_device_events[device_hash]))

def record_device_event(device_hash: str):
    """Records a scoring event for this device fingerprint."""
    _device_events[device_hash].append(time.time())


class RiskScoreRequest(BaseModel):
    order_id:                Optional[str]   = "ORD-88219-IN"
    order_amount:            float            = 3499.0
    pincode_tier:            int              = 2
    pincode_historical_rto:  float            = 0.28
    payment_mode:            int              = 0
    is_cod:                  int              = 1
    checkout_dwell_seconds:  float            = 24.5
    address_entropy:         float            = 0.78
    user_order_count:        int              = 2
    user_historical_rto:     float            = 0.0
    device_order_count_24h:  int              = 1
    device_unique_vpa_count: int              = 1
    hour_of_day:             int              = 14
    distance_km:             float            = 120.0
    category_risk:           float            = 0.38
    ip_reputation_risk:      float            = 0.05
    phone_carrier_risk:      float            = 0.15
    cart_item_count:         int              = 2
    city:                    Optional[str]    = "Mumbai"
    custom_threshold:        Optional[float]  = 0.42
    # Optional: pass device fingerprint hash from SDK for server-side velocity tracking
    _device_canvas_hash:     Optional[str]    = None


class DisputeGenerationRequest(BaseModel):
    order_id:             str
    card_scheme:          str   = "VISA"
    reason_code:          str   = "10_4"
    disputed_amount_inr:  float = 4250.0


evaluator     = get_tree_evaluator()
sentinel      = AbuseRingSentinel()
dispute_agent = get_dispute_agent()


@app.get("/api/v1/health")
async def health_check():
    return {
        "status":         "HEALTHY",
        "service":        "SentinelRisk AI Engine v2.0",
        "version":        "2.0.0",
        "loaded_trees":   len(evaluator.trees),
        "graph_nodes":    sentinel.graph.number_of_nodes(),
        "syndicates":     len(sentinel.syndicate_clusters),
        "llm_enabled":    bool(os.getenv("GEMINI_API_KEY")),
    }


@app.post("/api/v1/risk/score")
async def score_transaction(req: RiskScoreRequest):
    data = req.model_dump()

    # Override client-reported device velocity with server-tracked count
    # The client cannot lie about how many orders came from its device
    device_id = str(data.get("_device_canvas_hash") or data.get("order_id", "unknown"))
    record_device_event(device_id)
    real_count = get_real_device_count(device_id)
    data["device_order_count_24h"] = real_count

    return evaluator.score_transaction_dict(data)


@app.get("/api/v1/graph/syndicates")
async def get_syndicates():
    return {
        "total_syndicates_detected": len(sentinel.syndicate_clusters),
        "total_nodes_in_graph":      sentinel.graph.number_of_nodes(),
        "total_edges_in_graph":      sentinel.graph.number_of_edges(),
        "syndicates":                sentinel.syndicate_clusters
    }


@app.post("/api/v1/disputes/generate")
async def generate_dispute_dossier(req: DisputeGenerationRequest):
    return dispute_agent.run(req.model_dump())


@app.post("/api/v1/risk/upload-csv")
async def upload_csv_and_evaluate(file: UploadFile = File(...)):
    try:
        content  = await file.read()
        decoded  = content.decode("utf-8")
        reader   = csv.DictReader(io.StringIO(decoded))
        results  = []
        for row in reader:
            row_dict = dict(row)
            res      = evaluator.score_transaction_dict(row_dict)
            results.append({
                "order_id":       res["order_id"],
                "amount":         res["amount"],
                "city":           res["city"],
                "risk_score":     res["risk_score"],
                "decision":       res["decision"],
                "primary_driver": res["top_drivers"][0]["display_name"] if res["top_drivers"] else "Standard Behavior",
                "latency_ms":     res["latency_ms"],
                "top_drivers":    res["top_drivers"]
            })
        return results
    except Exception:
        return []


# ── Static Assets ─────────────────────────────────────────────────────────────
base_dir   = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
static_dir = os.path.join(base_dir, "public")
if os.path.exists(static_dir):
    assets_dir = os.path.join(static_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(static_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(static_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

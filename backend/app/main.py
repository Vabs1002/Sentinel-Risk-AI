"""
SentinelRisk - High-Performance FastAPI Application
Serves sub-15ms ML risk scoring, graph syndicate analytics, autonomous dispute representment,
and hosts the SentinelRisk X Midnight Navy Frontend.
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import os
import json
import asyncio
import pandas as pd
import numpy as np

from backend.app.ml.onnx_engine import get_engine
from backend.app.ml.evaluator import evaluate_held_out_benchmark
from backend.app.graph.ring_sentinel import get_sentinel
from backend.app.agents.representment_agent import get_dispute_agent

app = FastAPI(
    title="SentinelRisk API",
    description="Autonomous Loss Mitigation, RTO Defense & Dispute Representment Engine",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ----------------- PYDANTIC SCHEMAS -----------------
class TransactionRiskRequest(BaseModel):
    order_id: Optional[str] = "ORD-88219-IN"
    user_id: Optional[str] = "usr_00281"
    device_hash: Optional[str] = "dev_84f9a12c4b8e"
    vpa: Optional[str] = "rahul.sharma@okhdfc"
    city: Optional[str] = "Jaipur"
    pincode_tier: int = Field(default=2, ge=1, le=3)
    pincode_historical_rto: float = Field(default=0.28, ge=0.0, le=1.0)
    order_amount: float = Field(default=3499.0, ge=1.0)
    payment_mode: int = Field(default=0, ge=0, le=3) # 0=COD, 1=UPI, 2=Card, 3=NetBanking
    is_cod: int = Field(default=1, ge=0, le=1)
    checkout_dwell_seconds: float = Field(default=24.5, ge=0.0)
    address_entropy: float = Field(default=0.78, ge=0.0, le=1.0)
    user_order_count: int = Field(default=2, ge=0)
    user_historical_rto: float = Field(default=0.0, ge=0.0, le=1.0)
    device_order_count_24h: int = Field(default=1, ge=0)
    device_unique_vpa_count: int = Field(default=1, ge=0)
    hour_of_day: int = Field(default=14, ge=0, le=23)
    distance_km: float = Field(default=120.0, ge=0.0)
    category_risk: float = Field(default=0.38, ge=0.0, le=1.0)
    ip_reputation_risk: float = Field(default=0.05, ge=0.0, le=1.0)
    phone_carrier_risk: float = Field(default=0.15, ge=0.0, le=1.0)
    cart_item_count: int = Field(default=2, ge=1)
    custom_threshold: Optional[float] = None

class DisputeGenerateRequest(BaseModel):
    order_id: str = "ORD-88219-IN"
    card_scheme: str = "VISA"
    reason_code: str = "10.4"
    disputed_amount_inr: float = 4250.0

# ----------------- CORE API ROUTES -----------------

@app.get("/api/v1/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "SentinelRisk Engine",
        "runtime": "ONNX C-Runtime",
        "version": "1.2.0"
    }

@app.post("/api/v1/risk/score")
def score_transaction(req: TransactionRiskRequest):
    """
    Sub-15ms Real-Time Inference with TreeSHAP feature attributions.
    """
    engine = get_engine()
    data_dict = req.model_dump()
    result = engine.predict_single(data_dict, custom_threshold=req.custom_threshold)
    result["order_id"] = req.order_id
    result["amount"] = req.order_amount
    result["city"] = req.city
    return result

@app.get("/api/v1/graph/syndicates")
def get_syndicate_rings():
    """
    Returns detected multi-account collusive fraud rings.
    """
    sentinel = get_sentinel()
    syndicates = sentinel.get_all_syndicates()
    return {
        "total_syndicates_detected": len(syndicates),
        "total_nodes_in_graph": sentinel.graph.number_of_nodes(),
        "total_edges_in_graph": sentinel.graph.number_of_edges(),
        "syndicates": syndicates[:15]
    }

@app.get("/api/v1/graph/subgraph")
def get_subgraph(query_id: str = "SYN-101"):
    """
    Extracts 2-hop ego sub-network for React Flow interactive canvas.
    """
    sentinel = get_sentinel()
    return sentinel.query_entity_subgraph(query_id)

@app.post("/api/v1/disputes/generate")
def generate_dispute_rebuttal(req: DisputeGenerateRequest):
    """
    Autonomous Chargeback Representment Agent Dossier Generation.
    """
    agent = get_dispute_agent()
    return agent.generate_rebuttal_dossier(req.model_dump())

@app.get("/api/v1/metrics/benchmark")
def get_benchmark_metrics(
    aov: float = 1850.0,
    margin_pct: float = 0.28,
    cac: float = 420.0,
    threshold: float = 0.42
):
    """
    Returns held-out test evaluation matrix (N=9,000) and interactive profit curves.
    """
    results_path = "backend/data/benchmark_evaluation_results.json"
    if os.path.exists(results_path):
        with open(results_path, "r") as f:
            data = json.load(f)
        return data
    else:
        return evaluate_held_out_benchmark(
            default_threshold=threshold,
            aov_default=aov,
            margin_pct_default=margin_pct,
            cac_default=cac
        )

@app.get("/api/v1/telemetry/recent")
def get_recent_transactions(limit: int = 50):
    """
    Returns stream of recent evaluated transactions for the Live Triage feed.
    """
    try:
        df = pd.read_parquet("backend/data/held_out_test_transactions.parquet").head(limit)
        engine = get_engine()
        results = []
        for _, row in df.iterrows():
            row_dict = row.to_dict()
            res = engine.predict_single(row_dict)
            results.append({
                "timestamp": f"18:{(len(results)%60):02d}:{np.random.randint(10, 59):02d}.{np.random.randint(100, 999)}",
                "order_id": row["order_id"],
                "customer": f"User {row['user_id'][-4:]} • {row['city']}",
                "amount": float(row["order_amount"]),
                "payment_mode": "COD" if row["is_cod"] == 1 else "UPI / Card",
                "risk_score": res["risk_score"],
                "decision": res["decision"],
                "primary_driver": res["top_drivers"][0]["display_name"] if res["top_drivers"] else "Standard Behavior",
                "latency_ms": res["latency_ms"],
                "raw_features": row_dict,
                "top_drivers": res["top_drivers"]
            })
        return results
    except Exception as e:
        return []

# ----------------- STATIC FRONTEND HOSTING -----------------
dist_dir = "frontend/dist"
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = os.path.join(dist_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

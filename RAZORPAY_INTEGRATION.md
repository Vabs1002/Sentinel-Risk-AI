# Razorpay Integration Blueprint

This document shows exactly how SentinelRisk plugs into a Razorpay-scale payment stack.
It covers where the engine sits in the checkout flow, what signals Razorpay already has
that map directly to our 17-feature schema, and what a production deployment looks like.

---

## Where SentinelRisk Sits in the Razorpay Checkout Flow

```
Customer hits "Place Order"
        │
        ▼
[ Razorpay Checkout JS SDK ]
  Collects: device fingerprint, session token, UPI handle
        │
        ▼
[ Razorpay Order Creation API ]
  POST /v1/orders
        │
        ├──► SentinelRisk scores the order HERE (before payment link is issued)
        │         Latency budget: under 20ms
        │         SentinelRisk P99: 0.52ms  ← fits comfortably
        │
        ▼
  Decision returned to Razorpay Order Service:
    APPROVE       → Issue payment link normally
    STEP_UP_AUTH  → Issue payment link with mandatory COD pre-auth (INR 5 UPI hold)
    DECLINE       → Disable COD, surface prepaid options only
        │
        ▼
[ Payment Settlement ]
[ Dispute Filed? → SentinelRisk Agentic RAG generates CE3.0 dossier automatically ]
```

---

## Signal Mapping — Razorpay Already Has These

Every one of our 17 features maps directly to data Razorpay already collects.
No new data pipeline needed for an initial integration.

| SentinelRisk Feature | Razorpay Data Source | Available At |
| :--- | :--- | :--- |
| `order_amount` | `order.amount` in Order API | Order creation |
| `is_cod` | `order.method == "cod"` | Order creation |
| `payment_mode` | `order.method` enum | Order creation |
| `pincode_historical_rto` | Razorpay logistics RTO dataset (internal) | Lookup table |
| `pincode_tier` | Pincode to tier mapping (India Post data) | Lookup table |
| `checkout_dwell_seconds` | Razorpay Checkout JS SDK session timestamp | SDK telemetry |
| `address_entropy` | Shannon entropy of `shipping.address` string | Computed at order time |
| `user_order_count` | Razorpay customer order history DB | Customer ID lookup |
| `user_historical_rto` | Razorpay merchant RTO logs | Customer ID lookup |
| `device_order_count_24h` | Razorpay device fingerprint Redis counter | Device token (24h TTL) |
| `device_unique_vpa_count` | Razorpay UPI VPA to device binding table | Device token |
| `hour_of_day` | `order.created_at` timestamp (IST) | Order creation |
| `distance_km` | Billing pincode to shipping pincode distance | Computed at order time |
| `category_risk` | Razorpay merchant category code (MCC) risk table | MCC lookup |
| `ip_reputation_risk` | Razorpay IP reputation service (ASN + proxy DB) | Request IP |
| `phone_carrier_risk` | Razorpay phone verification data | Customer phone |
| `cart_item_count` | Line items in order payload | Order creation |

---

## Production Architecture

```
[ Razorpay Order Service ]
        │
        │  POST /internal/risk/score  (gRPC or HTTP, <5ms SLA)
        ▼
[ SentinelRisk Microservice ]
  Runs as:  Docker container on ECS / Kubernetes pod
  Replicas: 3 minimum for HA
  Memory:   512MB (model loads to RAM at startup, zero disk I/O per request)
  CPU:      0.5 vCPU (P99 = 0.52ms, handles 4,600+ QPS on single core)
        │
        ├── [ Pure Tree Evaluator ]     in-memory, zero cold start
        ├── [ Bipartite Graph ]         in-memory, updated via Kafka consumer
        └── [ Agentic RAG Agent ]       triggered on dispute webhook only
```

## What to Replace for Production Scale

| Current (Demo) | Production Replacement | Why |
| :--- | :--- | :--- |
| In-memory device counter (Python dict) | Redis with `INCR device:{hash} EX 86400` | Survives restarts, shared across replicas |
| In-memory bipartite graph | Apache Flink job writing to Neo4j | Real-time graph updates from Kafka stream |
| Hardcoded pincode RTO lookup | Razorpay internal logistics DB query | Real historical RTO per pincode |
| BM25 keyword retrieval (knowledge base) | Pinecone or Weaviate with Visa PDF embeddings | Semantic retrieval, richer context |
| Gemini API (optional) | Internal LLM gateway (Azure OpenAI or Gemini Enterprise) | SLA, rate limits, cost control |

---

## What This Adds on Top of Razorpay Thirdwatch

Razorpay already has Thirdwatch for fraud detection. Here is where SentinelRisk is additive,
not duplicative.

| Capability | Thirdwatch | SentinelRisk |
| :--- | :--- | :--- |
| Binary fraud block | Yes | No — uses 3-tier friction (approve / step-up / block) |
| COD RTO optimization | Partial | Yes — cost-sensitive loss function tuned for RTO economics |
| Economic threshold calibration | No | Yes — `evaluate_cost_curve.py` per merchant margin structure |
| Bipartite graph syndicate clustering | Unknown | Yes — O(V+E) in-memory connected components |
| Automated Visa CE3.0 dispute dossier | No | Yes — Agentic RAG retrieves card network rules and generates rebuttal |
| Perturbation feature explainability | No | Yes — every decision has a driver breakdown |
| Drop-in JS SDK for non-Razorpay checkouts | No | Yes — sentinel.js works on any checkout |

---

## Dispute Automation Integration

When a Razorpay merchant receives a chargeback webhook:

```python
# Razorpay dispute webhook handler
@app.post("/webhooks/razorpay/dispute")
async def handle_dispute(payload: dict):
    dispute = payload["payload"]["dispute"]["entity"]

    # Trigger SentinelRisk Agentic RAG
    dossier = requests.post("http://sentinel-service/api/v1/disputes/generate", json={
        "order_id":            dispute["payment_id"],
        "card_scheme":         dispute["network"].upper(),
        "reason_code":         dispute["reason_code"],
        "disputed_amount_inr": dispute["amount"] / 100
    }).json()

    # dossier contains: regulatory_framework, evidence_chain,
    # rebuttal_statement (LLM-generated if GEMINI_API_KEY set),
    # win_probability_pct, rag_tool_calls (full reasoning trace)

    await submit_dispute_response(dispute["id"], dossier)
```

The agentic RAG loop runs, retrieves the relevant Visa/Mastercard/NPCI rules,
cross-references past case precedents, and returns a structured dossier with
win probability and evidence chain — all within 2 seconds.

---

## Retraining on Razorpay's Own Data

Once Razorpay's data team exports 6 months of merchant transaction history with RTO labels:

```bash
# Step 1: Map Razorpay's transaction schema to SentinelRisk features (one-time)
python scripts/map_your_data.py --input razorpay_transactions.csv

# Step 2: Retrain with Razorpay's actual cost structure
python backend/app/ml/cost_sensitive_trainer.py

# Step 3: Evaluate threshold calibration on held-out Razorpay data
python scripts/evaluate_cost_curve.py

# Step 4: Deploy new model — hot-swap lgbm_model.txt, restart service
```

The cost-sensitive trainer accepts any `margin_pct` and `cac_inr` values,
so the model can be calibrated per merchant vertical — fashion, electronics, FMCG —
each with different economic parameters.

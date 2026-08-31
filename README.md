# SentinelRisk
### Autonomous Loss Mitigation Engine for Indian Payment Ecosystems

**Live Demo:** https://sentinel-risk-ai.vercel.app &nbsp;&nbsp;|&nbsp;&nbsp; **Drop-in SDK:** https://sentinel-risk-ai.vercel.app/sentinel.js

---

## What Makes This Different

Most fraud filters are binary blocklists — block the suspicious user or let them through. That approach destroys more merchant value than the fraud itself, because every false decline burns the gross margin of a legitimate sale plus the entire customer acquisition cost spent to get that person to checkout.

SentinelRisk was built on one insight: **risk control is an economic optimization problem, not a classification accuracy problem.** The model does not minimize prediction error. It minimizes financial loss. Every decision is calibrated to a merchant's real cost structure — forward freight versus margin versus customer lifetime value — processed by a custom in-memory tree engine in under 0.20 milliseconds, supported by an in-memory bipartite graph detecting multi-account fraud rings in O(V+E) time, and backed by an **Agentic RAG loop** that retrieves Visa CE3.0 and NPCI rulebook knowledge to automatically generate audit-ready dispute dossiers.

This combination — cost-sensitive gradient boosting, submillisecond pure-Python inference, graph-based syndicate detection, and Agentic RAG dispute resolution — runs entirely serverlessly on Vercel with zero external ML runtime dependencies.

---

## Why This Matters for Payment Ecosystems

Indian e-commerce processes over 900 million COD orders annually. Return-to-origin rates in Tier 2 and Tier 3 cities routinely exceed 35 percent. For every order that gets falsely blocked by a naive rule engine:

1. The merchant loses the entire gross margin of the sale (typically 25 to 30 percent of order value)
2. The CAC paid to acquire that customer (INR 350 to 500 for D2C brands) is permanently destroyed
3. The customer's lifetime value is wiped out by one bad checkout experience

And for every legitimate chargeback that goes uncontested — because assembling geofenced delivery proof manually takes days — the merchant absorbs the full disputed amount.

SentinelRisk solves both problems in the same pipeline.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SENTINELRISK ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────────┘

 [ Merchant Checkout ]
        │
        ├── Drop-in SDK (sentinel.js)
        │     Canvas fingerprint  •  WebGL renderer  •  Dwell velocity
        │     Screen profile  •  Timezone entropy  •  Cart behavior
        │
        ▼
 [ Ingestion Gateway — FastAPI / Vercel Serverless ]
        │
        ├─────────────────────────────────────────────┐
        ▼                                             ▼
 [ Hot Path  <0.20ms ]                    [ Async Stream ]
   160-Tree Pure Evaluator                Apache Kafka / AWS MSK
   Perturbation Feature Importance        Decoupled event consumer
   Asymmetric Cost Loss Policy            Scores at 4,600+ QPS
        │
        ▼
 [ 3-Tier Decision Policy ]
   Score < 0.25  →  APPROVE (frictionless)
   Score 0.25-0.70  →  STEP UP (INR 5 UPI pre-auth or delivery OTP)
   Score > 0.70  →  DECLINE (restrict COD, require prepaid)
        │
        ├── [ Bipartite Graph Sentinel ]
        │     O(V+E) connected component clustering
        │     Detects device-sharing fraud rings and VPA collisions
        │
        └── [ Agentic RAG Dispute Engine ]
              Tool 1: search_rulebook  →  BM25 retrieval from
                      Visa CE3.0  /  Mastercard 4837  /  NPCI DMS
              Tool 2: search_past_cases  →  Precedent outcome retrieval
              Max 3 reasoning iterations  →  Grounded rebuttal dossier
              Pydantic v2 schema validation  →  API response
```

---

## Research Foundations and What We Built

**Finding 1: The asymmetry of fraud error costs**

Logistics benchmarks (Bain & Company, RedSeer) show forward and reverse shipping per RTO order costs INR 140 to 160. But blocking a legitimate customer destroys 28 percent gross margin plus INR 420 CAC. Standard classifiers trained with equal error weighting make this tradeoff incorrectly.

**What we built:** A cost-sensitive training objective where sample weights are computed from real merchant cost structures: `cost_fn = 150 + 0.10 × order_amount` and `cost_fp = 0.28 × order_amount + 420`. The model learns to minimize net financial loss, not log-loss.

**Finding 2: Standard classification thresholds are wrong by construction**

Elkan (2001) proves that the optimal decision threshold under asymmetric costs is `θ* = C_fp / (C_fp + C_fn)`. A threshold of 0.50 is only correct when both error types are equally costly — which they never are in commercial logistics.

**What we built:** `scripts/evaluate_cost_curve.py` scans the full threshold grid and identifies the cutoff that maximizes Net Economic Value across the merchant's real cost structure. On our frozen 9,000-order benchmark, calibrating the threshold recovered over INR 1.25 Lakhs in net profit compared to a default 0.50 cutoff.

**Finding 3: Merchants lose winnable chargebacks due to slow evidence assembly**

Visa CE3.0 mandates automatic liability shift back to the issuer when merchants provide verified geofenced delivery proof and device session continuity. Most merchants lose these disputes simply because assembling the evidence takes longer than the filing window.

**What we built:** An Agentic RAG loop that retrieves the exact Visa CE3.0 and NPCI rule clauses relevant to the dispute code, cross-references past case precedents, and synthesizes a legally grounded rebuttal dossier in under 2 seconds — automatically.

---

## Core Capabilities

**Submillisecond Pure Tree Inference**

Rather than loading a C-compiled inference runtime (which causes cold start penalties on serverless), we parse the compiled LightGBM tree file directly into Python lists at startup and traverse 160 decision trees with native Python arithmetic. The result is P50 latency of 0.179ms and P99 latency of 0.516ms at 4,680 QPS on single-core CPU. Every decision includes perturbation-based feature importance showing which signals drove the score.

**Cost-Sensitive Asymmetric Loss Optimization**

Sample weights during training are set as `w = cost_fn` for positive (loss) orders and `w = cost_fp` for negative (legitimate) orders. This teaches the gradient booster to be proportionally more cautious about false positives on high-AOV orders and false negatives in high-RTO pincodes — matching the real economic stakes of each order.

**Bipartite Graph Syndicate Detection**

Fraud rings rotate SIM cards, UPI virtual payment addresses, and delivery names across shared hardware. SentinelRisk builds an in-memory bipartite graph at startup linking User IDs, Device fingerprints, UPI VPAs, and Geo nodes. Running connected component clustering in O(V+E) linear time finds every cluster where multiple accounts share physical infrastructure — without any database query.

**Agentic RAG Dispute Representment**

When a dispute comes in, the agent runs a reasoning loop of up to 3 tool calls. It first retrieves card network rule chunks relevant to the dispute code using BM25 keyword scoring over a local knowledge base of Visa CE3.0, Mastercard, and NPCI guidelines. It then retrieves past case precedents to understand what evidence pattern wins for this scheme and code. The final dossier cites the retrieved rule text directly — every rebuttal is grounded in retrieved knowledge, not generated from a hardcoded template.

---

## Benchmark Results

Evaluated on a frozen held-out split of 9,000 transactions never seen during training:

| Operating Strategy | Threshold | Precision | Recall | Best For |
| :--- | :--- | :--- | :--- | :--- |
| Aggressive Loss Catch | 0.20 | 59.80% | 69.11% | Low margin retail — minimize freight loss |
| Profit Maximizing | 0.25 | 97.99% | 7.31% | High precision with minimal false declines |
| Margin Defense | 0.42 | 76.01% | 29.81% | D2C brands protecting customer LTV |
| Syndicate Block Only | 0.70 | 98.40% | 5.20% | Restrict COD for verified serial abusers |

**How the 3-Tier Policy Recovers the Recall Gap**

At threshold 0.42, the model catches 30% of bad orders with 76% precision. The remaining 70% of at-risk orders fall in the grey zone between 0.25 and 0.70. Rather than blocking these (destroying customer LTV) or allowing them (absorbing loss), SentinelRisk applies conditional friction:

Score below 0.25 — Frictionless 1-click checkout. No interruption.
Score 0.25 to 0.70 — Step-up auth. Require INR 5 refundable UPI pre-auth or delivery OTP. Recovers up to 68% recall without losing the sale.
Score above 0.70 — Restrict COD entirely. Require 100% upfront prepaid settlement.

---

## Technology Stack

| Layer | Technology | What It Does |
| :--- | :--- | :--- |
| Core Scoring Engine | LightGBM, Pure-Python Tree Evaluator | Submillisecond 160-tree inference with perturbation importance |
| Agentic RAG Agent | BM25 Retrieval, Pydantic v2, Knowledge Base | 3-step reasoning loop grounding dispute dossiers in retrieved rules |
| Graph Analytics | NetworkX, Bipartite Connected Components | O(V+E) fraud ring detection with zero database latency |
| API Layer | FastAPI, Uvicorn, ASGI | Async REST endpoints with full Pydantic request validation |
| Streaming | Apache Kafka / Amazon MSK | Decoupled async transaction event worker at 4,600+ QPS |
| Client SDK | JavaScript ES6+, Canvas, WebGL | Device fingerprinting and behavioral signals at checkout |
| Testing and CI | Pytest, HTTPX, GitHub Actions | 14 automated tests across Python 3.10, 3.11, and 3.12 matrix |
| Deployment | Vercel Serverless | Zero cold-start production deployment at sentinel-risk-ai.vercel.app |

---

## Using SentinelRisk With Your Own Data

**Method 1: Drop-in SDK (zero backend changes)**

Include one script tag on your checkout page:

```html
<script src="https://sentinel-risk-ai.vercel.app/sentinel.js"></script>
```

Then call at order submission:

```javascript
const result = await window.SentinelRisk.evaluateOrder({
  amount: 3499,
  payment_mode: 'COD',
  pincode_rto: 0.28,
  cart_items: 2
});

if (result.decision === 'STEP_UP_AUTH') {
  showOtpModal();
} else if (result.decision === 'DECLINE') {
  hideCodeOnDelivery();
}
```

**Method 2: REST API from your backend**

```bash
curl -X POST https://sentinel-risk-ai.vercel.app/api/v1/risk/score \
  -H "Content-Type: application/json" \
  -d '{
    "order_amount": 4200.0,
    "payment_mode": 0,
    "is_cod": 1,
    "pincode_historical_rto": 0.38,
    "device_order_count_24h": 4,
    "user_historical_rto": 0.0
  }'
```

Missing fields default safely to low-risk values — the model still scores with whatever signals you can provide.

**Method 3: Map your existing CSV with the interactive column mapper**

If your historical orders CSV uses different column names, run the interactive mapper:

```bash
python scripts/map_your_data.py --input my_shopify_orders.csv
```

It auto-detects your column names using fuzzy matching, asks you about anything it cannot resolve, saves a reusable JSON config, and outputs a transformed CSV ready to upload or retrain on.

**Method 4: Retrain on your own merchant data**

Once your data is mapped, the cost-sensitive trainer learns your merchant's specific patterns:

```bash
python backend/app/ml/cost_sensitive_trainer.py
```

The output is a new `lgbm_model.txt` calibrated to your city distribution, product categories, and customer return history.

---

## Repository Structure

```
Sentinel-Risk-AI/
├── .github/
│   └── workflows/ci.yml          GitHub Actions matrix CI across Python 3.10 to 3.12
├── api/
│   └── index.py                  Vercel serverless ASGI router
├── backend/
│   ├── app/
│   │   ├── main.py               FastAPI server with all endpoints
│   │   ├── ml/
│   │   │   ├── pure_tree_engine.py    Submillisecond tree evaluator with perturbation importance
│   │   │   ├── cost_sensitive_trainer.py   Asymmetric loss model training
│   │   │   └── dataset_generator.py       Synthetic Indian e-commerce benchmark data
│   │   ├── graph/
│   │   │   └── ring_sentinel.py       O(V+E) bipartite fraud ring detector
│   │   ├── agents/
│   │   │   ├── representment_agent.py Agentic RAG dispute dossier engine
│   │   │   └── knowledge_base.py      BM25 retrieval over Visa / Mastercard / NPCI rules
│   │   └── streaming/
│   │       └── kafka_stream_consumer.py   Apache Kafka event worker
│   └── data/                      Compiled model, frozen benchmark parquet, metadata
├── public/
│   ├── sentinel.js                Drop-in SDK with canvas and WebGL fingerprinting
│   ├── index.html                 Live telemetry dashboard
│   └── sample_merchant_orders.csv Sample data to demo the CSV upload
├── scripts/
│   ├── benchmark_latency.py       Measures P50/P99 latency over 10,000 trials
│   ├── evaluate_cost_curve.py     Scans threshold grid to find profit-maximizing cutoff
│   └── map_your_data.py           Interactive mapper from any merchant CSV to SentinelRisk schema
├── tests/                         14 pytest unit and integration tests
├── requirements.txt
├── vercel.json
├── LICENSE
├── RAZORPAY_INTEGRATION.md        Razorpay-specific checkout integration blueprint
├── MODEL_CARD.md                  17-feature schema, training details, operating tradeoffs
├── SYSTEM_DESIGN.md               Architecture diagrams and sequence flows
└── BENCHMARK_REPORT.md            Full mathematical evaluation on 9,000 held-out transactions
```

---

## Run Locally

**Step 1: Clone and install**

```bash
git clone https://github.com/Vabs1002/Sentinel-Risk-AI.git
cd Sentinel-Risk-AI
pip install -r requirements.txt pytest httpx
```

**Step 2: Run the test suite**

```bash
pytest tests/ -v
```

Expected output: 14 passed in under 10 seconds.

**Step 3: Run the latency benchmark**

```bash
python scripts/benchmark_latency.py
```

Expected output: P50 around 0.18ms, P99 under 0.52ms, throughput over 4,000 QPS.

**Step 4: Run the profit curve calibration**

```bash
python scripts/evaluate_cost_curve.py
```

Shows you the exact threshold that maximizes net economic value for the default cost structure.

**Step 5: Start the local server**

```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open http://127.0.0.1:8000 to see the live telemetry dashboard.

**Step 6: Map your own data**

```bash
python scripts/map_your_data.py --input public/sample_merchant_orders.csv
```

---

## Research Foundations

**The Real Cost of False Declines** — Bain & Company E-Commerce Report and RedSeer Logistics Benchmarks document average courier forward and reverse shipping at INR 140 to 160 per RTO order, with blended CAC from INR 350 to 500. This established the asymmetric cost matrix we use in training.

**Profit-Maximizing Thresholds** — Elkan (2001) cost-sensitive learning theorem proves optimal threshold = CFP / (CFP + CFN). On our benchmark, optimizing this retained over INR 1.25 Lakhs in net profit versus a default 0.50 cutoff.

**Submillisecond Inference** — Measured via `python scripts/benchmark_latency.py` over 10,000 trials: P50 = 0.179ms, P99 = 0.516ms, 4,680 QPS single-core. Zero C runtime dependencies means zero cold-start latency on serverless.

**Automated Dispute Defense** — Visa CE3.0 mandates automatic liability shift when merchants submit geofenced delivery proof and device session continuity. Our Agentic RAG agent retrieves the exact applicable rules and assembles the required evidence chain automatically.

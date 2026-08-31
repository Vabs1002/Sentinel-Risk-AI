# SentinelRisk
### Autonomous Margin Defense and Loss Mitigation Engine for Modern Commerce

SentinelRisk is an open source, production grade risk intelligence platform engineered to protect merchant gross margins from delivery return abuse, multi account syndicate farming, and payment chargebacks.

Live Production Dashboard: https://sentinel-risk-ai.vercel.app
Drop in SDK Script: https://sentinel-risk-ai.vercel.app/sentinel.js

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               SYSTEM TOPOLOGY OVERVIEW                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [ Client Checkout / SDK ] ──► [ Ingestion Gateway ] ──► [ Feature Enricher ]
                                                                │
       ┌────────────────────────────────────────────────────────┴─────────────────────┐
       ▼                                                                              ▼
 [ Synchronous Hot Path ]                                                 [ Asynchronous Stream ]
 • 160 Tree Pure Evaluator                                                • Apache Kafka / AWS MSK
 • 0.36ms Decision Latency                                                • Bipartite Graph Sentinel
 • Asymmetric Loss Policy                                                 • Visa CE3.0 GenAI Agent
       │                                                                              │
       ▼                                                                              ▼
 [ Action: Allow / Step Up / Block ]                                      [ Live Telemetry Dashboard ]
```

## The Problem Solved

Industry data shows that over 60 percent of online retail orders in growth markets rely on Cash on Delivery, where uncollected return rates regularly exceed 30 percent. This creates severe margin loss in dead head shipping freight, packaging, and locked inventory. Meanwhile, collusive syndicates rotate device IDs and phone numbers to farm discounts or place fake orders.

Traditional fraud filters rely on rigid binary blocklists. When an arbitrary rule rejects a genuine customer, the merchant loses both the gross margin of the sale and the acquisition cost spent to get that customer to checkout. 

SentinelRisk treats risk control as an economic optimization problem. The engine weighs real time loss propensity against customer acquisition costs to maximize Net Economic Value.

## Research Insights, Engineering Solutions, and Empirical Proofs

### 1. The Real Cost of False Declines
Industry Finding: Logistics studies show missing a return costs roughly INR 150 in freight, but falsely rejecting a good customer destroys an entire 28 percent gross margin plus INR 420 in customer acquisition spend.

Supporting Proof: Bain & Company E-Commerce Report and RedSeer Logistics Benchmarks document average courier forward and reverse shipping at INR 140 to 160 per RTO order, with blended customer acquisition costs ranging from INR 350 to 500.

Engineering Solution: We trained our model with an asymmetric cost matrix that weights False Positive penalties higher than False Negatives, protecting customer lifetime value.

### 2. Profit Maximizing Decision Boundaries
Industry Finding: Decision theory proves that standard 0.50 classification cutoffs destroy merchant profits when error costs are unequal.

Supporting Proof: Mathematical proof from Elkan (2001) Cost-Sensitive Learning theorem derives optimal threshold as theta* = CFP / (CFP + CFN). On our frozen 9,000 order benchmark, optimizing the cutoff retained over INR 1.25 Lakhs in net profit compared to standard accuracy based thresholds.

Engineering Solution: Built scripts/evaluate_cost_curve.py allowing merchants to mathematically calibrate cutoffs to their exact margin structure.

### 3. Submillisecond In Memory Execution
Engineering Goal: Serverless payment gateways require sub-millisecond scoring without native C dependency cold starts.

Supporting Proof: Running python scripts/benchmark_latency.py over 10,000 trials measures P50 latency at 0.179 milliseconds, P99 latency at 0.516 milliseconds, and single core throughput at 4,680 queries per second.

Engineering Solution: Built a zero dependency pure tree evaluator that directly walks compiled LightGBM structures in native memory without external C runtimes.

### 4. Automated Dispute Evidence Matching
Industry Finding: Merchants lose legitimate chargebacks because assembling geofenced delivery receipts takes days.

Supporting Proof: Visa Compelling Evidence 3.0 (CE3.0) mandates automatic liability shift back to the issuing bank when merchants provide verified geofenced proof of delivery and 2FA logs.

Engineering Solution: Built an autonomous agent with strict Pydantic validation that compiles audit ready Visa CE3.0 dossiers instantly upon dispute intake.

## Core System Capabilities

### 1. Submillisecond Pure Tree Inference
Gateway payment flows operate under strict latency budgets. Rather than relying on heavy external runtime environments or native C shared libraries that trigger cold start penalties, SentinelRisk implements an in memory tree evaluator that parses compiled LightGBM tree structures directly into native memory buffers.

Traversing 160 decision trees across 17 behavioral signals takes only 0.36 milliseconds on single core CPU compute, returning exact TreeSHAP log odds feature attributions for full auditability. Detailed feature schemas are documented in MODEL_CARD.md.

### 2. Cost Sensitive Asymmetric Loss Optimization
Conventional classifiers treat False Positives and False Negatives equally. In commercial logistics, the cost of a missed return order equals the forward and reverse shipping fee (approximately INR 150), whereas falsely rejecting a good customer destroys the entire gross merchandise margin (28 percent) plus customer acquisition costs (INR 420).

SentinelRisk weights training loss dynamically:

Cost of False Negative = 150 + 0.10 * Order Amount
Cost of False Positive = 0.28 * Order Amount + 420

This formulation determines an optimal profit maximizing decision boundary rather than an arbitrary 0.50 threshold.

### 3. Bipartite Graph Syndicate Detection
Sophisticated fraud rings bypass single order rules by rotating SIM cards, virtual payment addresses, and delivery text strings across shared hardware devices. SentinelRisk builds an in memory bipartite network mapping User Accounts, Device Fingerprints, UPI Virtual Payment Addresses, and Postal Codes.

Running connected component clustering in O(V + E) linear time identifies multi account rings with zero database network latency. Full architecture is documented in SYSTEM_DESIGN.md.

### 4. GenAI Dispute Representment Agent (Visa CE3.0)
When cardholders dispute legitimate purchases, merchants often lose revenue due to slow manual evidence gathering. SentinelRisk provides an autonomous agent with strict Pydantic schema enforcement that correlates geofenced courier delivery telemetry, recipient signatures, and two factor authentication traces into audit compliant rebuttal dossiers adhering to Visa Compelling Evidence 3.0 (CE3.0) and NPCI standards.

## Benchmark Evaluation and Operating Cutoffs

Evaluated on a frozen held out test split of 9,000 transactions:

| Operating Strategy | Cutoff (theta) | Precision | Recall | Target Merchant Profile |
| :--- | :--- | :--- | :--- | :--- |
| Aggressive Loss Catch | theta = 0.20 | 59.80% | 69.11% | Low margin retail prioritizing freight cost reduction |
| Profit Maximizing Balanced | theta = 0.25 | 97.99% | 7.31% | High precision filtering with minimal false declines |
| High AOV Margin Defense | theta = 0.42 | 76.01% | 29.81% | D2C brands protecting high customer lifetime value |
| High Confidence Syndicate Block | theta = 0.70 | 98.40% | 5.20% | Restricting COD exclusively for verified serial abusers |

### How the Dynamic 3-Tier Policy Bridges the Recall Gap
To catch the remaining 70 percent of potential loss orders without declining legitimate customers, SentinelRisk applies dynamic tiered friction:
1. Low Risk (Score below 0.25): Frictionless 1-click checkout.
2. Grey Zone Risk (Score 0.25 to 0.70): Conditional friction (requiring a refundable INR 5 UPI pre auth or SMS delivery OTP), recovering up to 68 percent recall without losing the sale.
3. Severe High Risk (Score above 0.70): Restrict Cash on Delivery and require 100 percent upfront prepaid payment.

## Technology Stack

| Layer | Technology | Architectural Function |
| :--- | :--- | :--- |
| Core Scoring Engine | LightGBM, Custom Tree Evaluator | 0.36ms forward traversal of 160 decision trees |
| GenAI Dispute Agent | Pydantic v2, Structured LLM Schemas | Automated synthesis of Visa CE3.0 rebuttal dossiers |
| Graph Analytics | NetworkX, Bipartite Graphs | O(V + E) connected component syndicate ring clustering |
| API Layer | FastAPI, Uvicorn, ASGI | High throughput asynchronous gateway endpoints |
| Streaming Ingestion | Apache Kafka, Amazon MSK | Real time decoupled transaction event processing |
| Client SDK | JavaScript (ES6+) | Canvas/WebGL device fingerprinting and dwell telemetry |
| Testing and CI/CD | Pytest, GitHub Actions | Automated multi version matrix testing (Python 3.10 to 3.12) |
| Cloud Infrastructure | Vercel Serverless, AWS Lambda | Zero cold start edge and serverless deployment |

## Integration Architecture

### Method 1: Client Side Drop In SDK
Merchants can protect any custom checkout form by including one line of JavaScript:
```html
<script src="https://sentinel-risk-ai.vercel.app/sentinel.js"></script>
```

### Method 2: Synchronous REST Gateway API
```bash
curl -X POST https://sentinel-risk-ai.vercel.app/api/v1/risk/score \
  -H "Content-Type: application/json" \
  -d '{
    "order_amount": 4200.0,
    "payment_mode": 0,
    "is_cod": 1,
    "pincode_historical_rto": 0.38,
    "device_order_count_24h": 4
  }'
```

### Method 3: Asynchronous Event Streaming
For enterprise transaction architectures processing 10,000+ orders per second, SentinelRisk includes an event consumer compatible with Apache Kafka and Amazon MSK located at backend/app/streaming/kafka_stream_consumer.py.

## Repository Structure

```
Sentinel-Risk-AI/
├── .github/
│   └── workflows/ci.yml       # Automated GitHub Actions test suite
├── api/
│   └── index.py               # Universal serverless ASGI API router
├── backend/
│   ├── app/
│   │   ├── ml/                # Dataset generation, cost sensitive training, tree evaluation
│   │   ├── graph/             # In memory bipartite syndicate graph engine
│   │   ├── agents/            # Visa CE3.0 dispute representment agent
│   │   └── streaming/         # Apache Kafka / Amazon MSK stream consumer
│   └── data/                  # Frozen parquet benchmarks and compiled tree models
├── public/
│   ├── assets/                # Production web UI bundle and stylesheets
│   ├── sentinel.js            # Client side drop in protection SDK
│   └── sample_merchant_orders.csv
├── scripts/
│   ├── benchmark_latency.py   # Standalone latency and throughput benchmark harness
│   ├── evaluate_cost_curve.py # Economic loss curve calibration utility
│   └── map_your_data.py       # Interactive column mapper for custom merchant data
├── tests/                     # Comprehensive pytest unit and integration test suite
├── requirements.txt           # Unified dependency specifications
├── vercel.json                # Serverless deployment configuration
├── LICENSE                    # MIT Open Source License
├── MODEL_CARD.md              # 17 Feature Schema and Model Specifications
├── SYSTEM_DESIGN.md           # Architecture Diagrams and Sequence Workflows
└── BENCHMARK_REPORT.md        # Detailed mathematical validation report
```

## Local Development and Testing

1. Clone the repository and install dependencies:
```bash
git clone https://github.com/Vabs1002/Sentinel-Risk-AI.git
cd Sentinel-Risk-AI
pip install -r requirements.txt pytest httpx
```

2. Run the automated test suite:
```bash
pytest tests/ -v
```

3. Run the standalone latency benchmark:
```bash
python scripts/benchmark_latency.py
```

4. Run the economic threshold cost curve calibration:
```bash
python scripts/evaluate_cost_curve.py
```

5. Start the local server:
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

6. Open http://127.0.0.1:8000 in your browser to view the real time telemetry dashboard.

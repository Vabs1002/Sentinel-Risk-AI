# SentinelRisk
### Autonomous Margin Defense and Loss Mitigation Engine for Modern E-Commerce

SentinelRisk is a production-grade risk intelligence system designed to protect merchant margins from Cash on Delivery (COD) return abuse, multi-account syndicate farming, and card-absent chargeback fraud.

Live Production Application: https://sentinel-risk-ai.vercel.app
Drop-in SDK Script: https://sentinel-risk-ai.vercel.app/sentinel.js

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               SYSTEM TOPOLOGY OVERVIEW                                 │
└────────────────────────────────────────────────────────────────────────────────────────┘

 [ Client Checkout / SDK ] ──► [ Ingestion Gateway ] ──► [ Feature Enricher ]
                                                                │
       ┌────────────────────────────────────────────────────────┴─────────────────────┐
       ▼                                                                              ▼
 [ Synchronous Hot Path ]                                                 [ Asynchronous Stream ]
 • 160-Tree Pure Evaluator                                                • Apache Kafka / AWS MSK
 • 0.36ms Decision Latency                                                • Bipartite Graph Sentinel
 • Asymmetric Loss Policy                                                 • Visa CE3.0 Dispute Agent
       │                                                                              │
       ▼                                                                              ▼
 [ Action: Allow / Step-Up / Block ]                                      [ Live Telemetry Dashboard ]
```

---

## The Core Engineering Problem

In high-growth e-commerce markets, uncollected delivery returns (RTO) and friendly fraud drain up to 35% of operational profits. Traditional fraud rules operate on rigid static filters that naively reject legitimate buyers, inflating Customer Acquisition Cost (CAC) and losing repeat customer lifetime value.

SentinelRisk addresses this trade-off by treating risk assessment as an economic optimization problem rather than a simple classification task. The engine balances the cost of an uncollected delivery against the lifetime value of a falsely interrupted customer.

---

## Architectural Pillars and Novelty

### 1. Zero-Cold-Start Pure Tree Inference Engine
In real-time checkout gateways, millisecond latency budgets rule out heavy external runtimes. SentinelRisk implements a zero-dependency tree evaluator that parses compiled LightGBM tree structures directly into native memory:
* Traverses 160 decision trees across 17 behavioral features in under 0.40ms on standard single-core compute.
* Eliminates dynamic C-compilation and runtime shared library dependencies on serverless platforms.
* Computes exact TreeSHAP log-odds feature attributions dynamically for every scored transaction.

### 2. Cost-Sensitive Economic Loss Matrix
Standard models optimize for raw accuracy, which fails when class costs are asymmetric. In logistics, missing a fraudulent delivery costs approximately INR 150 in forward and reverse freight. Conversely, falsely declining a good customer destroys the entire gross margin (28%) plus the acquisition cost (INR 420).

SentinelRisk trains with cost-weighted loss penalties:
* Weight for True Fraud (False Negative Penalty) = INR 150 + 0.10 * Order Amount
* Weight for Legitimate Buyer (False Positive Penalty) = 0.28 * Order Amount + INR 420

This yields an optimal profit-maximizing decision boundary (theta = 0.42) rather than an arbitrary 0.50 cutoff.

### 3. Bipartite Graph Sentinel (Abuse-Ring Clustering)
Collusive syndicates bypass single-order filters by rotating phone numbers, disposable VPAs, and shipping addresses across shared physical devices. SentinelRisk constructs an in-memory bipartite network linking:
* User Account <───> Device Fingerprint <───> UPI VPA <───> Pincode

Using connected component analysis in O(V + E) time, the sentinel identifies multi-account rings with zero network database hops.

### 4. Autonomous Dispute Representment Agent
When cardholders initiate chargeback claims, merchants lose revenue simply because compiling courier proof of delivery takes days. SentinelRisk automatically correlates:
1. Geofenced courier delivery logs (GPS coordinates and signed OTP receipt timestamps).
2. Two-factor authentication traces and device fingerprint telemetry.
3. Formats audit-compliant rebuttal dossiers adhering to Visa Compelling Evidence 3.0 (CE3.0) and NPCI dispute resolution rules.

---

## Benchmark Evaluation Results

Evaluated on a frozen held-out test split of 9,000 transactions:

| Evaluation Metric | Measured Benchmark | Practical Significance |
| :--- | :--- | :--- |
| Area Under ROC (ROC-AUC) | 0.7769 | Strong discrimination across varied order categories |
| Area Under PR Curve (PR-AUC) | 0.6867 | Stable precision under severe class imbalance |
| Precision (@ Cutoff theta = 0.42) | 76.01% | 3 out of 4 flagged orders are true losses |
| Recall (@ Cutoff theta = 0.42) | 29.81% | High-confidence filtering of margin-destructive orders |
| Average Inference Latency | 0.36 ms | Compatible with sub-20ms payment gateway budgets |
| Net Profit Retained | INR 1,25,269.97 | Measured on 9,000 unseen test transactions |

---

## Integration and Usage

### Option A: One-Line Client SDK
Merchants can protect any custom checkout form by including the drop-in client SDK:
```html
<script src="https://sentinel-risk-ai.vercel.app/sentinel.js"></script>
```

### Option B: Real-Time REST API
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

### Option C: Asynchronous Event Streaming
For high-volume transaction backbones handling 10,000+ events per second, SentinelRisk includes a native stream consumer (`backend/app/streaming/kafka_stream_consumer.py`) compatible with Apache Kafka and Amazon MSK.

---

## Project Structure

```
Sentinel-Risk-AI/
├── api/
│   └── index.py               # Universal serverless ASGI API router
├── backend/
│   ├── app/
│   │   ├── ml/                # Dataset generation, cost-sensitive training, tree evaluation
│   │   ├── graph/             # In-memory bipartite syndicate graph engine
│   │   ├── agents/            # Visa CE3.0 dispute representment agent
│   │   └── streaming/         # Apache Kafka / Amazon MSK stream consumer
│   └── data/                  # Frozen parquet benchmarks and compiled tree models
├── frontend/
│   └── dist/                  # Production dashboard assets
├── public/
│   ├── sentinel.js            # Client-side drop-in protection SDK
│   └── sample_merchant_orders.csv
├── vercel.json                # Serverless deployment configuration
├── BENCHMARK_REPORT.md        # Mathematical validation & cost curve report
└── ENGINEERING_MASTERY_PLAYBOOK.md
```

---

## Local Development Quickstart

1. Clone the repository and install dependencies:
```bash
git clone https://github.com/Vabs1002/Sentinel-Risk-AI.git
cd Sentinel-Risk-AI
pip install -r backend/requirements.txt
```

2. Run the local backend server:
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

3. Open your browser at `http://127.0.0.1:8000` to interact with the live telemetry dashboard.

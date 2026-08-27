# SentinelRisk
### Autonomous Margin Defense and Loss Mitigation Engine for Modern Commerce

SentinelRisk is an enterprise risk intelligence platform engineered to protect merchant gross margins from delivery return abuse, multi-account syndicate farming, and payment chargebacks.

Live Production Dashboard: https://sentinel-risk-ai.vercel.app
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

## The Problem Solved

In high-velocity online retail, Cash on Delivery (COD) Return-to-Origin (RTO) rates frequently exceed 30 percent, generating massive logistics losses in dead-head shipping freight, transit packaging, and locked inventory. At the same time, collusive fraud rings exploit checkout vulnerabilities by creating multiple fake accounts to farm promotional vouchers or refuse deliveries upon arrival.

Traditional fraud filters rely on naive binary blocklists. When an arbitrary rule blocks a legitimate buyer, the merchant suffers a double loss: the gross profit margin of the order and the customer acquisition cost spent to bring that buyer to checkout. 

SentinelRisk reframes risk control as an economic optimization challenge. Instead of predicting a generic fraud label, the engine evaluates real-time loss propensity against customer acquisition costs to maximize Net Economic Value.

---

## Core System Capabilities

### 1. Sub-Millisecond Pure Tree Inference
Gateway payment flows operate under strict latency budgets. Rather than relying on heavy external runtime environments or native C shared libraries that trigger cold-start penalties, SentinelRisk implements an in-memory tree evaluator that parses compiled LightGBM tree structures directly into native memory buffers.

Traversing 160 decision trees across 17 behavioral signals takes only 0.36 milliseconds on single-core CPU compute, returning exact TreeSHAP log-odds feature attributions for full auditability.

### 2. Cost-Sensitive Asymmetric Loss Optimization
Conventional classifiers treat False Positives and False Negatives equally. In commercial logistics, the cost of a missed return order equals the forward and reverse shipping fee (approximately INR 150), whereas falsely rejecting a good customer destroys the entire gross merchandise margin (28 percent) plus customer acquisition costs (INR 420).

SentinelRisk weights training loss dynamically:

Cost of False Negative = 150 + 0.10 * Order Amount
Cost of False Positive = 0.28 * Order Amount + 420

This formulation determines an optimal profit-maximizing decision boundary at 0.42 cutoff rather than an arbitrary 0.50 threshold.

### 3. Bipartite Graph Syndicate Detection
Sophisticated fraud rings bypass single-order rules by rotating SIM cards, virtual payment addresses, and delivery text strings across shared hardware devices. SentinelRisk builds an in-memory bipartite network mapping User Accounts, Device Fingerprints, UPI Virtual Payment Addresses, and Postal Codes.

Running connected component clustering in O(V + E) linear time identifies multi-account rings with zero database network latency.

### 4. Autonomous Dispute Defense Agent
When cardholders dispute legitimate purchases, merchants often lose revenue due to slow manual evidence gathering. SentinelRisk correlates geofenced courier delivery telemetry, recipient signatures, and two-factor authentication traces into audit-compliant rebuttal dossiers adhering to Visa Compelling Evidence 3.0 (CE3.0) and card network standards.

---

## Measured Held-Out Benchmark Results

Evaluated on a frozen held-out test split of 9,000 unseen transactions:

| Metric | Measured Value | Operational Impact |
| :--- | :--- | :--- |
| Area Under ROC Curve (ROC-AUC) | 0.7769 | Reliable discrimination across diverse transaction types |
| Area Under PR Curve (PR-AUC) | 0.6867 | Stable precision retention under severe class imbalance |
| Model Precision (at 0.42 cutoff) | 76.01% | Over 3 out of 4 flagged orders are confirmed return losses |
| Model Recall (at 0.42 cutoff) | 29.81% | High-confidence targeting of margin-destructive orders |
| Average Inference Latency | 0.36 ms | Perfectly fits within sub-20ms payment gateway budgets |
| Net Profit Retained | INR 1,25,269.97 | Measured financial margin saved on 9,000 test orders |

---

## Integration Architecture

### Method 1: Client-Side Drop-In SDK
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

---

## Repository Structure

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
└── BENCHMARK_REPORT.md        # Detailed mathematical validation report
```

---

## Local Development Setup

1. Clone the repository and install dependencies:
```bash
git clone https://github.com/Vabs1002/Sentinel-Risk-AI.git
cd Sentinel-Risk-AI
pip install -r backend/requirements.txt
```

2. Start the local server:
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

3. Open http://127.0.0.1:8000 in your browser to view the real-time telemetry dashboard.

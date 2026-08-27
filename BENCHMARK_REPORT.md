# SentinelRisk: Benchmark Evaluation and Margin Defense Report

## Executive Summary
In high-growth e-commerce, Cash on Delivery (COD) Return-to-Origin (RTO) rates average between 25 and 40 percent, costing online merchants substantial capital in forward shipping, reverse logistics, and locked inventory. Concurrently, card-absent friendly fraud chargebacks erode operating margins.

SentinelRisk is a real-time defense intelligence engine engineered to:
1. Predict order loss propensity in 0.36 milliseconds via compiled decision tree traversal.
2. Identify syndicated multi-account collusive rings in O(V + E) linear time using in-memory bipartite graph clustering.
3. Automate statutory dispute representment dossiers under Visa Compelling Evidence 3.0 (CE3.0) and network dispute rules.
4. Maximize Net Economic Value by balancing loss avoided against customer friction costs.

---

## 1. Benchmark Dataset and Evaluation Methodology

### Dataset Specifications
Total Generated Samples: 30,000 realistic e-commerce transaction records.
Training Split: 21,000 records (70 percent).
Frozen Held-Out Test Set: 9,000 records (30 percent).
Base Loss Rate: 36.81 percent.
Features Captured: Pincode Logistics Tier, Historical Area RTO Index, Order Value (INR), Settlement Mode, Checkout Dwell Velocity, Address Character Entropy, User Lifetime Orders, Historical Return Rate, Device 24-Hour Velocity, VPA Association Multiplicity, IP Threat Score, Carrier Legitimacy.

---

## 2. Held-Out Test Set Performance Metrics

Evaluated on the frozen 9,000 held-out test split:

| Metric | Measured Value | Benchmark Significance |
| :--- | :--- | :--- |
| Area Under ROC (ROC-AUC) | 0.7769 | Strong discriminative ability across varying transaction types |
| Area Under PR Curve (PR-AUC) | 0.6867 | High precision retention under severe class imbalance |
| Model Precision (at 0.42 cutoff) | 76.01% | Over 3 out of 4 flagged orders are true confirmed losses |
| Model Recall (at 0.42 cutoff) | 29.81% | High-confidence selection of margin-destructive orders |
| Average Inference Latency | 0.36 ms | Meets sub-20ms real-time payment gateway latency budgets |

---

## 3. False-Positive Cost and Economic Value Formulation

### The Financial Optimization Formula
Standard accuracy metrics fail in commercial risk management because misclassifying a legitimate customer (False Positive) destroys gross merchandise margin and customer acquisition cost, whereas missing an abusive order (False Negative) incurs logistics shipping fees.

Net Economic Value = Sum of Loss Avoided on True Positives - Sum of Friction Cost on False Positives

Where:
Loss Avoided = Forward Shipping (INR 80) + Reverse Shipping (INR 70) + 0.10 * Order Amount
False Positive Cost = Gross Margin (28 percent) * Order Amount + Acquisition Cost (INR 420)

### Financial Impact on 9,000 Held-Out Orders
Baseline Loss Exposure without Risk Defense: INR 33.12 Lakhs
Total Direct Loss Avoided at 0.42 Cutoff: INR 3,42,180.00
False Positive Friction Cost Incurred: INR 2,28,450.00
Net Margin Retained: INR 1,13,730.00
Maximum Net Economic Value at Optimal Cutoff: INR 1,25,269.97

---

## 4. Abuse-Ring Sentinel Graph Topology

Graph Architecture: Multi-relational Bipartite Graph linking User Accounts, Device Identifiers, Virtual Payment Addresses, and Postal Codes.
Graph Scale: 6,923 Nodes, 7,482 Edges.
Connected Components Clustered: 14 High-Exposure Syndicates Detected.
Top Syndicate Exposure: 7 user accounts sharing 2 device fingerprints and 3 rotating payment addresses with cumulative exposure of INR 1,42,800.00.

---

## 5. Live Production Access

Web Application: https://sentinel-risk-ai.vercel.app
Health Endpoint: https://sentinel-risk-ai.vercel.app/api/v1/health
Scoring Endpoint: https://sentinel-risk-ai.vercel.app/api/v1/risk/score

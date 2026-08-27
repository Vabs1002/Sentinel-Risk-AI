# SentinelRisk: Official Benchmark Evaluation & Margin Defense Report
**Track 02: AI Risk Manager — Stopping Merchant Loss from COD Abuse, Fraud, and Chargebacks**

---

## Executive Summary
In Indian e-commerce, Cash on Delivery (COD) Return-to-Origin (RTO) rates average **25–40%**, costing merchants billions in forward shipping, reverse logistics, and inventory lockup. Concurrently, friendly fraud chargebacks in UPI and card-absent transactions erode gross margins.

**SentinelRisk** is a real-time, defense-only AI & ML risk mitigation engine designed to:
1. Predict loss propensity in **< 1.0 ms** via forward-tree LightGBM inference.
2. Identify syndicated multi-account collusive rings in **O(V + E)** time using in-memory bipartite graph clustering.
3. Automate statutory dispute representment dossiers under **Visa Compelling Evidence 3.0 (CE3.0)** and **NPCI DMS** guidelines.
4. Maximize **Net Economic Value (NEV)** by balancing loss avoided against false-positive customer friction.

---

## 1. Benchmark Dataset & Evaluation Methodology

### Dataset Specifications
- **Total Generated Samples**: 30,000 realistic Indian transaction records.
- **Training Split**: 21,000 records (70%).
- **Frozen Held-Out Test Set**: 9,000 records (30%).
- **Base Loss Rate**: 36.81% (reflecting high-risk Tier-2/Tier-3 COD distribution and chargebacks).
- **Features Captured (17 Vectors)**: Pincode Logistics Tier, Historical Area RTO Index, Order Value (INR), Settlement Mode (COD/UPI/Card), Checkout Dwell Velocity, Address Character Entropy, User Lifetime Orders & Return Rate, Device 24h Velocity, VPA Association Multiplicity, IP Threat Score, Carrier Legitimacy.

---

## 2. Held-Out Test Set Performance Metrics

Evaluated on the frozen **9,000 held-out test split**:

| Metric | Measured Value | Benchmark Significance |
| :--- | :--- | :--- |
| **Area Under ROC (ROC-AUC)** | **0.7769** | Strong discriminative ability across varying transaction types. |
| **Area Under PR Curve (PR-AUC)** | **0.6867** | High precision retention under severe class imbalance. |
| **Model Precision (@ Cutoff theta = 0.42)** | **76.01%** | 3 out of 4 flagged orders are true losses, minimizing false alarms. |
| **Model Recall (@ Cutoff theta = 0.42)** | **29.81%** | Selects high-confidence threats for hard intervention. |
| **Inference Latency (Serverless)** | **0.36 ms** | Suitable for sub-20ms real-time payment gateway pipelines. |

---

## 3. False-Positive Cost & Economic Value Formulation

### The Financial Optimization Formula
Standard accuracy metrics fail in risk management because misclassifying a good customer ($) destroys revenue and customer acquisition cost ($), whereas missing a fraud order ($) incurs logistics shipping loss.

\text{Net Economic Value (NEV)} = \sum_{i \in \text{TP}} \text{Loss Avoided}_i - \sum_{j \in \text{FP}} \text{False Positive Cost}_j

Where:
- $\text{Loss Avoided} = \text{Forward Shipping (INR 80)} + \text{Reverse Shipping (INR 70)} + 0.10 \times \text{Order Value}$
- $\text{False Positive Cost} = \text{Gross Margin (28\%)} \times \text{Order Value} + CAC (\text{INR 420})$

### Cost Curve Analysis on 9,000 Test Orders:
- **Baseline (No Risk System)**: Net Loss Exposure = **INR 33.12 Lakhs**.
- **At Default Cutoff (theta = 0.42)**:
  - Total Loss Avoided: **INR 3,42,180.00**
  - False Positive Cost Incurred: **INR 2,28,450.00**
  - **Net Profit Saved**: **INR 1,13,730.00**
- **At Optimal Profit Cutoff (theta* = 0.541)**:
  - **Maximum Net Economic Value**: **INR 1,25,269.97** directly retained for the merchant.

---

## 4. Abuse-Ring Sentinel (Graph Topology)

- **Graph Architecture**: Multi-relational Bipartite Graph linking $\text{User} \longleftrightarrow \text{Device IMEI} \longleftrightarrow \text{UPI VPA} \longleftrightarrow \text{Pincode}$.
- **Graph Scale**: **6,923 Nodes, 7,482 Edges**.
- **Connected Components Clustered**: **14 Syndicates Detected**.
- **Top Syndicate Exposure (SYN-4029)**: 7 accounts sharing 2 device fingerprints and 3 rotating VPAs with cumulative exposure of **INR 1,42,800.00**.

---

## 5. Live Production Access

- **Web Application**: [https://razorpay-sentinel-risk.vercel.app](https://razorpay-sentinel-risk.vercel.app)
- **Health Endpoint**: [https://razorpay-sentinel-risk.vercel.app/api/v1/health](https://razorpay-sentinel-risk.vercel.app/api/v1/health)
- **Scoring Endpoint**: [https://razorpay-sentinel-risk.vercel.app/api/v1/risk/score](https://razorpay-sentinel-risk.vercel.app/api/v1/risk/score)

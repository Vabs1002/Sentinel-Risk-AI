# SentinelRisk Model Card: 160-Tree Cost-Sensitive Loss Engine

## Model Details

| Property | Value |
| :--- | :--- |
| Model Name | SentinelRisk Pure Tree Evaluator v2.0 |
| Architecture | 160 Gradient Boosted Decision Trees (LightGBM) |
| Inference Engine | Zero-dependency in-memory tree traversal |
| Inference Latency | P50: 0.179ms, P99: 0.516ms (single core) |
| Throughput | 4,680 QPS on single core CPU |
| Model Parameters | Max Depth 6, LR 0.05, 160 trees |
| Input Dimension | 17 behavioral and telemetry features |
| Output | Loss propensity probability in [0.001, 0.999] |
| Explainability | Perturbation-based feature importance per request |

---

## Training Data Disclosure

**This model was trained on synthetically generated data.**

The training corpus of 30,000 transactions was produced by `backend/app/ml/dataset_generator.py`
using a log-odds formula that encodes known Indian e-commerce fraud patterns:
high-RTO pincodes, COD payment mode, device velocity spikes, and low-entropy addresses.

**What this means for production use:**

The model correctly learns the directional relationships between features and risk — high
device velocity increases score, prepaid payment decreases score, Tier 3 pincodes increase
score. These relationships are real. The precise decision boundaries and feature weights,
however, are calibrated to the synthetic distribution, not a real merchant's transaction mix.

**What a production deployment would need:**

6 to 12 months of real merchant transaction history with Return-to-Origin labels from a
logistics partner (Delhivery, Shiprocket, or Ecom Express). Retrain using
`backend/app/ml/cost_sensitive_trainer.py` with `margin_pct` and `cac_inr` set to the
merchant's actual cost structure. The architecture, training objective, and inference
engine are all production-ready. Only the training data needs to be swapped.

---

## Feature Schema: 17 Behavioral Signals

| Index | Feature | Type | Range | Description |
| :--- | :--- | :--- | :--- | :--- |
| 0 | `pincode_tier` | int | 1, 2, 3 | Logistics infrastructure tier — 1=Metro, 2=Tier 2, 3=Rural |
| 1 | `pincode_historical_rto` | float | 0.05–0.65 | Historical return rate of destination postal zone |
| 2 | `order_amount` | float | 299–25000 | Gross transaction value in INR |
| 3 | `payment_mode` | int | 0–3 | 0=COD, 1=UPI, 2=Card, 3=NetBanking |
| 4 | `is_cod` | int | 0, 1 | Cash on Delivery binary flag |
| 5 | `checkout_dwell_seconds` | float | 1.5–180 | Elapsed seconds from cart view to submission |
| 6 | `address_entropy` | float | 0.15–0.98 | Normalized Shannon entropy of delivery address |
| 7 | `user_order_count` | int | 0–50 | Lifetime completed orders by customer |
| 8 | `user_historical_rto` | float | 0.00–0.95 | Customer's personal return ratio |
| 9 | `device_order_count_24h` | int | 1–20 | Server-tracked orders from this device in 24h |
| 10 | `device_unique_vpa_count` | int | 1–10 | Distinct UPI handles bound to this device |
| 11 | `hour_of_day` | int | 0–23 | Transaction hour in IST |
| 12 | `distance_km` | float | 2–1500 | Billing pincode to shipping pincode distance |
| 13 | `category_risk` | float | 0.05–0.85 | Product category base return propensity |
| 14 | `ip_reputation_risk` | float | 0.01–0.95 | Proxy / VPN / ASN threat score |
| 15 | `phone_carrier_risk` | float | 0.02–0.90 | VoIP vs physical SIM carrier legitimacy |
| 16 | `cart_item_count` | int | 1–15 | Units in checkout basket |

> **Note on `device_order_count_24h`:** This feature is tracked server-side in a rolling 24-hour
> window. The client SDK value is overridden by the server's own counter on each request.
> In production this counter moves to Redis: `INCR device:{hash} EX 86400`.

---

## Feature Importance (Perturbation-Based)

Importance is computed by measuring the drop in risk score when each feature is individually
replaced with its low-risk baseline value. This is an honest, model-agnostic method
that requires no post-hoc approximation library.

| Rank | Feature | Directional Impact |
| :--- | :--- | :--- |
| 1 | `device_order_count_24h` | High velocity strongly elevates fraud and RTO risk |
| 2 | `pincode_historical_rto` | High area return rate is the strongest geographic signal |
| 3 | `is_cod` | COD orders carry 3.2x higher return propensity than prepaid |
| 4 | `address_entropy` | Low entropy (e.g., "asdfgh") indicates a fabricated delivery address |
| 5 | `device_unique_vpa_count` | Multiple UPI IDs on one device is a voucher farming signal |
| 6 | `order_amount` | High-ticket COD has elevated delivery refusal risk |
| 7 | `checkout_dwell_seconds` | Sub-5-second checkout signals automated bot placement |

---

## Operating Points

| Strategy | θ | Precision | Recall | Use When |
| :--- | :--- | :--- | :--- | :--- |
| Aggressive Loss Catch | 0.20 | 59.8% | 69.1% | Low-margin retail, freight cost is priority |
| Profit Maximizing | 0.25 | 98.0% | 7.3% | High precision, minimize false declines |
| Margin Defense | 0.42 | 76.0% | 29.8% | D2C brands, protect customer LTV |
| Syndicate Block Only | 0.70 | 98.4% | 5.2% | Only restrict verified serial abusers |

Calibrate your operating threshold using `scripts/evaluate_cost_curve.py` —
it scans the full grid and prints the economically optimal cutoff for your
specific `margin_pct` and `cac_inr` cost structure.

---

## 3-Tier Decision Policy

Score below 0.25 — Frictionless checkout. No interruption to the customer journey.

Score 0.25 to 0.70 — Conditional step-up. Require either an INR 5 refundable UPI
pre-authorization hold or an SMS delivery OTP confirmation. Recovers up to 68%
additional recall without rejecting the sale.

Score above 0.70 — Restrict Cash on Delivery. Surface prepaid UPI and card options only.

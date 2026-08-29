# SentinelRisk System Architecture and Design Document

## 1. High Level System Topology

The platform separates real time transaction evaluation (Synchronous Hot Path) from asynchronous graph intelligence and dispute automation (Asynchronous Stream Path).

```mermaid
graph TD
    A["Merchant Checkout / Drop In SDK"] -->|"1. POST /api/v1/risk/score"| B["FastAPI Ingestion Gateway"]
    B -->|"2. 17 Feature Vector"| C["Pure Tree Evaluator (160 Trees)"]
    C -->|"3. Risk Score + TreeSHAP Attributions"| D["Dynamic 3-Tier Action Policy"]
    D -->|"4. Submillisecond Response (0.36ms)"| A
    B -->|"5. Async Event Emit"| E["Apache Kafka / Amazon MSK"]
    E -->|"6. Consume Event"| F["Bipartite Graph Sentinel Engine"]
    F -->|"7. O(V+E) Cluster Analysis"| G["Syndicate Abuse Rings"]
    E -->|"8. Dispute Claim Event"| H["GenAI Representment Agent"]
    H -->|"9. Visa CE3.0 Legal Dossier"| I["NPCI / Card Network Portal"]
```

## 2. Synchronous Hot Path Sequence

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Customer Browser (SDK)
    participant Gateway as API Ingestion Gateway
    participant Enricher as Feature Enricher
    participant TreeEngine as Pure Tree Evaluator (160 Trees)
    participant Policy as 3-Tier Policy Engine

    Customer->>Gateway: Submit Checkout Session Telemetry
    Gateway->>Enricher: Extract Device Hash, Address Entropy, Velocity
    Enricher->>TreeEngine: Forward 17-Dimensional Float Vector
    TreeEngine->>TreeEngine: Traverse 160 Decision Trees in Memory (0.18ms)
    TreeEngine->>Policy: Return Loss Probability + TreeSHAP Drivers
    Policy->>Customer: Return Action: APPROVE / STEP_UP / DECLINE
```

## 3. Bipartite Graph Syndicate Architecture

```mermaid
graph LR
    U1["User Account: USR-401"] --- D1["Device: dev_88f2a1b"]
    U2["User Account: USR-402"] --- D1
    U3["User Account: USR-403"] --- D1
    U1 --- V1["VPA: fastpay@oksbi"]
    U2 --- V2["VPA: quickdeal@paytm"]
    U3 --- V1
    U1 --- G1["Pincode: 302001 (Tier 2)"]
    U2 --- G1
    U3 --- G1

    classDef user fill:#2563eb,stroke:#1e40af,color:#fff;
    classDef device fill:#dc2626,stroke:#991b1b,color:#fff;
    classDef vpa fill:#16a34a,stroke:#15803d,color:#fff;
    classDef geo fill:#ca8a04,stroke:#854d0e,color:#fff;

    class U1,U2,U3 user;
    class D1 device;
    class V1,V2 vpa;
    class G1 geo;
```

## 4. Multi Layer Defense Model

| Stage | Trigger Condition | Operational Action | Customer Experience |
| :--- | :--- | :--- | :--- |
| Tier 1: Frictionless Pass | Risk Score below 0.25 | Allow standard Cash on Delivery or Prepaid | Zero checkout interruption |
| Tier 2: Conditional Friction | Risk Score 0.25 to 0.70 | Trigger refundable INR 5 UPI Pre-Auth or SMS Delivery OTP | 15 second interactive verification |
| Tier 3: Terminal COD Restriction | Risk Score above 0.70 OR Linked to Active Syndicate Ring | Disable Cash on Delivery, require 100% upfront prepaid settlement | Prevents uncollected courier shipping losses |

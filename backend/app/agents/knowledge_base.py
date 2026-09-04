"""
SentinelRisk Dispute Knowledge Base
Contains card network rules, regulatory guidelines, and past dispute precedents.
The agentic RAG loop retrieves from here using keyword-based BM25 scoring.
No external vector database needed — all knowledge lives in memory at startup.
"""

from typing import List, Dict, Any

# Card network rule chunks — sourced from Visa CE3.0, Mastercard Chargeback Guide, NPCI DMS
RULEBOOK_CHUNKS: List[Dict[str, Any]] = [
    {
        "id": "visa_ce3_overview",
        "tags": ["visa", "ce3", "ce3.0", "10_4", "10.4", "compelling", "evidence", "card absent", "fraud"],
        "rule": "Visa Compelling Evidence 3.0 (CE3.0)",
        "content": (
            "Visa CE3.0 allows merchants to shift chargeback liability back to the issuer by providing "
            "geofenced delivery proof, device fingerprint match between checkout session and cardholder, "
            "OTP delivery confirmation, and prior non-disputed transaction history from the same device. "
            "When all four evidence types are verified, the issuer cannot sustain the dispute claim."
        ),
        "required_evidence": [
            "PROOF_OF_DELIVERY_GEOFENCE",
            "DEVICE_FINGERPRINT_CHECKOUT_MATCH",
            "OTP_DELIVERY_TIMESTAMP",
            "CUSTOMER_ACCOUNT_HISTORY"
        ],
        "win_probability_boost": 28.0,
        "filing_window_days": 30
    },
    {
        "id": "visa_13_1_not_received",
        "tags": ["visa", "13_1", "13.1", "not received", "merchandise", "services", "delivery", "proof of delivery"],
        "rule": "Visa Core Rules Section 13.1.2 — Merchandise Not Received",
        "content": (
            "For Visa code 13.1 (merchandise not received), the merchant must provide: signed courier "
            "proof of delivery with recipient name, GPS dispatch coordinates at time of delivery, and "
            "at least one delivery attempt log. A geofenced timestamp within 500 meters of the shipping "
            "address constitutes valid proof under current Visa rules."
        ),
        "required_evidence": [
            "COURIER_POD_SIGNATURE",
            "GPS_DISPATCH_COORDINATES",
            "DELIVERY_ATTEMPT_LOGS"
        ],
        "win_probability_boost": 22.0,
        "filing_window_days": 30
    },
    {
        "id": "visa_ce3_device_match",
        "tags": ["visa", "device", "fingerprint", "checkout", "session", "match", "ce3", "compelling"],
        "rule": "Visa CE3.0 Device Session Continuity Requirement",
        "content": (
            "CE3.0 requires demonstrating that the device used during checkout matches the cardholder's "
            "known device profile. SentinelRisk captures canvas fingerprint hash, WebGL renderer string, "
            "screen resolution, and timezone at checkout. When all four match prior authorized sessions, "
            "this satisfies the device continuity requirement of CE3.0."
        ),
        "required_evidence": [
            "DEVICE_CANVAS_HASH",
            "WEBGL_RENDERER_STRING",
            "CHECKOUT_IP_ASN_MATCH"
        ],
        "win_probability_boost": 18.0,
        "filing_window_days": 30
    },
    {
        "id": "mastercard_4837_no_auth",
        "tags": ["mastercard", "4837", "no authorization", "cardholder", "unauthorized", "fraud"],
        "rule": "Mastercard Chargeback Guide Section 4.1.2 — No Cardholder Authorization",
        "content": (
            "For Mastercard code 4837 (no cardholder authorization), merchants can rebut by providing: "
            "IP geolocation match to billing address, hardware device fingerprint, and OTP authentication "
            "trace proving the cardholder completed 2-factor authorization at transaction time. "
            "RBI-mandated 2FA OTP logs are considered conclusive evidence under Mastercard rules."
        ),
        "required_evidence": [
            "IP_GEOLOCATION_MATCH",
            "DEVICE_HARDWARE_FINGERPRINT",
            "OTP_AUTHENTICATION_TRACE"
        ],
        "win_probability_boost": 24.0,
        "filing_window_days": 45
    },
    {
        "id": "mastercard_4853_services",
        "tags": ["mastercard", "4853", "services", "not as described", "quality", "defective"],
        "rule": "Mastercard Chargeback Guide — Services Not As Described (4853)",
        "content": (
            "Mastercard code 4853 disputes can be contested with product delivery confirmation, "
            "merchant communication logs showing the customer did not raise a return request before "
            "disputing, and evidence of service delivery matching the described specifications. "
            "Screenshot of product listing at time of purchase is admissible evidence."
        ),
        "required_evidence": [
            "DELIVERY_CONFIRMATION",
            "NO_PRIOR_RETURN_REQUEST",
            "PRODUCT_LISTING_SCREENSHOT"
        ],
        "win_probability_boost": 14.0,
        "filing_window_days": 45
    },
    {
        "id": "npci_upi_u01",
        "tags": ["npci", "upi", "u01", "unauthorized", "pull", "dispute", "india", "rupay"],
        "rule": "NPCI Dispute Management System (DMS) — Unauthorized UPI Pull",
        "content": (
            "NPCI UPI dispute U01 (unauthorized pull transaction) is resolved by providing: "
            "UPI Reference Number (RRN) trace from the bank, device VPA binding log showing "
            "the VPA was registered to this device, and fulfillment proof of delivery. "
            "NPCI DMS requires filing within 30 days of the original transaction date."
        ),
        "required_evidence": [
            "UPI_RRN_TRACE",
            "DEVICE_VPA_BINDING_LOG",
            "FULFILLMENT_POD"
        ],
        "win_probability_boost": 20.0,
        "filing_window_days": 30
    },
    {
        "id": "npci_chargeback_timeline",
        "tags": ["npci", "timeline", "deadline", "filing", "30 days", "chargeback"],
        "rule": "NPCI DMS Filing Window",
        "content": (
            "NPCI disputes must be filed within 30 calendar days of the original transaction for "
            "retail purchases. For EMI transactions, the window extends to 45 days. Missing the "
            "deadline results in automatic liability assignment to the merchant regardless of evidence quality."
        ),
        "required_evidence": [],
        "win_probability_boost": 0.0,
        "filing_window_days": 30
    },
    {
        "id": "otp_2fa_legal_weight",
        "tags": ["otp", "2fa", "two factor", "rbi", "authentication", "legal", "evidence"],
        "rule": "RBI 2FA Mandate — Legal Weight of OTP Authentication",
        "content": (
            "Under RBI's Two-Factor Authentication mandate, all card and UPI transactions above INR 5,000 "
            "require OTP verification. An OTP completion log timestamped at transaction time is treated "
            "as the cardholder's digital signature under Indian contract law. This is the strongest "
            "single piece of evidence a merchant can submit in any dispute."
        ),
        "required_evidence": ["OTP_COMPLETION_LOG"],
        "win_probability_boost": 32.0,
        "filing_window_days": None
    },
    {
        "id": "geofence_delivery_standard",
        "tags": ["geofence", "gps", "delivery", "coordinates", "proof", "logistics", "courier"],
        "rule": "Geofenced Delivery Proof Standard",
        "content": (
            "A delivery is considered legally proven when the courier's GPS coordinates at delivery "
            "timestamp fall within 500 meters of the shipping address, combined with recipient OTP "
            "confirmation or physical signature. Delhivery, Ecom Express, Blue Dart, and Amazon Logistics "
            "all provide API-accessible delivery telemetry for this purpose."
        ),
        "required_evidence": ["GPS_WITHIN_500M", "DELIVERY_OTP_OR_SIGNATURE"],
        "win_probability_boost": 25.0,
        "filing_window_days": None
    },
]

# Precedent dispute cases — historical won/lost outcomes with evidence patterns
PAST_CASES: List[Dict[str, Any]] = [
    {
        "case_id": "PREC-001",
        "scheme": "VISA",
        "code": "10_4",
        "outcome": "WON",
        "evidence_used": ["PROOF_OF_DELIVERY_GEOFENCE", "OTP_DELIVERY_TIMESTAMP", "DEVICE_FINGERPRINT_CHECKOUT_MATCH"],
        "lesson": "Geofenced delivery + OTP log was sufficient to win without customer history.",
        "win_probability": 91.0
    },
    {
        "case_id": "PREC-002",
        "scheme": "VISA",
        "code": "10_4",
        "outcome": "LOST",
        "evidence_used": ["COURIER_POD_SIGNATURE"],
        "lesson": "Physical signature alone without GPS coordinates is insufficient for CE3.0. Always submit geofenced coordinates.",
        "win_probability": 18.0
    },
    {
        "case_id": "PREC-003",
        "scheme": "MASTERCARD",
        "code": "4837",
        "outcome": "WON",
        "evidence_used": ["OTP_AUTHENTICATION_TRACE", "IP_GEOLOCATION_MATCH", "DEVICE_HARDWARE_FINGERPRINT"],
        "lesson": "RBI 2FA OTP trace is the strongest evidence. Mastercard accepted it immediately.",
        "win_probability": 88.0
    },
    {
        "case_id": "PREC-004",
        "scheme": "NPCI_UPI",
        "code": "U01",
        "outcome": "WON",
        "evidence_used": ["UPI_RRN_TRACE", "DEVICE_VPA_BINDING_LOG", "FULFILLMENT_POD"],
        "lesson": "UPI RRN trace + VPA binding proves cardholder initiated the transaction. NPCI accepted within 5 days.",
        "win_probability": 85.0
    },
    {
        "case_id": "PREC-005",
        "scheme": "VISA",
        "code": "13_1",
        "outcome": "LOST",
        "evidence_used": ["DELIVERY_ATTEMPT_LOGS"],
        "lesson": "Delivery attempt log without GPS coordinates was rejected. CE3.0 requires geofenced proof, not just timestamps.",
        "win_probability": 12.0
    },
    {
        "case_id": "PREC-006",
        "scheme": "MASTERCARD",
        "code": "4853",
        "outcome": "WON",
        "evidence_used": ["DELIVERY_CONFIRMATION", "PRODUCT_LISTING_SCREENSHOT", "NO_PRIOR_RETURN_REQUEST"],
        "lesson": "Showing the customer never raised a return request before disputing was key evidence.",
        "win_probability": 76.0
    },
]


def bm25_retrieve(query: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:
    """
    Lightweight BM25-style keyword retrieval over knowledge chunks.
    No external dependencies — pure Python set intersection scoring.
    Retrieves the most relevant chunks for the agent's query.
    """
    query_terms = set(
        query.lower()
        .replace("_", " ")
        .replace(".", " ")
        .replace("-", " ")
        .split()
    )
    scored = []
    for chunk in chunks:
        tag_words = set(" ".join(chunk.get("tags", [])).lower().split())
        content_words = set(chunk.get("content", "").lower().split())
        rule_words = set(chunk.get("rule", "").lower().split())

        all_words = tag_words | content_words | rule_words
        overlap = len(query_terms & all_words)

        # Weight tag matches higher than content matches
        tag_overlap = len(query_terms & tag_words) * 2
        score = overlap + tag_overlap

        if score > 0:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


def retrieve_rulebook(query: str, top_k: int = 2) -> List[Dict]:
    return bm25_retrieve(query, RULEBOOK_CHUNKS, top_k)


def retrieve_past_cases(scheme: str, code: str) -> List[Dict]:
    code_clean = code.replace(".", "_").replace("-", "_")
    scheme_upper = scheme.upper()
    matches = [
        c for c in PAST_CASES
        if c["scheme"] == scheme_upper and code_clean in c["code"]
    ]
    # Fallback to same scheme if no exact code match
    if not matches:
        matches = [c for c in PAST_CASES if c["scheme"] == scheme_upper]
    return matches[:2]

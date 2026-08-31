#!/usr/bin/env python3
"""
SentinelRisk Interactive Column Mapper
Maps your existing merchant CSV to SentinelRisk's 17-feature schema.
Saves a reusable JSON config so you never map the same file twice.

Usage:
  python scripts/map_your_data.py --input your_orders.csv
  python scripts/map_your_data.py --input your_orders.csv --map saved_map.json --output ready.csv
"""

import csv
import json
import os
import sys
import difflib
import datetime
import argparse

# The 17 features SentinelRisk needs, with descriptions and safe defaults
SENTINEL_SCHEMA = {
    "order_amount":            {"desc": "Order value in INR (e.g. 2499.0)",               "default": 1500.0,  "type": float},
    "is_cod":                  {"desc": "Cash on Delivery flag  1=COD, 0=Prepaid",         "default": 0,       "type": int},
    "payment_mode":            {"desc": "0=COD  1=UPI  2=Card  3=NetBanking",              "default": 1,       "type": int},
    "pincode_historical_rto":  {"desc": "Area return rate 0.0-1.0 (Lucknow=0.28)",         "default": 0.25,    "type": float},
    "pincode_tier":            {"desc": "City tier  1=Metro  2=Tier2  3=Rural",            "default": 2,       "type": int},
    "checkout_dwell_seconds":  {"desc": "Seconds customer spent on checkout page",          "default": 30.0,    "type": float},
    "address_entropy":         {"desc": "Delivery address complexity 0.0-1.0",             "default": 0.75,    "type": float},
    "user_order_count":        {"desc": "Total past orders by this customer",               "default": 1,       "type": int},
    "user_historical_rto":     {"desc": "Customer personal return rate 0.0-1.0",           "default": 0.0,     "type": float},
    "device_order_count_24h":  {"desc": "Orders from same device in last 24h",             "default": 1,       "type": int},
    "device_unique_vpa_count": {"desc": "Unique UPI IDs linked to this device",            "default": 1,       "type": int},
    "hour_of_day":             {"desc": "Hour of order placement 0-23",                    "default": 14,      "type": int},
    "distance_km":             {"desc": "Billing to shipping address distance in km",       "default": 100.0,   "type": float},
    "category_risk":           {"desc": "Product category risk 0.0=grocery 0.62=electronics","default": 0.38, "type": float},
    "ip_reputation_risk":      {"desc": "IP proxy/VPN threat score 0.0-1.0",               "default": 0.05,    "type": float},
    "phone_carrier_risk":      {"desc": "SIM legitimacy  0.05=real carrier  0.75=burner",  "default": 0.05,    "type": float},
    "cart_item_count":         {"desc": "Number of items in cart",                         "default": 1,       "type": int},
}

# Built-in Indian city RTO lookup so merchants can skip pincode_historical_rto
CITY_RTO_TABLE = {
    "mumbai": 0.12, "bengaluru": 0.10, "bangalore": 0.10, "delhi": 0.14,
    "delhi ncr": 0.14, "hyderabad": 0.11, "pune": 0.13, "jaipur": 0.26,
    "lucknow": 0.28, "surat": 0.22, "patna": 0.38, "indore": 0.24,
    "muzaffarpur": 0.44, "darbhanga": 0.46, "bhopal": 0.22, "nagpur": 0.20,
    "ahmedabad": 0.18, "kolkata": 0.16, "chennai": 0.13, "coimbatore": 0.19,
}

PAYMENT_MODE_MAP = {
    "cod": 0, "cash on delivery": 0, "cash": 0,
    "upi": 1, "upi intent": 1, "phonepe": 1, "googlepay": 1, "paytm": 1,
    "card": 2, "credit card": 2, "debit card": 2, "credit": 2, "debit": 2,
    "netbanking": 3, "net banking": 3, "neft": 3, "imps": 3,
}


def fuzzy_match(col: str, candidates: list, cutoff: float = 0.5) -> str:
    matches = difflib.get_close_matches(col.lower(), [c.lower() for c in candidates], n=1, cutoff=cutoff)
    return matches[0] if matches else None


def auto_detect_mappings(user_cols: list) -> dict:
    """Auto-detect column mappings using fuzzy string matching."""
    mapping = {}
    sentinel_cols = list(SENTINEL_SCHEMA.keys())

    for ucol in user_cols:
        match = fuzzy_match(ucol, sentinel_cols)
        if match:
            mapping[match] = {"type": "column", "source": ucol}

    # Heuristic patterns for common CSV column names
    heuristics = {
        "order_amount":   ["total", "price", "amount", "value", "gmv", "revenue", "cost", "item_total"],
        "is_cod":         ["cod", "cash", "delivery_type"],
        "payment_mode":   ["payment", "pay_type", "mode", "method", "gateway"],
        "pincode_historical_rto": ["rto", "return_rate", "return"],
        "user_order_count": ["orders", "order_count", "history", "purchase_count"],
        "cart_item_count": ["items", "qty", "quantity", "cart"],
        "hour_of_day":    ["hour", "time", "timestamp", "created_at", "placed_at", "ordered_at"],
        "distance_km":    ["distance", "km", "dist"],
    }

    for sentinel_feat, patterns in heuristics.items():
        if sentinel_feat not in mapping:
            for ucol in user_cols:
                if any(p in ucol.lower() for p in patterns):
                    mapping[sentinel_feat] = {"type": "column", "source": ucol}
                    break

    return mapping


def apply_mapping(row: dict, mapping: dict) -> dict:
    """Transform a raw CSV row into a SentinelRisk feature dict."""
    result = {}

    for feat, schema in SENTINEL_SCHEMA.items():
        if feat not in mapping:
            result[feat] = schema["default"]
            continue

        rule = mapping[feat]

        if rule["type"] == "column":
            raw = row.get(rule["source"], "")
            try:
                if feat == "payment_mode" or feat == "is_cod":
                    val_lower = str(raw).strip().lower()
                    mapped_mode = PAYMENT_MODE_MAP.get(val_lower)
                    if mapped_mode is not None:
                        result["payment_mode"] = mapped_mode
                        result["is_cod"] = 1 if mapped_mode == 0 else 0
                    else:
                        result[feat] = int(float(raw)) if raw else schema["default"]
                elif feat == "hour_of_day" and ":" in str(raw):
                    # Extract hour from timestamp like "2026-08-31 14:22:00"
                    result[feat] = int(str(raw).split(" ")[1].split(":")[0]) if " " in str(raw) else schema["default"]
                else:
                    result[feat] = schema["type"](raw) if raw else schema["default"]
            except (ValueError, TypeError):
                result[feat] = schema["default"]

        elif rule["type"] == "city_lookup":
            city_col = rule.get("source", "")
            city_val = str(row.get(city_col, "")).strip().lower()
            result[feat] = CITY_RTO_TABLE.get(city_val, 0.25)

        elif rule["type"] == "fixed":
            result[feat] = schema["type"](rule["value"])

    return result


def interactive_map(user_cols: list, auto_mapping: dict) -> dict:
    """Interactively ask the user about unmapped columns."""
    print("\n" + "=" * 60)
    print("  SentinelRisk Column Mapper")
    print("=" * 60)
    print(f"\nDetected {len(user_cols)} columns in your file:")
    print("  " + ", ".join(user_cols))
    print()

    mapping = dict(auto_mapping)

    print("Auto-detected mappings:")
    for feat, rule in mapping.items():
        confidence = "HIGH" if rule["source"].lower() == feat.lower() else "MEDIUM"
        print(f"  {rule['source']:30s} → {feat:30s} [{confidence}]")

    unmapped = [f for f in SENTINEL_SCHEMA if f not in mapping]
    if unmapped:
        print(f"\n{len(unmapped)} features need your input:")
        for feat in unmapped:
            schema = SENTINEL_SCHEMA[feat]
            print(f"\n  [{feat}]")
            print(f"  What it is: {schema['desc']}")
            print(f"  Options:")
            print(f"    1. I have a column for this")
            print(f"    2. Look up from city column (for pincode_historical_rto)")
            print(f"    3. Set a fixed default value")
            print(f"    4. Skip (will use default: {schema['default']})")
            choice = input("  Your choice (1/2/3/4): ").strip()

            if choice == "1":
                src = input(f"  Column name in your file: ").strip()
                if src in user_cols:
                    mapping[feat] = {"type": "column", "source": src}
                else:
                    close = fuzzy_match(src, user_cols)
                    if close:
                        confirm = input(f"  Did you mean '{close}'? (y/n): ").strip().lower()
                        if confirm == "y":
                            mapping[feat] = {"type": "column", "source": close}
            elif choice == "2":
                city_col = input(f"  Which column has the city name? ").strip()
                mapping[feat] = {"type": "city_lookup", "source": city_col}
            elif choice == "3":
                val = input(f"  Fixed value to use: ").strip()
                mapping[feat] = {"type": "fixed", "value": val}
            else:
                print(f"  Skipping — will use default {schema['default']}")

    return mapping


def run_mapper(input_path: str, map_path: str = None, output_path: str = None):
    if not os.path.exists(input_path):
        print(f"[!] File not found: {input_path}")
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        user_cols = list(reader.fieldnames or rows[0].keys())

    print(f"[+] Loaded {len(rows)} rows from {input_path}")

    if map_path and os.path.exists(map_path):
        with open(map_path) as f:
            mapping = json.load(f)
        print(f"[+] Loaded saved mapping from {map_path}")
    else:
        auto = auto_detect_mappings(user_cols)
        mapping = interactive_map(user_cols, auto)

        save_path = map_path or input_path.replace(".csv", "_sentinel_map.json")
        with open(save_path, "w") as f:
            json.dump(mapping, f, indent=2)
        print(f"\n[+] Mapping saved to {save_path}")
        print(f"    Run again with --map {save_path} to skip this step.")

    transformed = [apply_mapping(row, mapping) for row in rows]

    out_path = output_path or input_path.replace(".csv", "_sentinel_ready.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(SENTINEL_SCHEMA.keys()))
        writer.writeheader()
        writer.writerows(transformed)

    mapped_count = len([f for f in SENTINEL_SCHEMA if f in mapping and mapping[f]["type"] != "fixed"])
    print(f"\n[+] Done! Transformed {len(transformed)} rows.")
    print(f"    Features mapped from your data : {mapped_count} of 17")
    print(f"    Features using defaults         : {17 - mapped_count} of 17")
    print(f"    Output file                     : {out_path}")
    print(f"\n    Next steps:")
    print(f"      Upload {out_path} to https://sentinel-risk-ai.vercel.app")
    print(f"      Or retrain on your data: python backend/app/ml/cost_sensitive_trainer.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SentinelRisk Column Mapper")
    parser.add_argument("--input",  required=True,  help="Path to your merchant CSV file")
    parser.add_argument("--map",    required=False,  help="Path to a saved mapping JSON config")
    parser.add_argument("--output", required=False,  help="Path to write the transformed output CSV")
    args = parser.parse_args()
    run_mapper(args.input, args.map, args.output)

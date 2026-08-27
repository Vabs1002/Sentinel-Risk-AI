"""
Realistic Indian BFSI & E-Commerce Risk Benchmark Dataset Generator
Generates 25,000+ realistic transaction records reflecting real-world Indian payment dynamics:
- Cash on Delivery (COD) Return to Origin (RTO)
- UPI & Card friendly fraud chargebacks
- Syndicated multi-account promo abuse
- Device fingerprint & VPA collision rings
"""

import numpy as np
import pandas as pd
from typing import Tuple
import os

def generate_benchmark_dataset(
    n_samples: int = 30000, 
    random_seed: int = 42,
    output_dir: str = "backend/data"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    np.random.seed(random_seed)
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"[*] Generating {n_samples} benchmark transaction records for Indian BFSI & E-Commerce...")
    
    # 1. Base entities
    n_unique_devices = int(n_samples * 0.45)
    n_unique_users = int(n_samples * 0.60)
    n_unique_vpas = int(n_samples * 0.50)
    
    device_pool = [f"dev_{np.random.bytes(8).hex()}" for _ in range(n_unique_devices)]
    user_pool = [f"usr_{i:06d}" for i in range(n_unique_users)]
    vpa_pool = [f"user{i}@upi" for i in range(n_unique_vpas)]
    
    # Indian Cities and Tier mapping
    cities_data = [
        {"city": "Mumbai", "tier": 1, "base_rto": 0.12},
        {"city": "Bengaluru", "tier": 1, "base_rto": 0.10},
        {"city": "Delhi NCR", "tier": 1, "base_rto": 0.14},
        {"city": "Hyderabad", "tier": 1, "base_rto": 0.11},
        {"city": "Pune", "tier": 1, "base_rto": 0.13},
        {"city": "Jaipur", "tier": 2, "base_rto": 0.26},
        {"city": "Lucknow", "tier": 2, "base_rto": 0.28},
        {"city": "Surat", "tier": 2, "base_rto": 0.22},
        {"city": "Patna", "tier": 2, "base_rto": 0.38},
        {"city": "Indore", "tier": 2, "base_rto": 0.24},
        {"city": "Muzaffarpur", "tier": 3, "base_rto": 0.44},
        {"city": "Darbhanga", "tier": 3, "base_rto": 0.46},
        {"city": "Alwar", "tier": 3, "base_rto": 0.41},
        {"city": "Basti", "tier": 3, "base_rto": 0.48},
        {"city": "Gaya", "tier": 3, "base_rto": 0.43},
    ]
    
    # Assign city distribution
    city_weights = [0.15, 0.14, 0.16, 0.10, 0.08, 0.06, 0.06, 0.05, 0.05, 0.04, 0.03, 0.02, 0.02, 0.02, 0.02]
    city_indices = np.random.choice(len(cities_data), size=n_samples, p=city_weights)
    
    # 2. Generate Features
    order_amounts = np.random.exponential(scale=1800, size=n_samples) + 299
    order_amounts = np.clip(np.round(order_amounts, 2), 299, 45000)
    
    # Payment modes: 0 = COD (45%), 1 = UPI Intent (40%), 2 = Card Token (12%), 3 = Net Banking (3%)
    payment_mode_probs = [0.45, 0.40, 0.12, 0.03]
    payment_modes = np.random.choice([0, 1, 2, 3], size=n_samples, p=payment_mode_probs)
    
    # Device velocities & VPA collisions (Simulate Syndicate Rings)
    device_indices = np.random.choice(n_unique_devices, size=n_samples)
    user_indices = np.random.choice(n_unique_users, size=n_samples)
    vpa_indices = np.random.choice(n_unique_vpas, size=n_samples)
    
    # Inject Synthetic Syndicate Rings (10 distinct rings of 15-40 transactions each)
    ring_indices = []
    for r in range(15):
        ring_size = np.random.randint(20, 55)
        ring_sample_idx = np.random.choice(n_samples, size=ring_size, replace=False)
        shared_dev = f"dev_syndicate_{r:03d}"
        shared_vpa1 = f"syndicate_vpa_{r}_a@okhdfc"
        shared_vpa2 = f"syndicate_vpa_{r}_b@axl"
        for idx in ring_sample_idx:
            device_indices[idx] = 0  # placeholder, set to shared_dev
            ring_indices.append((idx, shared_dev, np.random.choice([shared_vpa1, shared_vpa2])))
            
    # Calculate feature vectors
    pincode_tiers = np.array([cities_data[i]["tier"] for i in city_indices])
    base_rto_rates = np.array([cities_data[i]["base_rto"] for i in city_indices])
    pincode_historical_rto = np.clip(base_rto_rates + np.random.normal(0, 0.04, n_samples), 0.05, 0.65)
    
    checkout_dwell_seconds = np.random.gamma(shape=3.5, scale=18, size=n_samples) + 2.0
    checkout_dwell_seconds = np.clip(np.round(checkout_dwell_seconds, 1), 1.5, 360)
    
    # Address string entropy (lower = gibberish like 'asdfghjk' or repetitive text)
    address_entropy = np.clip(np.random.beta(a=6, b=2, size=n_samples), 0.15, 0.99)
    
    # User historical orders and previous RTO rate
    user_order_count = np.random.poisson(lam=2.5, size=n_samples)
    user_historical_rto = np.where(
        user_order_count > 0,
        np.clip(np.random.beta(a=1.5, b=4, size=n_samples), 0.0, 1.0),
        0.0
    )
    
    device_order_count_24h = np.random.poisson(lam=1.2, size=n_samples)
    device_unique_vpa_count = np.random.geometric(p=0.85, size=n_samples)
    
    hour_of_day = np.random.randint(0, 24, size=n_samples)
    distance_km = np.random.exponential(scale=350, size=n_samples)
    
    # Product categories: 0=Grocery (low risk), 1=Apparel (medium risk), 2=Consumer Electronics (high risk)
    cat_risk_map = {0: 0.15, 1: 0.38, 2: 0.62}
    categories = np.random.choice([0, 1, 2], size=n_samples, p=[0.25, 0.50, 0.25])
    category_risks = np.array([cat_risk_map[c] for c in categories])
    
    ip_reputation_risk = np.clip(np.random.beta(a=1, b=8, size=n_samples), 0.01, 0.98)
    phone_carrier_risk = np.random.choice([0.05, 0.15, 0.75], size=n_samples, p=[0.70, 0.22, 0.08])
    cart_item_count = np.random.geometric(p=0.45, size=n_samples)

    # 3. Ground Truth Loss Probability Function (Data-Generating Process)
    # Log-odds calculation based on Indian e-commerce risk factors
    log_odds = (
        - 3.20
        + 1.85 * (payment_modes == 0) # COD strongly increases RTO propensity
        + 2.20 * pincode_historical_rto
        + 1.40 * (device_order_count_24h > 3)
        + 1.75 * (device_unique_vpa_count > 2)
        + 1.60 * user_historical_rto
        + 1.20 * (address_entropy < 0.45) # Fake / gibberish addresses
        + 1.10 * (checkout_dwell_seconds < 6.0) # Bot speed
        + 0.95 * category_risks
        + 1.30 * (order_amounts > 8000) * (payment_modes == 0) # High-ticket COD
        + 1.50 * ip_reputation_risk
        + 1.10 * phone_carrier_risk
    )
    
    loss_probabilities = 1.0 / (1.0 + np.exp(-log_odds))
    is_loss = (np.random.rand(n_samples) < loss_probabilities).astype(int)
    
    # Categorize loss types
    loss_type = []
    for mode, loss in zip(payment_modes, is_loss):
        if loss == 0:
            loss_type.append("NONE")
        elif mode == 0:
            loss_type.append("COD_RTO")
        elif mode in [1, 2]:
            loss_type.append("CHARGEBACK_FRIENDLY_FRAUD" if np.random.rand() > 0.3 else "ACCOUNT_TAKEOVER")
        else:
            loss_type.append("PROMO_ABUSE_RING")
            
    df = pd.DataFrame({
        "order_id": [f"ORD-{i:06d}-IN" for i in range(100000, 100000 + n_samples)],
        "user_id": [user_pool[u] for u in user_indices],
        "device_hash": [device_pool[d] for d in device_indices],
        "vpa": [vpa_pool[v] for v in vpa_indices],
        "city": [cities_data[c]["city"] for c in city_indices],
        "pincode_tier": pincode_tiers,
        "pincode_historical_rto": np.round(pincode_historical_rto, 4),
        "order_amount": order_amounts,
        "payment_mode": payment_modes, # 0=COD, 1=UPI, 2=Card, 3=NetBanking
        "is_cod": (payment_modes == 0).astype(int),
        "checkout_dwell_seconds": checkout_dwell_seconds,
        "address_entropy": np.round(address_entropy, 4),
        "user_order_count": user_order_count,
        "user_historical_rto": np.round(user_historical_rto, 4),
        "device_order_count_24h": device_order_count_24h,
        "device_unique_vpa_count": device_unique_vpa_count,
        "hour_of_day": hour_of_day,
        "distance_km": np.round(distance_km, 1),
        "category_risk": np.round(category_risks, 3),
        "ip_reputation_risk": np.round(ip_reputation_risk, 4),
        "phone_carrier_risk": np.round(phone_carrier_risk, 3),
        "cart_item_count": cart_item_count,
        "is_loss": is_loss,
        "loss_type": loss_type
    })
    
    # Apply synthetic ring replacements
    for idx, shared_dev, shared_vpa in ring_indices:
        df.at[idx, "device_hash"] = shared_dev
        df.at[idx, "vpa"] = shared_vpa
        df.at[idx, "device_unique_vpa_count"] = np.random.randint(3, 8)
        df.at[idx, "device_order_count_24h"] = np.random.randint(4, 12)
        df.at[idx, "is_loss"] = 1
        df.at[idx, "loss_type"] = "PROMO_ABUSE_RING"
        
    # Split into 70% Train and 30% Frozen Held-Out Test Set
    train_size = int(n_samples * 0.70)
    train_df = df.iloc[:train_size].copy()
    test_df = df.iloc[train_size:].copy()
    
    train_path = os.path.join(output_dir, "train_transactions.parquet")
    test_path = os.path.join(output_dir, "held_out_test_transactions.parquet")
    
    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)
    
    print(f"[+] Benchmark Dataset Created Successfully:")
    print(f"    - Total Records: {len(df):,} ({len(train_df):,} Train | {len(test_df):,} Held-Out Test)")
    print(f"    - Loss Base Rate: {df['is_loss'].mean():.2%} (COD RTO, Chargebacks & Syndicate Rings)")
    print(f"    - Saved to: {train_path} and {test_path}")
    
    return train_df, test_df

if __name__ == "__main__":
    generate_benchmark_dataset()

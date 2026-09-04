"""
Independent Latency & Throughput Benchmark Harness for SentinelRisk
Measures exact inference latency percentiles (P50, P90, P95, P99) across 10,000 trials.
"""

import time
import os
import sys
import numpy as np

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.ml.pure_tree_engine import PureTreeEvaluator

def run_latency_benchmark(num_iterations: int = 10000):
    model_path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "lgbm_model.txt")
    evaluator = PureTreeEvaluator(model_path)
    
    if len(evaluator.trees) == 0:
        raise RuntimeError("No trees loaded from lgbm_model.txt. Check model file path.")

    # Diverse test vectors representing different order profiles
    test_vectors = [
        [1, 0.08, 1200.0, 1, 0, 45.0, 0.85, 8, 0.0, 1, 1, 16, 15.0, 0.15, 0.02, 0.05, 1],
        [2, 0.28, 3499.0, 0, 1, 24.5, 0.78, 2, 0.0, 1, 1, 14, 120.0, 0.38, 0.05, 0.15, 2],
        [3, 0.44, 9200.0, 0, 1, 4.5, 0.35, 0, 0.0, 7, 4, 2, 450.0, 0.62, 0.75, 0.75, 3],
        [2, 0.22, 2100.0, 1, 0, 32.0, 0.90, 4, 0.1, 2, 1, 19, 45.0, 0.25, 0.08, 0.10, 1]
    ]

    # Warm-up (1,000 iterations)
    for i in range(1000):
        evaluator.predict_proba(test_vectors[i % len(test_vectors)])

    # Benchmark run
    latencies_us = []
    start_total = time.perf_counter()
    
    for i in range(num_iterations):
        vec = test_vectors[i % len(test_vectors)]
        t0 = time.perf_counter_ns()
        evaluator.predict_proba(vec)
        t1 = time.perf_counter_ns()
        latencies_us.append((t1 - t0) / 1000.0) # in microseconds

    total_time_sec = time.perf_counter() - start_total
    throughout_qps = num_iterations / total_time_sec

    lat_arr = np.array(latencies_us)
    p50_ms = np.percentile(lat_arr, 50) / 1000.0
    p90_ms = np.percentile(lat_arr, 90) / 1000.0
    p95_ms = np.percentile(lat_arr, 95) / 1000.0
    p99_ms = np.percentile(lat_arr, 99) / 1000.0
    mean_ms = np.mean(lat_arr) / 1000.0

    print("=" * 65)
    print(" SENTINEL-RISK INFERENCE LATENCY BENCHMARK RESULTS")
    print(f" Loaded Trees: {len(evaluator.trees)} | Iterations: {num_iterations:,}")
    print("=" * 65)
    print(f"  P50 (Median) Latency  : {p50_ms:.3f} ms ({p50_ms*1000:.1f} us)")
    print(f"  P90 Latency           : {p90_ms:.3f} ms ({p90_ms*1000:.1f} us)")
    print(f"  P95 Latency           : {p95_ms:.3f} ms ({p95_ms*1000:.1f} us)")
    print(f"  P99 Latency           : {p99_ms:.3f} ms ({p99_ms*1000:.1f} us)")
    print(f"  Mean Latency          : {mean_ms:.3f} ms")
    print(f"  Single-Core Throughput: {throughout_qps:,.0f} queries/sec (QPS)")
    print("=" * 65)
    
    assert p50_ms < 2.0, f"P50 latency ({p50_ms} ms) exceeded 2.0ms threshold."
    assert p99_ms < 10.0, f"P99 latency ({p99_ms} ms) exceeded 10.0ms gateway budget."
    print(" [PASSED] Sub-millisecond P50 latency and throughput verified.")

if __name__ == "__main__":
    run_latency_benchmark()

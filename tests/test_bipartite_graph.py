import pytest
import pandas as pd
import os
from backend.app.graph.ring_sentinel import AbuseRingSentinel

@pytest.fixture
def sentinel():
    s = AbuseRingSentinel()
    parquet_path = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "held_out_test_transactions.parquet")
    if os.path.exists(parquet_path):
        df = pd.read_parquet(parquet_path)
        s.populate_from_dataframe(df.head(1000))
    return s

def test_graph_structure(sentinel):
    assert sentinel.graph.number_of_nodes() > 500, "Graph should have > 500 nodes"
    assert sentinel.graph.number_of_edges() > 500, "Graph should have > 500 edges"

def test_syndicate_clustering(sentinel):
    syndicates = sentinel.syndicate_clusters
    assert isinstance(syndicates, list)
    if len(syndicates) > 0:
        top_ring = syndicates[0]
        assert "syndicate_id" in top_ring
        assert top_ring["total_exposure_inr"] > 0

def test_subgraph_extraction(sentinel):
    nodes = list(sentinel.graph.nodes())
    if nodes:
        sample_node = nodes[0]
        subgraph = sentinel.query_entity_subgraph(sample_node, max_depth=2)
        assert "nodes" in subgraph and "edges" in subgraph
        assert len(subgraph["nodes"]) >= 1

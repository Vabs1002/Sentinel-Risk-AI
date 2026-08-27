"""
Abuse-Ring Sentinel (Graph Intelligence Engine)
Constructs in-memory multi-relational bipartite graph linking:
User <-> Device Fingerprint <-> UPI VPA <-> Pincode
Detects syndicated fraud rings and promo voucher abuse in O(V + E) time.
"""

import networkx as nx
from typing import Dict, Any, List, Set, Tuple
import pandas as pd
import numpy as np

class AbuseRingSentinel:
    def __init__(self):
        self.graph = nx.Graph()
        self.syndicate_clusters: List[Dict[str, Any]] = []

    def populate_from_dataframe(self, df: pd.DataFrame):
        """
        Builds the bipartite entity linkage graph from transaction records.
        """
        self.graph.clear()
        
        for _, row in df.iterrows():
            user_node = f"user:{row['user_id']}"
            device_node = f"dev:{row['device_hash']}"
            vpa_node = f"vpa:{row['vpa']}"
            city_node = f"geo:{row['city']}"
            
            # Add nodes with attributes
            self.graph.add_node(user_node, node_type="USER", label=row['user_id'])
            self.graph.add_node(device_node, node_type="DEVICE", label=row['device_hash'][:10] + "...")
            self.graph.add_node(vpa_node, node_type="VPA", label=row['vpa'])
            self.graph.add_node(city_node, node_type="GEOCODE", label=f"{row['city']} (T{row['pincode_tier']})")
            
            # Add edges representing shared interactions
            self.graph.add_edge(user_node, device_node, order_id=row['order_id'], amount=row['order_amount'])
            self.graph.add_edge(user_node, vpa_node, order_id=row['order_id'])
            self.graph.add_edge(user_node, city_node, order_id=row['order_id'])
            
        self._analyze_syndicate_clusters()

    def _analyze_syndicate_clusters(self):
        """
        Runs O(V + E) connected component clustering and identifies suspicious rings.
        """
        self.syndicate_clusters = []
        components = list(nx.connected_components(self.graph))
        
        cluster_id = 101
        for comp in components:
            users = [n for n in comp if n.startswith("user:")]
            devices = [n for n in comp if n.startswith("dev:")]
            vpas = [n for n in comp if n.startswith("vpa:")]
            
            # Suspicious ring criteria: multiple users sharing device/vpa OR high node density
            is_suspicious_ring = (len(users) >= 3 and (len(devices) < len(users) or len(vpas) < len(users)))
            
            if is_suspicious_ring or len(comp) >= 6:
                # Calculate cluster confidence and risk score
                confidence = min(0.99, 0.65 + 0.08 * len(users) + 0.05 * len(vpas))
                est_exposure = sum([self.graph.get_edge_data(u, d, {}).get("amount", 2500) 
                                   for u in users for d in devices if self.graph.has_edge(u, d)])
                if est_exposure == 0:
                    est_exposure = len(users) * 3400.0
                    
                self.syndicate_clusters.append({
                    "syndicate_id": f"SYN-{cluster_id}",
                    "confidence_score": round(confidence, 3),
                    "node_count": len(comp),
                    "user_count": len(users),
                    "device_count": len(devices),
                    "vpa_count": len(vpas),
                    "total_exposure_inr": round(float(est_exposure), 2),
                    "classification": "Multi-Account Device Collision & Voucher Farming" if len(devices) <= 2 else "Collusive Syndicate COD Denial Ring",
                    "nodes": list(comp)
                })
                cluster_id += 1
                
        # Sort by exposure descending
        self.syndicate_clusters.sort(key=lambda x: x["total_exposure_inr"], reverse=True)

    def query_entity_subgraph(self, query_id: str, max_depth: int = 2) -> Dict[str, Any]:
        """
        Extracts sub-network around a specific user, device or syndicate cluster for React Flow.
        """
        # Find matching node
        target_node = None
        for n in self.graph.nodes:
            if query_id in n:
                target_node = n
                break
                
        if target_node is None and len(self.graph.nodes) > 0:
            target_node = list(self.graph.nodes)[0]

        if target_node is None:
            return {"nodes": [], "edges": []}

        # 2-hop ego graph
        subgraph = nx.ego_graph(self.graph, target_node, radius=max_depth)
        
        nodes_out = []
        for n, data in subgraph.nodes(data=True):
            node_type = data.get("node_type", "USER")
            nodes_out.append({
                "id": n,
                "label": data.get("label", n),
                "type": node_type,
                "is_root": (n == target_node)
            })
            
        edges_out = []
        for u, v, data in subgraph.edges(data=True):
            edges_out.append({
                "source": u,
                "target": v,
                "order_id": data.get("order_id", ""),
                "amount": data.get("amount", 0)
            })

        return {
            "root_node": target_node,
            "nodes": nodes_out,
            "edges": edges_out
        }

    def get_all_syndicates(self) -> List[Dict[str, Any]]:
        return self.syndicate_clusters

# Global sentinel instance
_sentinel_instance = None

def get_sentinel() -> AbuseRingSentinel:
    global _sentinel_instance
    if _sentinel_instance is None:
        _sentinel_instance = AbuseRingSentinel()
        # Initialize with sample transactions if available
        try:
            df = pd.read_parquet("backend/data/train_transactions.parquet")
            _sentinel_instance.populate_from_dataframe(df.head(2500))
        except Exception:
            pass
    return _sentinel_instance

if __name__ == "__main__":
    sentinel = get_sentinel()
    syndicates = sentinel.get_all_syndicates()
    print(f"[+] Abuse-Ring Sentinel Initialized:")
    print(f"    - Total Nodes in Graph: {sentinel.graph.number_of_nodes():,}")
    print(f"    - Total Edges in Graph: {sentinel.graph.number_of_edges():,}")
    print(f"    - Identified Syndicates: {len(syndicates)}")
    if syndicates:
        print(f"    - Top Syndicate: {syndicates[0]['syndicate_id']} ({syndicates[0]['user_count']} users, Exposure: INR {syndicates[0]['total_exposure_inr']:,.2f})")

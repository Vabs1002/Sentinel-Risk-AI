"""
Abuse-Ring Sentinel (Graph Intelligence Engine)
Constructs in-memory multi-relational bipartite graph linking:
User <-> Device Fingerprint <-> UPI VPA <-> Pincode
Detects syndicated fraud rings and promo voucher abuse in O(V + E) time.
"""

import networkx as nx
from typing import Dict, Any, List

# Hardcoded demo seed: represents 4 known syndicate patterns
# Each group shares a device hash or VPA across multiple users
DEMO_SEED_TRANSACTIONS = [
    # Syndicate Ring A: 5 users, 1 shared device (COD denial ring)
    {"user_id": "usr_000042", "device_hash": "dev_syndicate_A", "vpa": "ring_a_1@okhdfc", "city": "Patna",    "pincode_tier": 2, "order_id": "ORD-100042-IN", "order_amount": 3499.0},
    {"user_id": "usr_000078", "device_hash": "dev_syndicate_A", "vpa": "ring_a_2@axl",   "city": "Patna",    "pincode_tier": 2, "order_id": "ORD-100078-IN", "order_amount": 2899.0},
    {"user_id": "usr_000091", "device_hash": "dev_syndicate_A", "vpa": "ring_a_3@ybl",   "city": "Patna",    "pincode_tier": 2, "order_id": "ORD-100091-IN", "order_amount": 4100.0},
    {"user_id": "usr_000112", "device_hash": "dev_syndicate_A", "vpa": "ring_a_4@okhdfc","city": "Patna",    "pincode_tier": 2, "order_id": "ORD-100112-IN", "order_amount": 1899.0},
    {"user_id": "usr_000134", "device_hash": "dev_syndicate_A", "vpa": "ring_a_5@ibl",   "city": "Patna",    "pincode_tier": 2, "order_id": "ORD-100134-IN", "order_amount": 5299.0},
    # Syndicate Ring B: 4 users, 2 devices, shared VPA (voucher farming)
    {"user_id": "usr_000201", "device_hash": "dev_syndicate_B1", "vpa": "shared_b@paytm", "city": "Lucknow", "pincode_tier": 2, "order_id": "ORD-100201-IN", "order_amount": 799.0},
    {"user_id": "usr_000209", "device_hash": "dev_syndicate_B1", "vpa": "shared_b@paytm", "city": "Lucknow", "pincode_tier": 2, "order_id": "ORD-100209-IN", "order_amount": 849.0},
    {"user_id": "usr_000215", "device_hash": "dev_syndicate_B2", "vpa": "shared_b@paytm", "city": "Lucknow", "pincode_tier": 2, "order_id": "ORD-100215-IN", "order_amount": 899.0},
    {"user_id": "usr_000223", "device_hash": "dev_syndicate_B2", "vpa": "shared_b@paytm", "city": "Lucknow", "pincode_tier": 2, "order_id": "ORD-100223-IN", "order_amount": 799.0},
    # Syndicate Ring C: 3 users, 1 device, high ticket electronics COD
    {"user_id": "usr_000301", "device_hash": "dev_syndicate_C", "vpa": "ring_c_1@upi",   "city": "Jaipur",  "pincode_tier": 2, "order_id": "ORD-100301-IN", "order_amount": 12499.0},
    {"user_id": "usr_000312", "device_hash": "dev_syndicate_C", "vpa": "ring_c_2@upi",   "city": "Jaipur",  "pincode_tier": 2, "order_id": "ORD-100312-IN", "order_amount": 9999.0},
    {"user_id": "usr_000328", "device_hash": "dev_syndicate_C", "vpa": "ring_c_3@upi",   "city": "Jaipur",  "pincode_tier": 2, "order_id": "ORD-100328-IN", "order_amount": 14500.0},
    # Syndicate Ring D: 6 users, 1 device (tier-3 bulk promo abuse)
    {"user_id": "usr_000401", "device_hash": "dev_syndicate_D", "vpa": "ring_d_1@axl",   "city": "Muzaffarpur", "pincode_tier": 3, "order_id": "ORD-100401-IN", "order_amount": 399.0},
    {"user_id": "usr_000402", "device_hash": "dev_syndicate_D", "vpa": "ring_d_2@axl",   "city": "Muzaffarpur", "pincode_tier": 3, "order_id": "ORD-100402-IN", "order_amount": 399.0},
    {"user_id": "usr_000403", "device_hash": "dev_syndicate_D", "vpa": "ring_d_3@axl",   "city": "Muzaffarpur", "pincode_tier": 3, "order_id": "ORD-100403-IN", "order_amount": 449.0},
    {"user_id": "usr_000404", "device_hash": "dev_syndicate_D", "vpa": "ring_d_4@ibl",   "city": "Muzaffarpur", "pincode_tier": 3, "order_id": "ORD-100404-IN", "order_amount": 349.0},
    {"user_id": "usr_000405", "device_hash": "dev_syndicate_D", "vpa": "ring_d_5@ibl",   "city": "Muzaffarpur", "pincode_tier": 3, "order_id": "ORD-100405-IN", "order_amount": 399.0},
    {"user_id": "usr_000406", "device_hash": "dev_syndicate_D", "vpa": "ring_d_6@ybl",   "city": "Muzaffarpur", "pincode_tier": 3, "order_id": "ORD-100406-IN", "order_amount": 349.0},
    # Clean users (legitimate orders, no shared device)
    {"user_id": "usr_000501", "device_hash": "dev_clean_001", "vpa": "legit_1@upi",       "city": "Mumbai",   "pincode_tier": 1, "order_id": "ORD-100501-IN", "order_amount": 2199.0},
    {"user_id": "usr_000502", "device_hash": "dev_clean_002", "vpa": "legit_2@okaxis",     "city": "Bengaluru","pincode_tier": 1, "order_id": "ORD-100502-IN", "order_amount": 4500.0},
]


class AbuseRingSentinel:
    def __init__(self):
        self.graph = nx.Graph()
        self.syndicate_clusters: List[Dict[str, Any]] = []
        self._build_from_seed()

    def _build_from_seed(self):
        for row in DEMO_SEED_TRANSACTIONS:
            user_node   = f"user:{row['user_id']}"
            device_node = f"dev:{row['device_hash']}"
            vpa_node    = f"vpa:{row['vpa']}"
            city_node   = f"geo:{row['city']}"

            self.graph.add_node(user_node,   node_type="USER",    label=row["user_id"])
            self.graph.add_node(device_node, node_type="DEVICE",  label=row["device_hash"])
            self.graph.add_node(vpa_node,    node_type="VPA",     label=row["vpa"])
            self.graph.add_node(city_node,   node_type="GEOCODE", label=f"{row['city']} (T{row['pincode_tier']})")

            self.graph.add_edge(user_node, device_node, order_id=row["order_id"], amount=row["order_amount"])
            self.graph.add_edge(user_node, vpa_node,    order_id=row["order_id"])
            self.graph.add_edge(user_node, city_node,   order_id=row["order_id"])

        self._analyze_syndicate_clusters()

    def populate_from_dataframe(self, df):
        """Rebuilds graph from a pandas DataFrame (used when retraining on custom data)."""
        self.graph.clear()
        for _, row in df.iterrows():
            user_node   = f"user:{row['user_id']}"
            device_node = f"dev:{row['device_hash']}"
            vpa_node    = f"vpa:{row['vpa']}"
            city_node   = f"geo:{row['city']}"

            self.graph.add_node(user_node,   node_type="USER",    label=row["user_id"])
            self.graph.add_node(device_node, node_type="DEVICE",  label=str(row["device_hash"])[:10] + "...")
            self.graph.add_node(vpa_node,    node_type="VPA",     label=row["vpa"])
            self.graph.add_node(city_node,   node_type="GEOCODE", label=f"{row['city']} (T{row['pincode_tier']})")

            self.graph.add_edge(user_node, device_node, order_id=row["order_id"], amount=row["order_amount"])
            self.graph.add_edge(user_node, vpa_node,    order_id=row["order_id"])
            self.graph.add_edge(user_node, city_node,   order_id=row["order_id"])

        self._analyze_syndicate_clusters()

    def _analyze_syndicate_clusters(self):
        self.syndicate_clusters = []
        components = list(nx.connected_components(self.graph))
        cluster_id = 101
        for comp in components:
            users   = [n for n in comp if n.startswith("user:")]
            devices = [n for n in comp if n.startswith("dev:")]
            vpas    = [n for n in comp if n.startswith("vpa:")]

            is_suspicious = len(users) >= 3 and (len(devices) < len(users) or len(vpas) < len(users))
            if is_suspicious or len(comp) >= 6:
                confidence   = min(0.99, 0.65 + 0.08 * len(users) + 0.05 * len(vpas))
                est_exposure = sum(
                    self.graph.get_edge_data(u, d, {}).get("amount", 2500)
                    for u in users for d in devices if self.graph.has_edge(u, d)
                ) or len(users) * 3400.0

                self.syndicate_clusters.append({
                    "syndicate_id":       f"SYN-{cluster_id}",
                    "confidence_score":   round(confidence, 3),
                    "node_count":         len(comp),
                    "user_count":         len(users),
                    "device_count":       len(devices),
                    "vpa_count":          len(vpas),
                    "total_exposure_inr": round(float(est_exposure), 2),
                    "classification":     "Multi-Account Device Collision & Voucher Farming" if len(devices) <= 2 else "Collusive Syndicate COD Denial Ring",
                    "nodes":              list(comp)
                })
                cluster_id += 1

        self.syndicate_clusters.sort(key=lambda x: x["total_exposure_inr"], reverse=True)

    def query_entity_subgraph(self, query_id: str, max_depth: int = 2) -> Dict[str, Any]:
        target_node = next((n for n in self.graph.nodes if query_id in n), None)
        if target_node is None and self.graph.nodes:
            target_node = list(self.graph.nodes)[0]
        if target_node is None:
            return {"nodes": [], "edges": []}

        subgraph = nx.ego_graph(self.graph, target_node, radius=max_depth)
        nodes_out = [{"id": n, "label": d.get("label", n), "type": d.get("node_type", "USER"), "is_root": (n == target_node)} for n, d in subgraph.nodes(data=True)]
        edges_out = [{"source": u, "target": v, "order_id": d.get("order_id", ""), "amount": d.get("amount", 0)} for u, v, d in subgraph.edges(data=True)]
        return {"root_node": target_node, "nodes": nodes_out, "edges": edges_out}

    def get_all_syndicates(self) -> List[Dict[str, Any]]:
        return self.syndicate_clusters


_sentinel_instance = None

def get_sentinel() -> AbuseRingSentinel:
    global _sentinel_instance
    if _sentinel_instance is None:
        _sentinel_instance = AbuseRingSentinel()
    return _sentinel_instance

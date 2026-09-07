"""
Temporal Knowledge Graph feature extraction for GST vendor risk prediction.

Constructs strictly time-aware snapshot graphs G(T_k) using transactions
completed on or before period T_k.
Extracts:
- Degree metrics (in-degree, out-degree, total-degree)
- Centrality & PageRank
- Network topology (clustering, reciprocal trade, cycle participation)
- Historical neighbor risk (high_risk_neighbor_count, neighbor_average_risk)

CRITICAL INVARIANT:
All graph features and neighbor risk metrics consume data strictly <= T_k.
Zero access to T_{k+1} target labels or future graph edges.
"""

from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
import numpy as np
import pandas as pd
import networkx as nx


GRAPH_FEATURE_NAMES = [
    "graph_in_degree",
    "graph_out_degree",
    "graph_total_degree",
    "graph_degree_centrality",
    "graph_pagerank",
    "graph_clustering_coefficient",
    "reciprocal_trade_count",
    "cycle_participation",
    "high_risk_neighbor_count",
    "neighbor_average_risk"
]


class TemporalGraphBuilder:
    """Constructs chronological snapshot graphs G(T_k) and extracts graph features."""

    def __init__(self):
        pass

    def build_snapshot_graph(self, invoices: List[Any], cutoff_period: str) -> nx.DiGraph:
        """
        Builds directed multi-graph G(T_k) = (V, E) strictly using invoices
        with tax_period <= cutoff_period.
        """
        G = nx.DiGraph()

        for inv in invoices:
            inv_period = getattr(inv, "tax_period", None) or inv.get("tax_period")
            if inv_period and inv_period <= cutoff_period:
                supplier = getattr(inv, "vendor_id", None) or inv.get("vendor_id")
                # Buyer can be buyer_id or buyer_gstin
                buyer = getattr(inv, "buyer_id", None) or inv.get("buyer_id") or "TP001"
                
                if supplier and buyer:
                    if not G.has_edge(supplier, buyer):
                        G.add_edge(supplier, buyer, weight=0, count=0)
                    G[supplier][buyer]["count"] += 1
                    val = float(getattr(inv, "invoice_value", 0.0) or inv.get("invoice_value", 0.0))
                    G[supplier][buyer]["weight"] += val

        return G

    def extract_vendor_graph_features(
        self,
        vendor_ids: List[str],
        G: nx.DiGraph,
        historical_vendor_risk: Dict[str, float]
    ) -> Dict[str, Dict[str, float]]:
        """
        Extracts graph features for all requested vendors from snapshot G.
        
        historical_vendor_risk: dictionary mapping vendor_id -> latest risk score
        computed at or before T_k. NEVER uses future target risk T_{k+1}.
        """
        node_features = {}

        # 1. Compute PageRank on snapshot (fallback to uniform if graph is empty or disconnected)
        try:
            pagerank_scores = nx.pagerank(G, alpha=0.85, max_iter=100) if len(G) > 0 else {}
        except Exception:
            pagerank_scores = {n: 1.0 / max(1, len(G)) for n in G.nodes()}

        # 2. Compute degree centrality
        try:
            deg_centrality = nx.degree_centrality(G) if len(G) > 0 else {}
        except Exception:
            deg_centrality = {}

        # 3. Compute clustering coefficient on undirected projection
        try:
            undirected_G = G.to_undirected()
            clustering_scores = nx.clustering(undirected_G)
        except Exception:
            clustering_scores = {}

        # 4. Find strongly connected components of size >= 3 (circular cycles)
        cycle_nodes = set()
        try:
            for scc in nx.strongly_connected_components(G):
                if len(scc) >= 3:
                    cycle_nodes.update(scc)
        except Exception:
            pass

        # 5. Extract per-vendor metrics
        for vid in vendor_ids:
            if vid in G:
                in_deg = float(G.in_degree(vid))
                out_deg = float(G.out_degree(vid))
                tot_deg = in_deg + out_deg
                centr = float(deg_centrality.get(vid, 0.0))
                pr = float(pagerank_scores.get(vid, 0.0))
                clust = float(clustering_scores.get(vid, 0.0))
                is_cycle = 1.0 if vid in cycle_nodes else 0.0

                # Reciprocal trade count (vendors who are both supplier and buyer of vid)
                succ = set(G.successors(vid))
                pred = set(G.predecessors(vid))
                reciprocal_count = float(len(succ.intersection(pred)))

                # 1-hop neighbors: all suppliers and buyers
                neighbors = succ.union(pred)
                
                # Neighbor risk metrics using STRICTLY historical risk at or before T_k
                # Default for unobserved/neutral neighbor is 0.0
                neighbor_risks = [
                    historical_vendor_risk.get(nbr, 0.0) 
                    for nbr in neighbors if nbr != vid
                ]
                
                high_risk_nbr_count = float(sum(1 for r in neighbor_risks if r >= 0.50))
                avg_nbr_risk = float(np.mean(neighbor_risks)) if neighbor_risks else 0.0

            else:
                # Isolated / unobserved in graph snapshot at T_k
                in_deg = 0.0
                out_deg = 0.0
                tot_deg = 0.0
                centr = 0.0
                pr = 0.0
                clust = 0.0
                is_cycle = 0.0
                reciprocal_count = 0.0
                high_risk_nbr_count = 0.0
                avg_nbr_risk = 0.0

            node_features[vid] = {
                "graph_in_degree": in_deg,
                "graph_out_degree": out_deg,
                "graph_total_degree": tot_deg,
                "graph_degree_centrality": centr,
                "graph_pagerank": pr,
                "graph_clustering_coefficient": clust,
                "reciprocal_trade_count": reciprocal_count,
                "cycle_participation": is_cycle,
                "high_risk_neighbor_count": high_risk_nbr_count,
                "neighbor_average_risk": avg_nbr_risk
            }

        return node_features


def attach_temporal_graph_features(
    feature_df: pd.DataFrame,
    invoices: List[Any],
    tax_periods: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Computes and joins temporal graph features onto feature_df for each period T_k.
    
    Guarantees:
    - At period T_k, snapshot graph uses ONLY invoices with tax_period <= T_k.
    - Neighbor risks use ONLY previous_period_risk available at T_k.
    - Zero future temporal leakage.
    """
    out_df = feature_df.copy()
    builder = TemporalGraphBuilder()

    # Pre-index invoices by period for fast snapshot building
    inv_by_period = defaultdict(list)
    for inv in invoices:
        p = getattr(inv, "tax_period", None) or inv.get("tax_period")
        if p:
            inv_by_period[p].append(inv)

    all_periods = sorted(list(set(out_df["prediction_period"].dropna())))
    graph_rows = []

    # Track historical vendor risk strictly as of each period T_k
    # (using previous_period_risk from feature_df which was computed at or before T_k)
    for period in all_periods:
        sub_df = out_df[out_df["prediction_period"] == period]
        period_vendors = sub_df["vendor_id"].tolist()

        # Historical risk dictionary at T_k
        hist_risk_map = dict(zip(sub_df["vendor_id"], sub_df["previous_period_risk"].fillna(0.0)))

        # Build snapshot graph G(T_k) using invoices up to period T_k
        cum_invoices = []
        for p in all_periods:
            if p <= period:
                cum_invoices.extend(inv_by_period.get(p, []))

        G = builder.build_snapshot_graph(cum_invoices, cutoff_period=period)
        features_map = builder.extract_vendor_graph_features(period_vendors, G, hist_risk_map)

        for _, row in sub_df.iterrows():
            vid = row["vendor_id"]
            feat_dict = features_map.get(vid, {})
            # Include unique index to merge back
            feat_dict["vendor_id"] = vid
            feat_dict["prediction_period"] = period
            graph_rows.append(feat_dict)

    graph_features_df = pd.DataFrame(graph_rows)
    # Merge onto original dataframe
    merged_df = pd.merge(
        out_df,
        graph_features_df,
        on=["vendor_id", "prediction_period"],
        how="left"
    )

    # Fill any missing graph metrics with 0.0
    for col in GRAPH_FEATURE_NAMES:
        if col in merged_df.columns:
            merged_df[col] = merged_df[col].fillna(0.0)

    return merged_df

"""
Unit tests for Temporal Graph Builder and graph feature extraction.
"""
import pytest
import networkx as nx
from backend.ml.graph_features import TemporalGraphBuilder, GRAPH_FEATURE_NAMES

def test_temporal_graph_snapshot_building():
    """Verify snapshot graph includes strictly invoices <= cutoff_period."""
    builder = TemporalGraphBuilder()
    invoices = [
        {"vendor_id": "V1", "buyer_id": "V2", "tax_period": "2024-05", "invoice_value": 1000},
        {"vendor_id": "V2", "buyer_id": "V3", "tax_period": "2024-05", "invoice_value": 2000},
        {"vendor_id": "V3", "buyer_id": "V1", "tax_period": "2024-07", "invoice_value": 3000} # Future
    ]
    
    # Snapshot at 2024-05 should only have 2 edges
    G_may = builder.build_snapshot_graph(invoices, cutoff_period="2024-05")
    assert G_may.number_of_nodes() == 3
    assert G_may.number_of_edges() == 2
    assert G_may.has_edge("V1", "V2")
    assert G_may.has_edge("V2", "V3")
    assert not G_may.has_edge("V3", "V1")

def test_graph_feature_extraction():
    """Verify calculation of degree, centrality, pagerank, and clustering."""
    builder = TemporalGraphBuilder()
    G = nx.DiGraph()
    G.add_edge("V1", "V2", weight=100)
    G.add_edge("V2", "V3", weight=200)
    G.add_edge("V3", "V1", weight=300)  # Triangle / Cycle
    
    hist_risk = {"V1": 0.1, "V2": 0.6, "V3": 0.2}
    features = builder.extract_vendor_graph_features(["V1", "V2", "V3", "V_ISOLATED"], G, hist_risk)
    
    assert "V1" in features
    f1 = features["V1"]
    for col in GRAPH_FEATURE_NAMES:
        assert col in f1, f"Missing graph feature: {col}"
        
    assert f1["graph_in_degree"] == 1.0
    assert f1["graph_out_degree"] == 1.0
    assert f1["graph_total_degree"] == 2.0
    assert f1["cycle_participation"] == 1.0  # V1 belongs to a 3-cycle
    assert f1["high_risk_neighbor_count"] == 1.0  # V2 has risk 0.60 >= 0.50
    
    # Isolated node
    f_iso = features["V_ISOLATED"]
    assert f_iso["graph_total_degree"] == 0.0
    assert f_iso["high_risk_neighbor_count"] == 0.0

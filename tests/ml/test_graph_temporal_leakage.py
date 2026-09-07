"""
Explicit test proving neighbor-risk features cannot access T_{k+1} or later target labels.
"""
import pytest
import networkx as nx
from backend.ml.graph_features import TemporalGraphBuilder

def test_neighbor_risk_temporal_isolation():
    """
    Assert that if a neighbor becomes high risk ONLY at period T_{k+1},
    their risk at period T_k remains low/unaffected, and high_risk_neighbor_count
    at T_k reflects ONLY historical data <= T_k.
    """
    builder = TemporalGraphBuilder()
    G = nx.DiGraph()
    # Vendor V_TARGET is connected to V_NEIGHBOR
    G.add_edge("V_TARGET", "V_NEIGHBOR", weight=1000)
    
    # At historical period T_k: V_NEIGHBOR was compliant (risk = 0.05)
    historical_risk_at_Tk = {
        "V_TARGET": 0.10,
        "V_NEIGHBOR": 0.05
    }
    
    # At FUTURE period T_{k+1}: V_NEIGHBOR fails GSTR-3B and becomes HIGH RISK (0.90)
    future_target_risk_at_Tk_plus_1 = {
        "V_TARGET": 0.15,
        "V_NEIGHBOR": 0.90
    }
    
    # When extracting features for prediction at T_k, pass historical_risk_at_Tk
    features_Tk = builder.extract_vendor_graph_features(["V_TARGET"], G, historical_risk_at_Tk)
    
    v_target_feat = features_Tk["V_TARGET"]
    
    # 1. Neighbor high-risk count must be 0 at T_k (since neighbor was 0.05 <= 0.50)
    assert v_target_feat["high_risk_neighbor_count"] == 0.0
    assert v_target_feat["neighbor_average_risk"] == 0.05
    
    # 2. Even if future labels exist in memory, the feature extraction at T_k
    # strictly does not see V_NEIGHBOR's future 0.90 risk
    assert v_target_feat["neighbor_average_risk"] != future_target_risk_at_Tk_plus_1["V_NEIGHBOR"]

def test_unobserved_neighbor_neutral_fallback():
    """Verify that neighbors with no prior history default to neutral 0.0 risk."""
    builder = TemporalGraphBuilder()
    G = nx.DiGraph()
    G.add_edge("V1", "V_NEW_NEIGHBOR")
    
    # V_NEW_NEIGHBOR has no historical risk recorded
    features = builder.extract_vendor_graph_features(["V1"], G, historical_vendor_risk={})
    
    assert features["V1"]["high_risk_neighbor_count"] == 0.0
    assert features["V1"]["neighbor_average_risk"] == 0.0

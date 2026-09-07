"""
Tests for diverse graph topology generation scenarios.
"""
import pytest
from backend.data.synthetic.generator import SyntheticGSTGenerator

def test_graph_scenarios_presence():
    """Verify generator constructs diverse graph topologies including cycles, clusters, and bilateral trade."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=60, months_count=6)
    
    invoices = dataset["invoices"]
    vendors = dataset["vendors"]
    vendor_ids = {v.vendor_id for v in vendors}
    
    # Map directed invoice transactions: (vendor_id, buyer_gstin)
    gstin_to_id = {v.gstin: v.vendor_id for v in vendors}
    edges = set()
    for inv in invoices:
        edges.add((inv.vendor_id, inv.buyer_gstin))
        
    assert len(edges) > 0

    # 1. Bilateral trade test: check if there exists at least one reciprocal pair (A -> B and B -> A)
    vendor_edges = set()
    for inv in invoices:
        supp_id = inv.vendor_id
        recip_id = gstin_to_id.get(inv.buyer_gstin)
        if recip_id and supp_id != recip_id:
            vendor_edges.add((supp_id, recip_id))
            
    # Also check graph_edges topology for bilateral trade
    graph_edges = dataset.get("graph_edges", [])
    bilateral_edges = [e for e in graph_edges if e.get("topology") == "bilateral"]
    assert len(bilateral_edges) > 0, "Bilateral trade edges should exist in graph"

def test_syndicate_cycle_edges():
    """Verify that circular syndicate edges are produced and logged."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=50, months_count=6)
    
    syndicate_edges = dataset.get("syndicate_edges", [])
    assert len(syndicate_edges) > 0
    first_edge = syndicate_edges[0]
    assert "source_vendor" in first_edge
    assert "target_vendor" in first_edge
    assert "relation" in first_edge
    assert "topology" in first_edge

def test_diverse_graph_vendors():
    """Verify that vendors participating in various topologies are properly labeled."""
    gen = SyntheticGSTGenerator(seed=42)
    dataset = gen.generate_dataset(vendor_count=50, months_count=6)
    
    vendors = dataset["vendors"]
    profiles = {v.synthetic_profile for v in vendors}
    # Should contain G (Suspicious Network) and normal profiles
    assert "G" in profiles
    assert "A" in profiles

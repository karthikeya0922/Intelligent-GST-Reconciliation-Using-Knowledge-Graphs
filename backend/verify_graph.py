"""
End-to-end check for the Neo4j knowledge graph path.

Run this once Neo4j is up (`docker compose up -d`) to prove the graph engine
works and agrees with the MongoDB view:

    python verify_graph.py

It syncs Mongo -> Neo4j, runs graph-traversal reconciliation, and cross-checks
the structural findings against what MongoDB's stored match_status labels say.
A mismatch between the two is reported rather than hidden.
"""

import os
import sys

from pymongo import MongoClient

from graph_sync import get_sync
from reconcile import ReconciliationEngine


def main():
    mongo = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017"),
                        serverSelectionTimeoutMS=4000)
    db = mongo["gst_reconcile_ai"]

    print("1. Checking Neo4j connectivity...")
    sync = get_sync()
    status = sync.status()
    if not status.get("connected"):
        print(f"   FAIL: {status.get('reason')}")
        print("   Start it with:  docker compose up -d neo4j")
        return 1
    print(f"   OK: {status['uri']}")

    print("2. Syncing MongoDB -> Neo4j...")
    vendors = list(db["vendors"].find({}, {"_id": 0}))
    invoices = list(db["invoices"].find({}, {"_id": 0}))
    taxpayer = db["taxpayer"].find_one({}, {"_id": 0})
    returns = list(db["returns"].find({"type": "GSTR-3B"}, {"_id": 0}))
    summary = sync.sync(vendors, invoices, taxpayer=taxpayer, returns=returns)
    sync.compute_centrality()
    print(f"   OK: {summary['vendors']} vendors, {summary['invoices']} invoices, "
          f"{summary['taxpayer']} taxpayer, {summary['gstr3bFilings']} GSTR-3B filings, "
          f"{summary['matched']} fully matched")

    after = sync.status()
    print(f"   Graph now holds: {after['nodes']} / {after['relationships']} relationships")

    print("3. Running graph-traversal reconciliation...")
    engine = ReconciliationEngine(driver=sync.driver)
    result = engine.full_reconciliation()
    print(f"   OK: {result['total_mismatches']} mismatches, "
          f"Rs.{result['total_tax_at_risk']:,.0f} at risk")
    for issue, count in result["by_type"].items():
        print(f"     - {issue}: {count}")

    print("4. Cross-checking structural findings against MongoDB labels...")
    graph_missing = {
        m["invoice_id"] for m in result["mismatches"]
        if m["issue_type"] == "Missing in GSTR-1"
    }
    mongo_missing = {
        d["id"] for d in db["invoices"].find(
            {"gstr1Reported": False, "gstr2bReported": True}, {"id": 1}
        )
    }
    if graph_missing == mongo_missing:
        print(f"   OK: both agree on {len(graph_missing)} GSTR-1 gaps")
    else:
        print(f"   MISMATCH")
        print(f"     graph only: {sorted(graph_missing - mongo_missing)}")
        print(f"     mongo only: {sorted(mongo_missing - graph_missing)}")
        return 1

    print("5. Cross-checking the multi-hop tax-payment chain...")
    graph_unpaid = {
        m["invoice_id"] for m in result["mismatches"]
        if m["issue_type"] == "Supplier GSTR-3B Not Filed"
    }
    # Same question asked of MongoDB: invoices in GSTR-1 whose supplier did not
    # file a GSTR-3B for that period.
    unfiled = {
        (r["gstin"], r["period"])
        for r in db["returns"].find({"type": "GSTR-3B", "filed": False}, {"gstin": 1, "period": 1})
    }
    mongo_unpaid = {
        d["id"] for d in db["invoices"].find({"gstr1Reported": True}, {"id": 1, "gstin": 1, "period": 1})
        if (d.get("gstin"), d.get("period")) in unfiled
    }
    if graph_unpaid == mongo_unpaid:
        print(f"   OK: both agree on {len(graph_unpaid)} invoice(s) with unremitted tax")
    else:
        print("   MISMATCH")
        print(f"     graph only: {sorted(graph_unpaid - mongo_unpaid)}")
        print(f"     mongo only: {sorted(mongo_unpaid - graph_unpaid)}")
        return 1

    print("6. Fetching an evidence path...")
    if graph_missing:
        sample = sorted(graph_missing)[0]
        evidence = engine.get_evidence_path(sample)
        print(f"   {evidence['graph_path']}")
        print(f"   missing_gstr1={evidence['missing_gstr1']} tax={evidence['tax']}")

    sync.close()
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

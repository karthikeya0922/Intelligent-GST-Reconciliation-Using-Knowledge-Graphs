"""
Seed trained ML vendors, realistic GST invoices, filing returns, and trade edges into MongoDB and Neo4j.
"""
import os
import sys
import json
from pymongo import MongoClient

# Add root directory to sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

from backend.ml.data_store import get_data_store
from backend.graph_sync import get_sync

def populate_trained_ecosystem():
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
    client = MongoClient(mongo_uri)
    db = client["gst_reconcile_ai"]

    vendors_col = db["vendors"]
    invoices_col = db["invoices"]
    taxpayer_col = db["taxpayer"]
    returns_col = db["returns"]

    # 1. Load trained vendors from ML data store
    ds = get_data_store()
    period_df = ds.get_period_dataframe("2026-02")
    if period_df is None or period_df.empty:
        print("[WARN] 2026-02 period dataframe empty, using latest available")
        period_df = ds.features_df

    # Select top 25 diverse trained vendors
    top_vendors_df = period_df.head(25)

    vendors = []
    vendor_gstin_map = {}
    vendor_name_map = {}

    for _, r in top_vendors_df.iterrows():
        vid = str(r["vendor_id"]).strip()
        vname = str(r["vendor_name"]).strip()
        # Clean display name if redundant (V0001) suffix
        clean_name = vname.replace(f"({vid})", "").strip() if f"({vid})" in vname else vname
        gstin = str(r["gstin"]).strip()
        state = str(r.get("state", "Maharashtra")).strip()
        raw_score = float(r.get("risk_score", 15.0))
        risk_score_norm = round(raw_score / 100.0, 3)
        risk_band = str(r.get("risk_band", "LOW")).upper()

        if risk_band == "HIGH" or raw_score >= 70.0:
            status = "High Risk"
        elif risk_band == "MEDIUM" or raw_score >= 35.0:
            status = "Review"
        else:
            status = "Compliant"

        v_dict = {
            "id": vid,
            "name": clean_name,
            "fullName": vname,
            "gstin": gstin,
            "state": state,
            "riskScore": risk_score_norm,
            "risk_score": raw_score,
            "status": status,
            "riskBand": risk_band,
            "itcExposure": round(float(r.get("itc_exposure", 0.0)), 2),
            "priority": str(r.get("priority", "NORMAL")),
            "mismatchRate": round(float(r.get("mismatch_rate", 0.0)) * 100, 1),
            "totalTransactions": int(r.get("invoice_count", 150) or 150),
            "missedFilings": int(r.get("missing_gstr1_count", 0) or 0),
            "avgDaysLate": int(r.get("average_filing_delay", 1) or 1),
        }
        vendors.append(v_dict)
        vendor_gstin_map[vid] = gstin
        vendor_name_map[vid] = clean_name

    # 2. Load and build invoices
    sample_path = os.path.join(_root_dir, "data", "sample", "sample_hybrid_dataset.json")
    sample_invoices = []
    trade_edges = []
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            sample_data = json.load(f)
            sample_invoices = sample_data.get("sample_invoices", [])
            trade_edges = sample_data.get("syndicate_network_edges", [])

    invoices = []
    inv_counter = 1

    # Map existing sample invoices
    for sinv in sample_invoices:
        vid = sinv.get("vendor_id")
        if vid in vendor_gstin_map:
            gstin = vendor_gstin_map[vid]
            vname = vendor_name_map[vid]
            taxable = round(float(sinv.get("taxable_value", 450000.0)), 2)
            tot_tax = round(float(sinv.get("total_tax", 81000.0)), 2)
            half_tax = round(tot_tax / 2, 2)
            period = sinv.get("tax_period", "2025-08")

            # Determine match status
            is_anomaly = bool(sinv.get("anomaly_type"))
            match_status = "Missing in GSTR-1" if is_anomaly else "Matched"
            risk_level = "High" if is_anomaly else "Low"

            inv_dict = {
                "id": f"INV-2025-{inv_counter:03d}",
                "vendorId": vid,
                "vendorName": vname,
                "gstin": gstin,
                "date": sinv.get("invoice_date", "2025-08-15"),
                "taxableAmount": taxable,
                "cgst": half_tax,
                "sgst": half_tax,
                "igst": 0.0,
                "totalTax": tot_tax,
                "total": round(taxable + tot_tax, 2),
                "hsn": str(sinv.get("hsn_code", "7208")),
                "period": period,
                "gstr1Reported": not is_anomaly,
                "gstr2bReported": True,
                "eInvoice": True,
                "eWayBill": not is_anomaly,
                "matchStatus": match_status,
                "riskLevel": risk_level,
                "inPurchaseRegister": True
            }
            invoices.append(inv_dict)
            inv_counter += 1

    # Ensure every vendor in our 25 has at least 1-2 realistic invoices
    existing_vendor_ids = set(i["vendorId"] for i in invoices)
    for v in vendors:
        if v["id"] not in existing_vendor_ids:
            is_flagged = v["riskBand"] == "HIGH" or v["missedFilings"] > 0
            taxable = round(float(v["itcExposure"] * 5) if v["itcExposure"] > 0 else 380000.0, 2)
            tot_tax = round(taxable * 0.18, 2)
            half_tax = round(tot_tax / 2, 2)

            match_status = "Missing in GSTR-1" if is_flagged else "Matched"
            risk_level = "High" if is_flagged else "Low"

            inv_dict = {
                "id": f"INV-2025-{inv_counter:03d}",
                "vendorId": v["id"],
                "vendorName": v["name"],
                "gstin": v["gstin"],
                "date": "2025-09-12",
                "taxableAmount": taxable,
                "cgst": half_tax,
                "sgst": half_tax,
                "igst": 0.0,
                "totalTax": tot_tax,
                "total": round(taxable + tot_tax, 2),
                "hsn": "8471" if inv_counter % 2 == 0 else "7210",
                "period": "2025-09",
                "gstr1Reported": not is_flagged,
                "gstr2bReported": True,
                "eInvoice": True,
                "eWayBill": True,
                "matchStatus": match_status,
                "riskLevel": risk_level,
                "inPurchaseRegister": True
            }
            invoices.append(inv_dict)
            inv_counter += 1

    # 3. Taxpayer entity
    taxpayer = {
        "id": "TP001",
        "name": "Quadric Manufacturing Ltd",
        "legalName": "Quadric Manufacturing Private Limited",
        "gstin": "29AAQCQ1234M1Z8",
        "state": "Karnataka",
        "registrationType": "Regular Taxpayer",
        "filingFrequency": "Monthly"
    }

    # 4. GSTR-3B filings for each vendor
    returns = []
    for v in vendors:
        is_filed = v["missedFilings"] == 0
        returns.append({
            "gstin": v["gstin"],
            "period": "2025-08",
            "filed": is_filed,
            "filedDate": "2025-08-20" if is_filed else None,
            "status": "FILED" if is_filed else "PENDING",
            "vendorName": v["name"]
        })

    # 5. Save to MongoDB
    vendors_col.delete_many({})
    vendors_col.insert_many(vendors)
    print(f"[OK] Saved {len(vendors)} trained vendors to MongoDB")

    invoices_col.delete_many({})
    invoices_col.insert_many(invoices)
    print(f"[OK] Saved {len(invoices)} invoices to MongoDB")

    taxpayer_col.delete_many({})
    taxpayer_col.insert_one(taxpayer)

    returns_col.delete_many({})
    returns_col.insert_many(returns)

    # 6. Clean ObjectId before syncing to Neo4j
    clean_vendors = [{k: v for k, v in vend.items() if k != "_id"} for vend in vendors]
    clean_invoices = [{k: v for k, v in inv.items() if k != "_id"} for inv in invoices]
    clean_returns = [{k: v for k, v in ret.items() if k != "_id"} for ret in returns]
    clean_taxpayer = {k: v for k, v in taxpayer.items() if k != "_id"}

    # Sync to Neo4j
    sync = get_sync()
    if sync.status().get("connected"):
        print("[*] Projecting trained ecosystem into Neo4j Knowledge Graph...")
        summary = sync.sync(
            vendors=clean_vendors,
            invoices=clean_invoices,
            wipe=True,
            taxpayer=clean_taxpayer,
            returns=clean_returns,
            trade_edges=trade_edges
        )
        sync.compute_centrality()
        print(f"[OK] Neo4j Knowledge Graph Synced successfully: {summary}")
    else:
        print("[WARN] Neo4j not connected; MongoDB updated.")

if __name__ == "__main__":
    populate_trained_ecosystem()

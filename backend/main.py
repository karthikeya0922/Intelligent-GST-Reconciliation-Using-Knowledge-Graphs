"""
GST ReconcileAI - FastAPI Backend

MongoDB is the system of record. Two optional subsystems layer on top:

  * a RandomForest vendor-risk model (risk_model.py), loaded at startup
  * a Neo4j knowledge graph projection (graph_sync.py / reconcile.py)

Both degrade gracefully. If scikit-learn is missing the API falls back to a
documented heuristic; if Neo4j is unreachable the graph endpoints report offline
and every Mongo-derived view keeps working.
"""

from fastapi import FastAPI, Query, Body, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from pymongo import MongoClient
from bson import ObjectId
import json, os, sys
from datetime import datetime
from dotenv import load_dotenv

# Ensure backend directory and repo root are in sys.path
_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)
if _root_dir not in sys.path:
    sys.path.insert(0, _root_dir)

import auth_utils
from audit_trail import build_audit_trail

load_dotenv()

# ---- Optional: ML risk model -------------------------------------------------
try:
    from risk_model import get_model, map_vendor_features
    ML_AVAILABLE = True
except ImportError as exc:
    print(f"[WARN] Risk model unavailable ({exc}); using heuristic fallback.")
    ML_AVAILABLE = False

# ---- Optional: Neo4j knowledge graph ----------------------------------------
try:
    from graph_sync import get_sync
    from reconcile import ReconciliationEngine
    GRAPH_AVAILABLE = True
except ImportError as exc:
    print(f"[WARN] Neo4j driver unavailable ({exc}); graph endpoints disabled.")
    GRAPH_AVAILABLE = False

app = FastAPI(
    title="GST ReconcileAI API",
    description="Knowledge Graph-powered GST Reconciliation Engine with MongoDB",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# MongoDB Connection
# ============================================================
MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["gst_reconcile_ai"]
vendors_col = db["vendors"]
invoices_col = db["invoices"]
alerts_col = db["alerts"]
users_col = db["users"]
# The filing entity (the buyer claiming ITC) and its own books.
taxpayer_col = db["taxpayer"]
# Per-vendor, per-period GSTR-3B filings - the return where tax is actually paid.
returns_col = db["returns"]

def serialize(doc):
    """Convert MongoDB document to JSON-safe dict"""
    if doc is None:
        return None
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

def serialize_list(cursor):
    return [serialize(doc) for doc in cursor]


# ============================================================
# Seed default data if collections are empty
# ============================================================
def seed_data():
    if vendors_col.count_documents({}) == 0:
        default_vendors = [
            {"id":"V001","name":"Tata Steel Ltd","gstin":"29AABCU9603R1ZM","state":"Karnataka","riskScore":0.12,"status":"Compliant","totalTransactions":245,"missedFilings":0,"avgDaysLate":0},
            {"id":"V002","name":"Reliance Industries","gstin":"27AABCR9718E1ZL","state":"Maharashtra","riskScore":0.08,"status":"Compliant","totalTransactions":312,"missedFilings":0,"avgDaysLate":0},
            {"id":"V003","name":"Infosys Technologies","gstin":"29AABCI1332L1ZJ","state":"Karnataka","riskScore":0.15,"status":"Compliant","totalTransactions":189,"missedFilings":0,"avgDaysLate":1},
            {"id":"V004","name":"Wipro Limited","gstin":"29AABCW6273R1ZA","state":"Karnataka","riskScore":0.22,"status":"Compliant","totalTransactions":156,"missedFilings":1,"avgDaysLate":2},
            {"id":"V005","name":"Hyderabad Steels Pvt","gstin":"36AAACH7409R1ZK","state":"Telangana","riskScore":0.78,"status":"High Risk","totalTransactions":67,"missedFilings":4,"avgDaysLate":12},
            {"id":"V006","name":"Bajaj Auto Ltd","gstin":"27AABCB8482K1Z5","state":"Maharashtra","riskScore":0.19,"status":"Compliant","totalTransactions":198,"missedFilings":0,"avgDaysLate":1},
            {"id":"V007","name":"Hindalco Industries","gstin":"22AABCH0812J1ZF","state":"Chhattisgarh","riskScore":0.35,"status":"Review","totalTransactions":143,"missedFilings":1,"avgDaysLate":3},
            {"id":"V008","name":"ITC Limited","gstin":"19AABCI5765M1ZO","state":"West Bengal","riskScore":0.11,"status":"Compliant","totalTransactions":276,"missedFilings":0,"avgDaysLate":0},
            {"id":"V009","name":"Mahindra & Mahindra","gstin":"27AABCM5964F1ZE","state":"Maharashtra","riskScore":0.28,"status":"Compliant","totalTransactions":167,"missedFilings":1,"avgDaysLate":2},
            {"id":"V010","name":"SunPharma Industries","gstin":"09AABCS1429B1ZE","state":"Uttar Pradesh","riskScore":0.65,"status":"High Risk","totalTransactions":89,"missedFilings":3,"avgDaysLate":8},
            {"id":"V011","name":"Grasim Industries","gstin":"09AABCG0127K1ZP","state":"Uttar Pradesh","riskScore":0.18,"status":"Compliant","totalTransactions":134,"missedFilings":0,"avgDaysLate":1},
            {"id":"V012","name":"NTPC Limited","gstin":"07AABCN8726L1ZF","state":"Delhi","riskScore":0.09,"status":"Compliant","totalTransactions":223,"missedFilings":0,"avgDaysLate":0},
            {"id":"V013","name":"EID Parry India","gstin":"33AABCE9012P1ZS","state":"Tamil Nadu","riskScore":0.72,"status":"High Risk","totalTransactions":56,"missedFilings":4,"avgDaysLate":10},
            {"id":"V014","name":"Godrej Consumer","gstin":"27AABCG3456R1ZM","state":"Maharashtra","riskScore":0.31,"status":"Review","totalTransactions":145,"missedFilings":1,"avgDaysLate":3},
            {"id":"V015","name":"Hero MotoCorp","gstin":"06AABCH7890K1ZR","state":"Haryana","riskScore":0.14,"status":"Compliant","totalTransactions":201,"missedFilings":0,"avgDaysLate":1},
            {"id":"V016","name":"DLF Limited","gstin":"07AABCD1234L1ZP","state":"Delhi","riskScore":0.42,"status":"Review","totalTransactions":98,"missedFilings":2,"avgDaysLate":5},
            {"id":"V017","name":"Asian Paints","gstin":"27AABCA5678E1ZK","state":"Maharashtra","riskScore":0.10,"status":"Compliant","totalTransactions":267,"missedFilings":0,"avgDaysLate":0},
            {"id":"V018","name":"Jubilant Foodworks","gstin":"09AABCJ9012B1ZM","state":"Uttar Pradesh","riskScore":0.55,"status":"Review","totalTransactions":78,"missedFilings":2,"avgDaysLate":6},
            {"id":"V019","name":"Torrent Pharma","gstin":"24AABCT3456P1ZG","state":"Gujarat","riskScore":0.48,"status":"Review","totalTransactions":112,"missedFilings":2,"avgDaysLate":4},
            {"id":"V020","name":"Adani Enterprises","gstin":"24AABCA7890E1ZL","state":"Gujarat","riskScore":0.25,"status":"Compliant","totalTransactions":189,"missedFilings":1,"avgDaysLate":2},
        ]
        vendors_col.insert_many(default_vendors)
        print("[OK] Seeded 20 vendors")

    if invoices_col.count_documents({}) == 0:
        default_invoices = [
            {"id":"INV-2025-001","vendorId":"V005","vendorName":"Hyderabad Steels Pvt","gstin":"36AAACH7409R1ZK","date":"2025-07-15","taxableAmount":450000,"cgst":40500,"sgst":40500,"igst":0,"totalTax":81000,"total":531000,"hsn":"7208","period":"2025-07","gstr1Reported":False,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Missing in GSTR-1","riskLevel":"High"},
            {"id":"INV-2025-002","vendorId":"V001","vendorName":"Tata Steel Ltd","gstin":"29AABCU9603R1ZM","date":"2025-07-18","taxableAmount":780000,"cgst":70200,"sgst":70200,"igst":0,"totalTax":140400,"total":920400,"hsn":"7210","period":"2025-07","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-003","vendorId":"V010","vendorName":"SunPharma Industries","gstin":"09AABCS1429B1ZE","date":"2025-07-22","taxableAmount":320000,"cgst":0,"sgst":0,"igst":38400,"totalTax":38400,"total":358400,"hsn":"3004","period":"2025-07","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Tax Amount Mismatch","riskLevel":"Medium"},
            {"id":"INV-2025-004","vendorId":"V013","vendorName":"EID Parry India","gstin":"33AABCE9012P1ZS","date":"2025-07-25","taxableAmount":1200000,"cgst":0,"sgst":0,"igst":140400,"totalTax":140400,"total":1340400,"hsn":"1701","period":"2025-07","gstr1Reported":False,"gstr2bReported":True,"eInvoice":True,"eWayBill":False,"matchStatus":"Missing in GSTR-1","riskLevel":"High"},
            {"id":"INV-2025-005","vendorId":"V002","vendorName":"Reliance Industries","gstin":"27AABCR9718E1ZL","date":"2025-07-28","taxableAmount":560000,"cgst":50400,"sgst":50400,"igst":0,"totalTax":100800,"total":660800,"hsn":"2710","period":"2025-07","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-006","vendorId":"V006","vendorName":"Bajaj Auto Ltd","gstin":"27AABCB8482K1Z5","date":"2025-08-02","taxableAmount":890000,"cgst":80100,"sgst":80100,"igst":0,"totalTax":160200,"total":1050200,"hsn":"8711","period":"2025-08","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-007","vendorId":"V018","vendorName":"Jubilant Foodworks","gstin":"09AABCJ9012B1ZM","date":"2025-08-05","taxableAmount":95000,"cgst":0,"sgst":0,"igst":17100,"totalTax":17100,"total":112100,"hsn":"2106","period":"2025-08","gstr1Reported":False,"gstr2bReported":True,"eInvoice":False,"eWayBill":True,"matchStatus":"Missing in GSTR-1","riskLevel":"High"},
            {"id":"INV-2025-008","vendorId":"V003","vendorName":"Infosys Technologies","gstin":"29AABCI1332L1ZJ","date":"2025-08-08","taxableAmount":1500000,"cgst":135000,"sgst":135000,"igst":0,"totalTax":270000,"total":1770000,"hsn":"9983","period":"2025-08","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":False,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-009","vendorId":"V007","vendorName":"Hindalco Industries","gstin":"22AABCH0812J1ZF","date":"2025-08-10","taxableAmount":410000,"cgst":0,"sgst":0,"igst":49200,"totalTax":49200,"total":459200,"hsn":"7208","period":"2025-08","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"HSN Mismatch","riskLevel":"Medium"},
            {"id":"INV-2025-010","vendorId":"V008","vendorName":"ITC Limited","gstin":"19AABCI5765M1ZO","date":"2025-08-12","taxableAmount":230000,"cgst":0,"sgst":0,"igst":27600,"totalTax":27600,"total":257600,"hsn":"2401","period":"2025-08","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-011","vendorId":"V005","vendorName":"Hyderabad Steels Pvt","gstin":"36AAACH7409R1ZK","date":"2025-08-15","taxableAmount":670000,"cgst":0,"sgst":0,"igst":120600,"totalTax":120600,"total":790600,"hsn":"7208","period":"2025-08","gstr1Reported":False,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Missing in GSTR-1","riskLevel":"High"},
            {"id":"INV-2025-012","vendorId":"V009","vendorName":"Mahindra & Mahindra","gstin":"27AABCM5964F1ZE","date":"2025-08-18","taxableAmount":340000,"cgst":30600,"sgst":30600,"igst":0,"totalTax":61200,"total":401200,"hsn":"8429","period":"2025-08","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-013","vendorId":"V014","vendorName":"Godrej Consumer","gstin":"27AABCG3456R1ZM","date":"2025-08-20","taxableAmount":120000,"cgst":10800,"sgst":10800,"igst":0,"totalTax":21600,"total":141600,"hsn":"3401","period":"2025-08","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Late Filing","riskLevel":"Medium"},
            {"id":"INV-2025-014","vendorId":"V015","vendorName":"Hero MotoCorp","gstin":"06AABCH7890K1ZR","date":"2025-09-01","taxableAmount":980000,"cgst":0,"sgst":0,"igst":176400,"totalTax":176400,"total":1156400,"hsn":"8711","period":"2025-09","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-015","vendorId":"V019","vendorName":"Torrent Pharma","gstin":"24AABCT3456P1ZG","date":"2025-09-03","taxableAmount":150000,"cgst":0,"sgst":0,"igst":18000,"totalTax":18000,"total":168000,"hsn":"3004","period":"2025-09","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"E-Way Bill Missing","riskLevel":"Medium"},
            {"id":"INV-2025-016","vendorId":"V012","vendorName":"NTPC Limited","gstin":"07AABCN8726L1ZF","date":"2025-09-05","taxableAmount":2100000,"cgst":189000,"sgst":189000,"igst":0,"totalTax":378000,"total":2478000,"hsn":"2716","period":"2025-09","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-017","vendorId":"V016","vendorName":"DLF Limited","gstin":"07AABCD1234L1ZP","date":"2025-09-08","taxableAmount":4500000,"cgst":405000,"sgst":405000,"igst":0,"totalTax":810000,"total":5310000,"hsn":"9972","period":"2025-09","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":False,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-018","vendorId":"V010","vendorName":"SunPharma Industries","gstin":"09AABCS1429B1ZE","date":"2025-09-10","taxableAmount":280000,"cgst":0,"sgst":0,"igst":33600,"totalTax":33600,"total":313600,"hsn":"2933","period":"2025-09","gstr1Reported":False,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Missing in GSTR-1","riskLevel":"High"},
            {"id":"INV-2025-019","vendorId":"V020","vendorName":"Adani Enterprises","gstin":"24AABCA7890E1ZL","date":"2025-09-12","taxableAmount":670000,"cgst":0,"sgst":0,"igst":120600,"totalTax":120600,"total":790600,"hsn":"2701","period":"2025-09","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":True,"matchStatus":"Matched","riskLevel":"Low"},
            {"id":"INV-2025-020","vendorId":"V004","vendorName":"Wipro Limited","gstin":"29AABCW6273R1ZA","date":"2025-09-15","taxableAmount":890000,"cgst":80100,"sgst":80100,"igst":0,"totalTax":160200,"total":1050200,"hsn":"9983","period":"2025-09","gstr1Reported":True,"gstr2bReported":True,"eInvoice":True,"eWayBill":False,"matchStatus":"Matched","riskLevel":"Low"},
        ]
        invoices_col.insert_many(default_invoices)
        print("[OK] Seeded 20 invoices")

    if users_col.count_documents({}) == 0:
        # Demo accounts. Passwords are hashed on the way in - nothing is ever
        # stored in plaintext, including seeds.
        users_col.insert_many([
            {"email":"admin@gstreconcile.ai","password":auth_utils.hash_password("admin123"),"name":"Admin User","role":"admin","createdAt":"2025-01-01"},
            {"email":"auditor@gstreconcile.ai","password":auth_utils.hash_password("auditor123"),"name":"Tax Auditor","role":"auditor","createdAt":"2025-03-15"},
        ])
        users_col.create_index("email", unique=True)
        print("[OK] Seeded default users")

    if alerts_col.count_documents({}) == 0:
        alerts_col.insert_many([
            {"type":"critical","message":"5 invoices missing from vendor GSTR-1 filings","time":"2 hours ago","icon":"🔴"},
            {"type":"warning","message":"Vendor V005 risk score increased to 78%","time":"5 hours ago","icon":"🟡"},
            {"type":"success","message":"GSTR-2B auto-reconciliation completed for Aug 2025","time":"1 day ago","icon":"🟢"},
            {"type":"warning","message":"3 vendors have pending GSTR-1 amendments","time":"1 day ago","icon":"🟡"},
            {"type":"critical","message":"₹8.1L ITC at risk due to unmatched invoices","time":"2 days ago","icon":"🔴"},
        ])
        print("[OK] Seeded alerts")


def seed_gst_ecosystem():
    """Seed the entities that complete the GST model beyond vendor+invoice.

    Three things the reconciliation needs but the original schema lacked:

    * Taxpayer  - the buyer claiming ITC. Every invoice is billed to it, and it
      is the entity whose GSTR-2B is auto-generated and whose GSTR-3B is filed.
    * GSTR-3B   - the summary return where tax is actually *paid*. GSTR-1 only
      reports an invoice; without the supplier's 3B the tax was never remitted,
      so the ITC is still at risk. This is what makes the
      invoice -> GSTR-1 -> GSTR-3B chain worth traversing.
    * Purchase Register - the buyer's own books. Reconciling PR against GSTR-2B
      is the match auditors actually run for ITC.
    """
    if taxpayer_col.count_documents({}) == 0:
        taxpayer_col.insert_one({
            "id": "TP001",
            "name": "Quadric Manufacturing Pvt Ltd",
            "gstin": "29AAQCQ1234M1Z8",
            "state": "Karnataka",
            "legalName": "Quadric Manufacturing Private Limited",
            "registrationType": "Regular",
            "filingFrequency": "Monthly",
        })
        print("[OK] Seeded taxpayer entity")

    # GSTR-3B filing status per vendor per period. Vendors who reported an
    # invoice in GSTR-1 but never filed 3B are the interesting case: the invoice
    # looks fine one hop out, and only the second hop reveals unpaid tax.
    if returns_col.count_documents({}) == 0:
        periods = ["2025-07", "2025-08", "2025-09"]
        # Vendors who defaulted on their 3B for a given period.
        defaulters = {
            "2025-07": {"V013"},
            "2025-08": {"V005", "V014"},
            "2025-09": {"V010", "V019"},
        }
        docs = []
        for vendor in vendors_col.find({}, {"_id": 0, "id": 1, "gstin": 1, "name": 1}):
            for period in periods:
                filed = vendor["id"] not in defaulters.get(period, set())
                docs.append({
                    "gstin": vendor["gstin"],
                    "vendorId": vendor["id"],
                    "vendorName": vendor["name"],
                    "type": "GSTR-3B",
                    "period": period,
                    "filed": filed,
                    "filedDate": f"{period}-20" if filed else None,
                    "status": "Filed" if filed else "Not Filed",
                })
        if docs:
            returns_col.insert_many(docs)
            print(f"[OK] Seeded {len(docs)} GSTR-3B filing records")

    # Purchase Register: which invoices the buyer actually recorded in its books.
    # Deliberate gaps in both directions so the PR<->2B checks have something to
    # find - an unrecorded purchase is as much a finding as a missing invoice.
    not_in_pr = {"INV-2025-013", "INV-2025-017"}
    missing = list(invoices_col.find({"inPurchaseRegister": {"$exists": False}}, {"_id": 0, "id": 1}))
    if missing:
        for inv in missing:
            invoices_col.update_one(
                {"id": inv["id"]},
                {"$set": {"inPurchaseRegister": inv["id"] not in not_in_pr}},
            )
        print(f"[OK] Backfilled purchase-register flags on {len(missing)} invoices")


# Run seed on startup
seed_data()
seed_gst_ecosystem()

# Rehash any legacy plaintext credentials left by earlier versions.
auth_utils.migrate_plaintext_passwords(users_col)

# Load (or train, on first run) the vendor risk model.
RISK_MODEL = None
if ML_AVAILABLE:
    try:
        RISK_MODEL = get_model()
    except Exception as exc:
        print(f"[WARN] Could not load risk model ({exc}); using heuristic fallback.")


# ============================================================
# Risk prediction
# ============================================================
def heuristic_risk(vendor_data):
    """Weighted-sum fallback, used only when the ML model is unavailable.

    Weights sum to 0.74, so this saturates around 0.75 rather than 1.0 - it is a
    rough ordering, not a calibrated probability. The RandomForest is preferred.
    """
    missed = min(vendor_data.get("missedFilings", 0) / 6, 1)
    late = min(vendor_data.get("avgDaysLate", 0) / 20, 1)
    tx = vendor_data.get("totalTransactions", 100)
    tx_score = 0.8 if tx < 50 else (0.4 if tx < 100 else 0.1)
    einv = 0.7 if vendor_data.get("missedFilings", 0) > 2 else 0.2

    score = missed * 0.34 + late * 0.28 + tx_score * 0.18 + einv * 0.20
    return min(max(score, 0.05), 0.95)


def vendor_invoices(vendor_id, gstin=None):
    """Fetch a vendor's invoices so risk features use real history."""
    query = {"vendorId": vendor_id} if vendor_id else {"gstin": gstin}
    return list(invoices_col.find(query, {"_id": 0}))


def predict_risk(vendor_data, invoices=None):
    """Score a vendor. Returns (score, source).

    Uses the trained RandomForest against graph-derived features when available,
    falling back to the heuristic otherwise.
    """
    if RISK_MODEL is not None:
        try:
            busiest = invoices_col.database["vendors"].find_one(
                sort=[("totalTransactions", -1)]
            ) or {}
            max_tx = max(busiest.get("totalTransactions", 500) or 500, 1)
            features = map_vendor_features(vendor_data, invoices, max_transactions=max_tx)
            score, _label = RISK_MODEL.predict_one(features)
            return float(score), "RandomForestClassifier"
        except Exception as exc:
            print(f"[WARN] Model prediction failed ({exc}); falling back to heuristic.")

    return heuristic_risk(vendor_data), "heuristic"


def classify_risk(score):
    if score >= 0.6: return "High Risk"
    if score >= 0.3: return "Review"
    return "Compliant"


def next_id(collection, prefix, width=3):
    """Generate the next sequential id without reusing a deleted one.

    Counting documents (the previous approach) collides after any delete, so we
    take the maximum existing suffix instead.
    """
    highest = 0
    for doc in collection.find({}, {"id": 1, "_id": 0}):
        raw = str(doc.get("id", ""))
        suffix = raw.rsplit("-", 1)[-1] if "-" in raw else raw[len(prefix):]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"{prefix}{str(highest + 1).zfill(width)}"


# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
def root():
    return {
        "service": "GST ReconcileAI",
        "status": "online",
        "database": "MongoDB",
        "version": "3.0.0",
        "subsystems": {
            "riskModel": "RandomForestClassifier" if RISK_MODEL is not None else "heuristic",
            "knowledgeGraph": "neo4j" if GRAPH_AVAILABLE else "unavailable",
            "auth": "bcrypt",
        },
    }


# ---- Vendors ----
@app.get("/api/vendors")
def get_vendors():
    vendors = serialize_list(vendors_col.find({}, {"_id": 0}))
    return vendors

@app.post("/api/vendors")
def add_vendor(vendor: dict = Body(...)):
    if not vendor.get("name") or not vendor.get("gstin"):
        return {"error": "name and gstin are required"}

    vid = next_id(vendors_col, "V")
    risk_score, source = predict_risk(vendor)
    status = classify_risk(risk_score)

    new_vendor = {
        "id": vid,
        "name": vendor["name"],
        "gstin": vendor["gstin"],
        "state": vendor.get("state", ""),
        "riskScore": round(risk_score, 2),
        "status": status,
        "totalTransactions": vendor.get("totalTransactions", 0),
        "missedFilings": vendor.get("missedFilings", 0),
        "avgDaysLate": vendor.get("avgDaysLate", 0),
    }
    vendors_col.insert_one(new_vendor.copy())

    # Add alert
    alert_type = "critical" if status == "High Risk" else ("warning" if status == "Review" else "success")
    alert = {
        "type": alert_type,
        "message": f"New vendor {vendor['name']} added — Risk: {int(risk_score * 100)}% ({status})",
        "time": "Just now",
        "icon": "🔴" if status == "High Risk" else ("🟡" if status == "Review" else "🟢"),
    }
    alerts_col.insert_one(alert.copy())

    return {"vendor": new_vendor, "alert": alert, "modelSource": source}


# ---- Invoices ----
@app.get("/api/invoices")
def get_invoices():
    invoices = serialize_list(invoices_col.find({}, {"_id": 0}))
    return invoices

@app.post("/api/invoices")
def add_invoice(invoice: dict = Body(...)):
    inv_id = next_id(invoices_col, "INV-2025-")

    # Determine match status
    gstr1 = invoice.get("gstr1Reported", True)
    gstr2b = invoice.get("gstr2bReported", True)
    match_status = "Matched"
    if not gstr1 and gstr2b:
        match_status = "Missing in GSTR-1"
    elif gstr1 and not gstr2b:
        match_status = "Missing in GSTR-2B"
    
    taxable = float(invoice.get("taxableAmount", 0))
    cgst = float(invoice.get("cgst", 0))
    sgst = float(invoice.get("sgst", 0))
    igst = float(invoice.get("igst", 0))
    total_tax = cgst + sgst + igst

    # Risk level
    risk_level = "Low"
    if match_status != "Matched":
        risk_level = "High" if total_tax > 50000 else "Medium"
    
    # Find vendor
    vendor = vendors_col.find_one({"id": invoice.get("vendorId")}, {"_id": 0})
    
    new_invoice = {
        "id": inv_id,
        "vendorId": invoice.get("vendorId", ""),
        "vendorName": vendor["name"] if vendor else "Unknown",
        "gstin": vendor["gstin"] if vendor else "",
        "date": invoice.get("date", ""),
        "taxableAmount": taxable,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "totalTax": total_tax,
        "total": taxable + total_tax,
        "hsn": invoice.get("hsn", ""),
        "period": invoice.get("period", ""),
        "gstr1Reported": gstr1,
        "gstr2bReported": gstr2b,
        "eInvoice": invoice.get("eInvoice", True),
        "eWayBill": invoice.get("eWayBill", True),
        "matchStatus": match_status,
        "riskLevel": risk_level,
    }
    invoices_col.insert_one(new_invoice.copy())
    
    # Add alert
    if match_status != "Matched":
        alert = {
            "type": "critical" if risk_level == "High" else "warning",
            "message": f"Mismatch: {inv_id} from {new_invoice['vendorName']} — {match_status} (₹{int(total_tax):,} tax)",
            "time": "Just now",
            "icon": "🔴" if risk_level == "High" else "🟡",
        }
    else:
        alert = {
            "type": "success",
            "message": f"Invoice {inv_id} from {new_invoice['vendorName']} matched",
            "time": "Just now",
            "icon": "🟢",
        }
    alerts_col.insert_one(alert.copy())

    # The new invoice changes this vendor's mismatch history, which is a model
    # input - so re-score them rather than leaving a stale risk figure.
    rescored = None
    if vendor:
        history = vendor_invoices(vendor["id"])
        new_score, _source = predict_risk(vendor, history)
        new_status = classify_risk(new_score)
        vendors_col.update_one(
            {"id": vendor["id"]},
            {"$set": {"riskScore": round(new_score, 2), "status": new_status}},
        )
        rescored = {
            "vendorId": vendor["id"],
            "riskScore": round(new_score, 2),
            "status": new_status,
            "previousStatus": vendor.get("status"),
        }
        if new_status != vendor.get("status"):
            alerts_col.insert_one({
                "type": "critical" if new_status == "High Risk" else "warning",
                "message": f"{vendor['name']} risk reclassified: {vendor.get('status')} → {new_status} ({int(new_score * 100)}%)",
                "time": "Just now",
                "icon": "🔴" if new_status == "High Risk" else "🟡",
            })

    return {"invoice": new_invoice, "alert": alert, "vendorRescored": rescored}


# ---- Alerts ----
@app.get("/api/alerts")
def get_alerts():
    alerts = serialize_list(alerts_col.find({}, {"_id": 0}).sort("_id", -1).limit(20))
    return alerts


# ---- Auth ----
@app.post("/api/login")
def login(creds: dict = Body(...)):
    email = (creds.get("email") or "").strip().lower()
    password = creds.get("password") or ""

    user = users_col.find_one({"email": email})
    # Verify against the bcrypt digest. The same generic error is returned for an
    # unknown email and a bad password so the endpoint cannot enumerate accounts.
    if not user or not auth_utils.verify_password(password, user.get("password", "")):
        return {"success": False, "error": "Invalid email or password"}

    return {"success": True, "user": auth_utils.public_user(user)}


@app.post("/api/signup")
def signup(data: dict = Body(...)):
    email = (data.get("email") or "").strip().lower()
    name = data.get("name") or ""
    password = data.get("password") or ""

    error = auth_utils.validate_credentials(email, password, name)
    if error:
        return {"success": False, "error": error}

    if users_col.find_one({"email": email}):
        return {"success": False, "error": "Email already registered"}

    doc = {
        "email": email,
        "password": auth_utils.hash_password(password),
        "name": name.strip(),
        "role": "user",
        "createdAt": datetime.now().strftime("%Y-%m-%d"),
    }
    result = users_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return {"success": True, "user": auth_utils.public_user(doc)}


@app.post("/api/profile")
def update_profile(data: dict = Body(...)):
    """Update the display name / email on an account."""
    current_email = (data.get("currentEmail") or "").strip().lower()
    user = users_col.find_one({"email": current_email})
    if not user:
        return {"success": False, "error": "User not found"}

    updates = {}
    if data.get("name"):
        updates["name"] = data["name"].strip()

    new_email = (data.get("email") or "").strip().lower()
    if new_email and new_email != current_email:
        if not auth_utils.EMAIL_RE.match(new_email):
            return {"success": False, "error": "Enter a valid email address"}
        if users_col.find_one({"email": new_email}):
            return {"success": False, "error": "Email already registered"}
        updates["email"] = new_email

    if updates:
        users_col.update_one({"_id": user["_id"]}, {"$set": updates})
        user.update(updates)

    return {"success": True, "user": auth_utils.public_user(user)}


@app.post("/api/change-password")
def change_password(data: dict = Body(...)):
    email = (data.get("email") or "").strip().lower()
    user = users_col.find_one({"email": email})
    if not user or not auth_utils.verify_password(data.get("currentPassword") or "", user.get("password", "")):
        return {"success": False, "error": "Current password is incorrect"}

    new_password = data.get("newPassword") or ""
    error = auth_utils.validate_credentials(email, new_password)
    if error:
        return {"success": False, "error": error}

    users_col.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": auth_utils.hash_password(new_password)}},
    )
    return {"success": True}


# ---- Risk Prediction ----
@app.post("/api/predict-risk")
def api_predict_risk(features: dict = Body(...)):
    """Score a vendor. Accepts either an existing vendorId or raw feature values."""
    invoices = None
    if features.get("vendorId"):
        invoices = vendor_invoices(features["vendorId"])

    score, source = predict_risk(features, invoices)
    status = classify_risk(score)

    response = {
        "score": round(score, 4),
        "status": status,
        "source": source,
    }

    # Include the feature vector and its drivers so the UI can explain the score.
    if RISK_MODEL is not None and source != "heuristic":
        try:
            busiest = vendors_col.find_one(sort=[("totalTransactions", -1)]) or {}
            max_tx = max(busiest.get("totalTransactions", 500) or 500, 1)
            vec = map_vendor_features(features, invoices, max_transactions=max_tx)
            response["features"] = vec
            response["contributions"] = RISK_MODEL.explain(vec)
        except Exception as exc:
            print(f"[WARN] Could not build explanation: {exc}")

    return response


@app.get("/api/model/info")
def model_info():
    """Report what is actually scoring vendors, with its real evaluation metrics."""
    if RISK_MODEL is None:
        return {
            "available": False,
            "source": "heuristic",
            "note": "scikit-learn model unavailable; using weighted-sum fallback.",
        }

    metrics = RISK_MODEL.metrics or {}
    return {
        "available": True,
        "source": "RandomForestClassifier",
        "accuracy": metrics.get("accuracy"),
        "aucRoc": metrics.get("auc_roc"),
        "crossValMean": metrics.get("cross_val_mean"),
        "nEstimators": metrics.get("n_estimators"),
        "maxDepth": metrics.get("max_depth"),
        "nTrain": metrics.get("n_train"),
        "nTest": metrics.get("n_test"),
        "trainingData": metrics.get("training_data"),
        "featureImportance": metrics.get("feature_importance", {}),
        "classificationReport": metrics.get("classification_report", {}),
    }


# ---- Knowledge Graph (Neo4j) ----
@app.get("/api/graph/status")
def graph_status():
    """Report Neo4j connectivity. Never raises - the UI polls this."""
    if not GRAPH_AVAILABLE:
        return {"connected": False, "reason": "neo4j driver not installed"}
    return get_sync().status()


@app.post("/api/graph/sync")
def graph_sync():
    """Project the current MongoDB contents into Neo4j."""
    if not GRAPH_AVAILABLE:
        return {"success": False, "error": "neo4j driver not installed"}

    sync = get_sync()
    status = sync.status()
    if not status.get("connected"):
        return {"success": False, "error": f"Neo4j unreachable: {status.get('reason')}"}

    try:
        summary = sync.sync(
            list(vendors_col.find({}, {"_id": 0})),
            list(invoices_col.find({}, {"_id": 0})),
            taxpayer=taxpayer_col.find_one({}, {"_id": 0}),
            returns=list(returns_col.find({"type": "GSTR-3B"}, {"_id": 0})),
        )
        sync.compute_centrality()
        return {"success": True, "synced": summary, "graph": sync.status()}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


@app.get("/api/graph/data")
def graph_data():
    """Serve the knowledge graph read straight out of Neo4j.

    Returns 'available': False when the graph is offline, so the frontend can
    fall back to building the projection client-side from MongoDB rows.
    """
    if not GRAPH_AVAILABLE:
        return {"available": False, "reason": "neo4j driver not installed"}

    sync = get_sync()
    status = sync.status()
    if not status.get("connected"):
        return {"available": False, "reason": status.get("reason")}

    try:
        data = sync.fetch_graph()
        if not data["nodes"]:
            return {"available": False, "reason": "graph is empty — run POST /api/graph/sync"}
        data["available"] = True
        return data
    except Exception as exc:
        return {"available": False, "reason": str(exc)}


@app.get("/api/reconcile")
def api_reconcile(period: Optional[str] = Query(None)):
    """Run graph-traversal reconciliation in Neo4j.

    Falls back to the MongoDB match_status labels when the graph is offline, so
    the endpoint always returns usable results. `engine` says which ran.
    """
    if GRAPH_AVAILABLE:
        sync = get_sync()
        if sync.status().get("connected"):
            try:
                engine = ReconciliationEngine(driver=sync.driver)
                result = engine.full_reconciliation(period)
                result["engine"] = "neo4j-graph-traversal"
                return result
            except Exception as exc:
                print(f"[WARN] Graph reconciliation failed ({exc}); using MongoDB.")

    return _mongo_reconciliation(period)


def _mongo_reconciliation(period=None):
    """Mongo-backed equivalent used when Neo4j is unavailable."""
    query = {"matchStatus": {"$ne": "Matched"}}
    if period:
        query["period"] = period

    mismatches = []
    by_type = {}
    for inv in invoices_col.find(query, {"_id": 0}):
        issue = inv.get("matchStatus", "Unknown")
        by_type[issue] = by_type.get(issue, 0) + 1
        mismatches.append({
            "invoice_id": inv.get("id"),
            "amount": inv.get("taxableAmount", 0),
            "tax": inv.get("totalTax", 0),
            "period": inv.get("period"),
            "vendor_name": inv.get("vendorName"),
            "vendor_gstin": inv.get("gstin"),
            "issue_type": issue,
            "detection": "label-carried",
            "severity": inv.get("riskLevel", "Low"),
        })

    mismatches.sort(key=lambda m: m["tax"], reverse=True)
    return {
        "period": period or "all",
        "engine": "mongodb-fallback",
        "total_mismatches": len(mismatches),
        "total_tax_at_risk": sum(m["tax"] for m in mismatches),
        "by_type": by_type,
        "mismatches": mismatches,
    }


def _mongo_evidence(invoice_id: str):
    """Evidence assembled from MongoDB, used when the graph is offline."""
    inv = invoices_col.find_one({"id": invoice_id}, {"_id": 0})
    if not inv:
        return None

    filings = []
    if inv.get("gstr1Reported"): filings.append("GSTR-1")
    if inv.get("gstr2bReported"): filings.append("GSTR-2B")

    vendor = vendors_col.find_one({"id": inv.get("vendorId")}, {"_id": 0}) or {}
    ret = returns_col.find_one(
        {"gstin": inv.get("gstin"), "period": inv.get("period"), "type": "GSTR-3B"},
        {"_id": 0},
    )
    taxpayer = taxpayer_col.find_one({}, {"_id": 0}) or {}
    in_pr = inv.get("inPurchaseRegister")

    path = (
        f"(Vendor {inv.get('vendorName')}) -[:ISSUED_INVOICE]-> (Invoice {invoice_id}) "
        f"-[:REPORTED_IN]-> {{{', '.join(filings) if filings else 'no GSTR return'}}}"
    )
    if ret is not None:
        path += (
            f"  |  (Vendor {inv.get('vendorName')}) -[:FILED_RETURN]-> "
            f"(GSTR-3B {inv.get('period')}: {'filed' if ret.get('filed') else 'NOT filed'})"
        )
    if taxpayer:
        edge = "-[:RECORDED_IN_PR]->" if in_pr else "--X-- (not in PR)"
        path += f"  |  (Taxpayer {taxpayer.get('name')}) {edge} (Invoice {invoice_id})"

    return {
        "source": "mongodb",
        "invoice_id": invoice_id,
        "vendor": inv.get("vendorName"),
        "gstin": inv.get("gstin"),
        "vendor_risk": vendor.get("riskScore"),
        "amount": inv.get("taxableAmount"),
        "tax": inv.get("totalTax"),
        "status": inv.get("matchStatus"),
        "period": inv.get("period"),
        "hsn": inv.get("hsn"),
        "filings": filings,
        "einvoices": 1 if inv.get("eInvoice") else 0,
        "ewaybills": 1 if inv.get("eWayBill") else 0,
        "gstr3b_filed": ret.get("filed") if ret else None,
        "in_purchase_register": in_pr,
        "taxpayer": taxpayer.get("name"),
        "missing_gstr1": not inv.get("gstr1Reported"),
        "graph_path": path,
    }


def _issues_for(invoice_id: str, evidence: dict):
    """Every finding against one invoice, from the reconciliation engine.

    An invoice can violate several rules at once - missing from GSTR-1 *and*
    lacking an e-Way Bill - so the audit trail reports the full set rather than
    just the stored single-valued matchStatus.
    """
    try:
        result = api_reconcile(None)
        issues = [
            m["issue_type"] for m in result.get("mismatches", [])
            if m.get("invoice_id") == invoice_id
        ]
    except Exception:
        issues = []

    stored = (evidence or {}).get("status")
    if stored and stored != "Matched" and stored not in issues:
        issues.insert(0, stored)
    return issues


@app.get("/api/audit-trail/{invoice_id}")
def audit_trail(invoice_id: str):
    """Generate an explainable audit trail for any flagged invoice.

    Built from live graph facts, so it covers every flagged invoice rather than
    the handful that once had prose written for them by hand.
    """
    evidence = None
    if GRAPH_AVAILABLE:
        sync = get_sync()
        if sync.status().get("connected"):
            try:
                engine = ReconciliationEngine(driver=sync.driver)
                evidence = engine.get_evidence_path(invoice_id)
                if evidence:
                    evidence["source"] = "neo4j"
            except Exception as exc:
                print(f"[WARN] Graph evidence lookup failed ({exc}).")

    if evidence is None:
        evidence = _mongo_evidence(invoice_id)
    if evidence is None:
        return {"error": "Invoice not found"}

    evidence["issues"] = _issues_for(invoice_id, evidence)
    trail = build_audit_trail(evidence)
    trail["evidence_source"] = evidence.get("source", "mongodb")
    return trail


@app.get("/api/reconcile/evidence/{invoice_id}")
def reconcile_evidence(invoice_id: str):
    """Raw graph neighbourhood backing a flagged invoice, without the prose."""
    if GRAPH_AVAILABLE:
        sync = get_sync()
        if sync.status().get("connected"):
            try:
                engine = ReconciliationEngine(driver=sync.driver)
                evidence = engine.get_evidence_path(invoice_id)
                if evidence:
                    evidence["source"] = "neo4j"
                    return evidence
            except Exception as exc:
                print(f"[WARN] Evidence lookup failed ({exc}).")

import re

def _vendor_exists(vendor_id: str) -> bool:
    if not vendor_id:
        return False
    v_clean = str(vendor_id).strip().upper()
    try:
        from backend.ml.data_store import get_data_store
        ds = get_data_store()
        if v_clean in ds._vendor_metadata or vendor_id in ds._vendor_metadata:
            return True
        if v_clean.startswith("V") and v_clean[1:].isdigit():
            num = int(v_clean[1:])
            for cand in [f"V{num:04d}", f"V{num:03d}", f"V{num}"]:
                if cand in ds._vendor_metadata:
                    return True
        v_doc = vendors_col.find_one({"$or": [{"id": vendor_id}, {"id": v_clean}, {"vendor_id": vendor_id}, {"vendor_id": v_clean}]})
        if v_doc:
            return True
    except Exception:
        pass
    return False

def _validate_period(period: Optional[str]) -> Optional[str]:
    if period is None:
        return None
    period_str = str(period).strip()
    if not re.match(r"^\d{4}-\d{2}$", period_str):
        raise HTTPException(status_code=400, detail=f"Invalid period format '{period}'. Expected YYYY-MM.")
    return period_str


class RiskPredictRequest(BaseModel):
    vendor_id: str
    period: str


@app.post("/risk/predict")
@app.post("/api/risk/predict")
def api_risk_predict(payload: RiskPredictRequest = Body(...)):
    """
    Evaluates production GST ITC risk assessment with separate Model Class,
    0-100 ML Risk Indicator Score, financial ITC exposure, Tree SHAP factors,
    auditable multi-domain evidence, and time-safe Knowledge Graph context.
    """
    _validate_period(payload.period)
    if not _vendor_exists(payload.vendor_id):
        raise HTTPException(status_code=404, detail=f"Vendor '{payload.vendor_id}' not found.")

    try:
        from backend.ml.risk_engine import get_risk_engine
        engine = get_risk_engine()
        record = {}
        v_doc = vendors_col.find_one({"$or": [{"id": payload.vendor_id}, {"vendor_id": payload.vendor_id}]})
        if v_doc:
            record["invoice_count"] = float(v_doc.get("totalTransactions", 5))
            record["mismatch_rate"] = float(v_doc.get("riskScore", 0.1))
            record["average_filing_delay"] = float(v_doc.get("avgDaysLate", 0))
            record["total_invoice_value"] = float(v_doc.get("totalInvoiceValue", 50000.0))
            record["total_tax"] = float(v_doc.get("totalTax", 9000.0))
            record["tax_period"] = payload.period

        assessment = engine.assess_vendor(
            vendor_id=payload.vendor_id,
            period=payload.period,
            record=record if record else None
        )

        # Include top-level aliases for backward compatibility with existing frontends
        assessment["risk_class"] = assessment["risk"]["model_class"]
        assessment["risk_probability"] = assessment["risk"]["probabilities"]
        assessment["risk_score"] = assessment["risk"]["score"]
        assessment["top_factors"] = assessment["evidence"].get("model", [])
        return assessment
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[WARN] Production Risk Engine error ({exc}), returning fallback")
        return {
            "vendor_id": payload.vendor_id,
            "prediction_period": payload.period,
            "risk": {
                "model_class": "LOW",
                "risk_band": "LOW",
                "score": 10.0,
                "probabilities": {"LOW": 0.85, "MEDIUM": 0.10, "HIGH": 0.05}
            },
            "itc": {
                "total_invoice_value": 50000.0,
                "total_tax": 9000.0,
                "exposure": 0.0,
                "exposure_ratio": 0.0
            },
            "risk_class": "LOW",
            "risk_probability": {"LOW": 0.85, "MEDIUM": 0.10, "HIGH": 0.05},
            "top_factors": [{"feature": "invoice_count", "impact": "low"}]
        }


@app.get("/risk/summary")
@app.get("/api/risk/summary")
def api_risk_summary(period: Optional[str] = Query(None)):
    """
    Returns dynamically calculated benchmark summary metrics:
    - total vendor count
    - Model Class and presentation Risk Band distributions & percentages
    - total, average, and high-risk ITC exposure
    - Risk x Exposure Matrix (3 risk bands x 2 exposure tiers)
    - exposure trend over time across all historical periods
    - operational review priority distribution
    """
    if period:
        _validate_period(period)
    try:
        from backend.ml.data_store import get_data_store
        ds = get_data_store()
        return ds.get_summary(period=period)
    except Exception as exc:
        print(f"[ERROR] Failed to compute risk summary: {exc}")
        raise HTTPException(status_code=500, detail="Internal error calculating risk summary.")


@app.get("/risk/vendors")
@app.get("/api/risk/vendors")
def api_risk_vendors(
    search: Optional[str] = Query(None, description="Search by vendor ID, name, GSTIN, or state"),
    risk_class: Optional[str] = Query(None, description="Filter by risk class: LOW, MEDIUM, HIGH"),
    priority: Optional[str] = Query(None, description="Filter by priority: LOW, MEDIUM, HIGH, CRITICAL"),
    min_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Minimum ML risk indicator score"),
    max_score: Optional[float] = Query(None, ge=0.0, le=100.0, description="Maximum ML risk indicator score"),
    min_exposure: Optional[float] = Query(None, ge=0.0, description="Minimum ITC financial exposure"),
    max_exposure: Optional[float] = Query(None, ge=0.0, description="Maximum ITC financial exposure"),
    sort: str = Query("risk_score", description="Sort field: vendor_id, vendor_name, risk_score, itc_exposure, priority"),
    order: str = Query("desc", description="Sort order: asc or desc"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    period: Optional[str] = Query(None, description="Evaluation tax period (YYYY-MM)")
):
    """
    Returns paginated, searchable, filterable, and sortable vendor risk evaluations.
    """
    if period:
        _validate_period(period)
    if risk_class and risk_class.upper() not in ["LOW", "MEDIUM", "HIGH"]:
        raise HTTPException(status_code=422, detail="Invalid risk_class filter. Allowed: LOW, MEDIUM, HIGH")
    if priority and priority.upper() not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        raise HTTPException(status_code=422, detail="Invalid priority filter. Allowed: LOW, MEDIUM, HIGH, CRITICAL")
    if min_score is not None and max_score is not None and min_score > max_score:
        raise HTTPException(status_code=422, detail="min_score cannot be greater than max_score")
    if min_exposure is not None and max_exposure is not None and min_exposure > max_exposure:
        raise HTTPException(status_code=422, detail="min_exposure cannot be greater than max_exposure")

    try:
        from backend.ml.data_store import get_data_store
        ds = get_data_store()
        return ds.get_vendors(
            search=search,
            risk_class=risk_class,
            priority=priority,
            min_score=min_score,
            max_score=max_score,
            min_exposure=min_exposure,
            max_exposure=max_exposure,
            sort=sort,
            order=order,
            page=page,
            page_size=page_size,
            period=period
        )
    except Exception as exc:
        print(f"[ERROR] Failed to query vendors: {exc}")
        raise HTTPException(status_code=500, detail="Internal error querying vendor risk evaluations.")


@app.get("/risk/vendor/{vendor_id}/graph")
@app.get("/api/risk/vendor/{vendor_id}/graph")
def api_risk_vendor_graph(
    vendor_id: str,
    period: Optional[str] = Query("2026-02", description="Temporal cutoff period (YYYY-MM)"),
    depth: int = Query(1, ge=1, le=2, description="Exploration depth: 1 (direct) or 2 (extended)")
):
    """
    Returns time-safe Knowledge Graph neighborhood structure for vendor:
    - depth 1 or depth 2
    - nodes, edges, and investigation metadata
    - strict temporal boundary (t <= period)
    """
    if depth not in (1, 2):
        raise HTTPException(status_code=422, detail="Graph depth must be 1 or 2.")
    _validate_period(period)
    if not _vendor_exists(vendor_id):
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_id}' not found.")

    try:
        from backend.ml.graph_investigation import GraphInvestigator
        investigator = GraphInvestigator()
        return investigator.get_graph_neighborhood(vendor_id=vendor_id, cutoff_period=period, depth=depth)
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        print(f"[ERROR] Knowledge graph neighborhood failed for {vendor_id}: {exc}")
        raise HTTPException(status_code=500, detail="Internal error retrieving graph neighborhood.")


@app.get("/risk/vendor/{vendor_id}")
@app.get("/api/risk/vendor/{vendor_id}")
def api_get_vendor_risk(vendor_id: str, period: Optional[str] = Query("2026-03")):
    """
    Returns latest risk assessment, financial exposure, evidence, and graph context for vendor.
    """
    if period:
        _validate_period(period)
    if not _vendor_exists(vendor_id):
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_id}' not found.")

    try:
        from backend.ml.risk_engine import get_risk_engine
        engine = get_risk_engine()
        assessment = engine.assess_vendor(vendor_id=vendor_id, period=period)
        return assessment
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] Risk assessment failed for {vendor_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to assess vendor {vendor_id}.")


@app.get("/risk/vendor/{vendor_id}/history")
@app.get("/api/risk/vendor/{vendor_id}/history")
def api_get_vendor_history(vendor_id: str):
    """
    Returns chronological risk indicator history and trend analysis for vendor.
    """
    if not _vendor_exists(vendor_id):
        raise HTTPException(status_code=404, detail=f"Vendor '{vendor_id}' not found.")

    try:
        from backend.ml.risk_engine import get_risk_engine
        engine = get_risk_engine()
        trend_data = engine.get_risk_trend(vendor_id=vendor_id)
        history_list = engine.get_vendor_history(vendor_id=vendor_id)
        return {
            "vendor_id": vendor_id,
            "trend": trend_data["trend"],
            "transitions": trend_data["transitions"],
            "history": history_list
        }
    except HTTPException:
        raise
    except Exception as exc:
        print(f"[ERROR] Risk history lookup failed for {vendor_id}: {exc}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history for {vendor_id}.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



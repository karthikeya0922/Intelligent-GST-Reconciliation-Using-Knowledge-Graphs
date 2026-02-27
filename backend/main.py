"""
GST ReconcileAI - MongoDB-Backed FastAPI Backend
All data persisted in MongoDB. Frontend fetches and posts via REST API.
"""

from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from pymongo import MongoClient
from bson import ObjectId
import json, os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="GST ReconcileAI API",
    description="Knowledge Graph-powered GST Reconciliation Engine with MongoDB",
    version="2.0.0"
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
        users_col.insert_many([
            {"email":"admin@gstreconcile.ai","password":"admin123","name":"Admin User","role":"admin","createdAt":"2025-01-01"},
            {"email":"auditor@gstreconcile.ai","password":"auditor123","name":"Tax Auditor","role":"auditor","createdAt":"2025-03-15"},
        ])
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


# Run seed on startup
seed_data()


# ============================================================
# Risk prediction (same logic as frontend)
# ============================================================
def predict_risk(vendor_data):
    missed = min(vendor_data.get("missedFilings", 0) / 6, 1)
    late = min(vendor_data.get("avgDaysLate", 0) / 20, 1)
    tx = vendor_data.get("totalTransactions", 100)
    tx_score = 0.8 if tx < 50 else (0.4 if tx < 100 else 0.1)
    einv = 0.7 if vendor_data.get("missedFilings", 0) > 2 else 0.2

    score = missed * 0.28 + late * 0.22 + tx_score * 0.12 + einv * 0.12 + 0.3 * 0.08
    return min(max(score, 0.05), 0.95)

def classify_risk(score):
    if score >= 0.6: return "High Risk"
    if score >= 0.3: return "Review"
    return "Compliant"


# ============================================================
# API Endpoints
# ============================================================

@app.get("/")
def root():
    return {"service": "GST ReconcileAI", "status": "online", "database": "MongoDB", "version": "2.0.0"}


# ---- Vendors ----
@app.get("/api/vendors")
def get_vendors():
    vendors = serialize_list(vendors_col.find({}, {"_id": 0}))
    return vendors

@app.post("/api/vendors")
def add_vendor(vendor: dict = Body(...)):
    count = vendors_col.count_documents({})
    vid = f"V{str(count + 1).zfill(3)}"
    risk_score = predict_risk(vendor)
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
    
    return {"vendor": new_vendor, "alert": alert}


# ---- Invoices ----
@app.get("/api/invoices")
def get_invoices():
    invoices = serialize_list(invoices_col.find({}, {"_id": 0}))
    return invoices

@app.post("/api/invoices")
def add_invoice(invoice: dict = Body(...)):
    count = invoices_col.count_documents({})
    inv_id = f"INV-2025-{str(count + 1).zfill(3)}"
    
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
    
    return {"invoice": new_invoice, "alert": alert}


# ---- Alerts ----
@app.get("/api/alerts")
def get_alerts():
    alerts = serialize_list(alerts_col.find({}, {"_id": 0}).sort("_id", -1).limit(20))
    return alerts


# ---- Auth ----
@app.post("/api/login")
def login(creds: dict = Body(...)):
    user = users_col.find_one({"email": creds["email"], "password": creds["password"]}, {"_id": 0, "password": 0})
    if not user:
        return {"success": False, "error": "Invalid email or password"}
    return {"success": True, "user": user}

@app.post("/api/signup")
def signup(data: dict = Body(...)):
    if users_col.find_one({"email": data["email"]}):
        return {"success": False, "error": "Email already registered"}
    users_col.insert_one({
        "email": data["email"],
        "password": data["password"],
        "name": data["name"],
        "role": "user",
        "createdAt": datetime.now().strftime("%Y-%m-%d"),
    })
    user = {"email": data["email"], "name": data["name"], "role": "user"}
    return {"success": True, "user": user}


# ---- Risk Prediction ----
@app.post("/api/predict-risk")
def api_predict_risk(features: dict = Body(...)):
    score = predict_risk(features)
    status = classify_risk(score)
    return {"score": round(score, 4), "status": status}


# ---- Dashboard Stats ----
@app.get("/api/stats")
def get_stats():
    total_invoices = invoices_col.count_documents({})
    mismatches = invoices_col.count_documents({"matchStatus": {"$ne": "Matched"}})
    pipeline = [{"$match": {"matchStatus": {"$ne": "Matched"}}}, {"$group": {"_id": None, "total": {"$sum": "$totalTax"}}}]
    at_risk_result = list(invoices_col.aggregate(pipeline))
    at_risk = at_risk_result[0]["total"] if at_risk_result else 0
    total_vendors = vendors_col.count_documents({})
    high_risk_vendors = vendors_col.count_documents({"status": "High Risk"})
    match_rate = round(((total_invoices - mismatches) / total_invoices * 100), 1) if total_invoices > 0 else 0
    
    return {
        "totalInvoices": total_invoices,
        "totalMismatches": mismatches,
        "atRiskITC": at_risk,
        "vendorsMonitored": total_vendors,
        "highRiskVendors": high_risk_vendors,
        "matchRate": match_rate,
        "avgResolutionDays": 4.2,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

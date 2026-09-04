"""
GST Data Ingestion Module
Reads GSTR-1/2B, e-Invoice and Purchase Register files into the Neo4j Knowledge Graph

Usage:
    python ingestion.py --file gstr1_sample.json --type GSTR-1 --period 2025-07
    python ingestion.py --file purchases.csv --type purchase-register \
        --taxpayer-gstin 29AAQCQ1234M1Z8 --period 2025-07
"""

from neo4j import GraphDatabase
import json
import csv
import os
from datetime import datetime


def _num(value):
    """Coerce a CSV cell to a float; blanks and stray symbols become 0."""
    if value in (None, ""):
        return 0.0
    try:
        return float(str(value).replace(",", "").replace("₹", "").strip())
    except ValueError:
        return 0.0


class GSTIngester:
    """ETL pipeline for loading GST data into Neo4j Knowledge Graph"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    # ---- GSTR-1 Ingestion (Supplier's Sales Return) ----
    def ingest_gstr1(self, filepath, period):
        """Load GSTR-1 data - creates Vendor, Invoice, and GSTR nodes with relationships"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        with self.driver.session() as session:
            for invoice in data.get('b2b', []):
                for item in invoice.get('inv', []):
                    session.execute_write(
                        self._create_gstr1_record,
                        vendor_gstin=invoice['ctin'],
                        invoice_id=item['inum'],
                        invoice_date=item['idt'],
                        taxable_value=item.get('val', 0),
                        tax_rate=item.get('rt', 0),
                        igst=item.get('iamt', 0),
                        cgst=item.get('camt', 0),
                        sgst=item.get('samt', 0),
                        hsn=item.get('hsn', ''),
                        period=period
                    )
        print(f"✅ Ingested GSTR-1 data for period {period}")
    
    @staticmethod
    def _create_gstr1_record(tx, **kwargs):
        tx.run("""
            MERGE (v:Vendor {gstin: $vendor_gstin})
            MERGE (i:Invoice {id: $invoice_id})
            SET i.date = date($invoice_date),
                i.taxable_amount = $taxable_value,
                i.tax_rate = $tax_rate,
                i.igst = $igst,
                i.cgst = $cgst,
                i.sgst = $sgst,
                i.hsn = $hsn,
                i.source = 'GSTR-1'
            MERGE (v)-[:ISSUED_INVOICE]->(i)
            MERGE (g:GSTR {type: 'GSTR-1', period: $period})
            MERGE (i)-[:REPORTED_IN]->(g)
        """, **kwargs)
    
    # ---- GSTR-2B Ingestion (Auto-populated Purchase Return) ----
    def ingest_gstr2b(self, filepath, period):
        """Load GSTR-2B data - auto-populated inward supply details"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        with self.driver.session() as session:
            for supplier in data.get('docdata', {}).get('b2b', []):
                for inv in supplier.get('inv', []):
                    session.execute_write(
                        self._create_gstr2b_record,
                        supplier_gstin=supplier['ctin'],
                        supplier_name=supplier.get('trdnm', ''),
                        invoice_id=inv['inum'],
                        invoice_date=inv['dt'],
                        taxable_value=inv.get('val', 0),
                        igst=inv.get('iamt', 0),
                        cgst=inv.get('camt', 0),
                        sgst=inv.get('samt', 0),
                        itc_available=inv.get('itcavl', 'Y'),
                        period=period
                    )
        print(f"✅ Ingested GSTR-2B data for period {period}")
    
    @staticmethod
    def _create_gstr2b_record(tx, **kwargs):
        tx.run("""
            MERGE (v:Vendor {gstin: $supplier_gstin})
            ON CREATE SET v.name = $supplier_name
            MERGE (i:Invoice {id: $invoice_id})
            SET i.date = date($invoice_date),
                i.taxable_amount = $taxable_value,
                i.igst = $igst,
                i.cgst = $cgst,
                i.sgst = $sgst,
                i.itc_available = $itc_available,
                i.source_2b = true
            MERGE (v)-[:ISSUED_INVOICE]->(i)
            MERGE (g:GSTR {type: 'GSTR-2B', period: $period})
            MERGE (i)-[:REPORTED_IN]->(g)
        """, **kwargs)
    
    # ---- Purchase Register Ingestion (the buyer's own books) ----
    def ingest_purchase_register(self, filepath, taxpayer_gstin, period=None):
        """Load the buyer's Purchase Register from CSV or JSON.

        The PR is what the taxpayer actually booked. Reconciling it against
        GSTR-2B is the match auditors run for ITC: an entry present in one and
        absent from the other is a finding in either direction.

        CSV is accepted because that is how most accounting packages export.
        Expected columns (case-insensitive):
            invoice_no, invoice_date, supplier_gstin, taxable_value,
            cgst, sgst, igst, hsn
        """
        rows = self._read_pr_rows(filepath)

        with self.driver.session() as session:
            for row in rows:
                session.execute_write(
                    self._create_pr_record,
                    taxpayer_gstin=taxpayer_gstin,
                    supplier_gstin=row["supplier_gstin"],
                    invoice_id=row["invoice_no"],
                    invoice_date=row.get("invoice_date", ""),
                    taxable_value=_num(row.get("taxable_value")),
                    cgst=_num(row.get("cgst")),
                    sgst=_num(row.get("sgst")),
                    igst=_num(row.get("igst")),
                    hsn=str(row.get("hsn", "")),
                    period=period or row.get("period", ""),
                )
        print(f"✅ Ingested {len(rows)} Purchase Register entries")
        return len(rows)

    @staticmethod
    def _read_pr_rows(filepath):
        """Read the PR from CSV or JSON, normalising header case."""
        if filepath.lower().endswith(".json"):
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            rows = data.get("purchases", data) if isinstance(data, dict) else data
            return [{str(k).strip().lower(): v for k, v in r.items()} for r in rows]

        with open(filepath, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return [
                {str(k).strip().lower(): v for k, v in row.items() if k}
                for row in reader
            ]

    @staticmethod
    def _create_pr_record(tx, **kwargs):
        # :RECORDED_IN_PR is the edge the purchase-register checks look for. Its
        # absence on an invoice the supplier reported is the finding.
        tx.run("""
            MERGE (t:Taxpayer {gstin: $taxpayer_gstin})
            MERGE (v:Vendor {gstin: $supplier_gstin})
            MERGE (i:Invoice {id: $invoice_id})
            SET i.pr_date = $invoice_date,
                i.pr_taxable_amount = $taxable_value,
                i.pr_cgst = $cgst,
                i.pr_sgst = $sgst,
                i.pr_igst = $igst,
                i.pr_hsn = $hsn,
                i.in_purchase_register = true,
                i.period = coalesce(i.period, $period)
            MERGE (v)-[:ISSUED_INVOICE]->(i)
            MERGE (i)-[:BILLED_TO]->(t)
            MERGE (t)-[:RECORDED_IN_PR]->(i)
        """, **kwargs)

    # ---- e-Invoice Ingestion ----
    def ingest_einvoice(self, filepath):
        """Load e-Invoice data and link to existing invoices"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        with self.driver.session() as session:
            for einv in data:
                session.execute_write(
                    self._create_einvoice_record,
                    irn=einv['Irn'],
                    invoice_id=einv['DocDtls']['No'],
                    ack_date=einv.get('AckDt', ''),
                    status=einv.get('Status', 'ACT')
                )
        print(f"✅ Ingested e-Invoice data")
    
    @staticmethod
    def _create_einvoice_record(tx, **kwargs):
        tx.run("""
            MERGE (i:Invoice {id: $invoice_id})
            MERGE (e:EInvoice {irn: $irn})
            SET e.ack_date = $ack_date,
                e.status = $status
            MERGE (i)-[:ELECTRONIC_VERSION]->(e)
        """, **kwargs)
    
    # ---- Cross-Match GSTR-1 and GSTR-2B ----
    def run_matching(self, period):
        """Create MATCHES relationships between invoices appearing in both GSTR-1 and GSTR-2B"""
        with self.driver.session() as session:
            result = session.execute_write(self._match_invoices, period=period)
            print(f"✅ Matched {result} invoices for period {period}")
    
    @staticmethod
    def _match_invoices(tx, period):
        result = tx.run("""
            MATCH (i:Invoice)-[:REPORTED_IN]->(g1:GSTR {type: 'GSTR-1', period: $period})
            MATCH (i)-[:REPORTED_IN]->(g2:GSTR {type: 'GSTR-2B', period: $period})
            WHERE NOT EXISTS { (i)-[:MATCHES]->(i) }
            SET i.match_status = 'Matched'
            RETURN count(i) AS matched_count
        """, period=period)
        return result.single()["matched_count"]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="GST Data Ingestion")
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--file", required=True, help="Path to data file")
    parser.add_argument(
        "--type",
        choices=["GSTR-1", "GSTR-2B", "e-Invoice", "purchase-register"],
        required=True,
    )
    parser.add_argument("--period", help="Filing period (YYYY-MM)")
    parser.add_argument("--taxpayer-gstin", help="Buyer GSTIN (purchase-register only)")
    args = parser.parse_args()
    
    ingester = GSTIngester(uri=args.uri)
    try:
        if args.type == "GSTR-1":
            ingester.ingest_gstr1(args.file, args.period)
        elif args.type == "GSTR-2B":
            ingester.ingest_gstr2b(args.file, args.period)
        elif args.type == "e-Invoice":
            ingester.ingest_einvoice(args.file)
        elif args.type == "purchase-register":
            if not args.taxpayer_gstin:
                parser.error("--taxpayer-gstin is required for purchase-register")
            ingester.ingest_purchase_register(
                args.file, args.taxpayer_gstin, args.period
            )
    finally:
        ingester.close()

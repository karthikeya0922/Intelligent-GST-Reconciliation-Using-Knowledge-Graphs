"""
GST Reconciliation Engine
Detects mismatches between GSTR-1 and GSTR-2B using Neo4j graph traversal.
Classifies mismatches by type and severity.
"""

from neo4j import GraphDatabase


class ReconciliationEngine:
    """Graph-traversal reconciliation engine for GST filings"""
    
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="password"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def find_missing_invoices(self, period):
        """
        Find invoices in GSTR-2B that are NOT in vendor's GSTR-1.
        This multi-hop traversal: GSTR-2B → Invoice → MATCHES → GSTR-1
        """
        with self.driver.session() as session:
            result = session.execute_read(self._query_missing, period=period)
            return result
    
    @staticmethod
    def _query_missing(tx, period):
        query = """
        MATCH (p:Invoice)-[:REPORTED_IN]->(g2:GSTR {type:'GSTR-2B', period:$period})
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(p)
        WHERE NOT EXISTS {
            MATCH (p)-[:REPORTED_IN]->(:GSTR {type:'GSTR-1', period:$period})
        }
        RETURN p.id AS invoice_id, 
               p.taxable_amount AS amount,
               p.cgst + p.sgst + p.igst AS tax,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'Missing in GSTR-1' AS issue_type
        ORDER BY tax DESC
        """
        return [dict(row) for row in tx.run(query, period=period)]
    
    def find_tax_mismatches(self, period):
        """
        Find invoices where tax amounts differ between GSTR-1 and GSTR-2B.
        """
        with self.driver.session() as session:
            result = session.execute_read(self._query_tax_diff, period=period)
            return result
    
    @staticmethod
    def _query_tax_diff(tx, period):
        query = """
        MATCH (i:Invoice)-[:REPORTED_IN]->(g1:GSTR {type:'GSTR-1', period:$period})
        MATCH (i)-[:REPORTED_IN]->(g2:GSTR {type:'GSTR-2B', period:$period})
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i)
        WHERE i.cgst_gstr1 <> i.cgst OR i.sgst_gstr1 <> i.sgst
        RETURN i.id AS invoice_id,
               abs(i.cgst - i.cgst_gstr1) + abs(i.sgst - i.sgst_gstr1) AS tax_difference,
               v.name AS vendor_name,
               'Tax Amount Mismatch' AS issue_type
        ORDER BY tax_difference DESC
        """
        return [dict(row) for row in tx.run(query, period=period)]
    
    def find_hsn_mismatches(self, period):
        """Find invoices where HSN code differs between filings"""
        with self.driver.session() as session:
            return session.execute_read(self._query_hsn_diff, period=period)
    
    @staticmethod
    def _query_hsn_diff(tx, period):
        query = """
        MATCH (i:Invoice)-[:REPORTED_IN]->(g1:GSTR {type:'GSTR-1', period:$period})
        MATCH (i)-[:REPORTED_IN]->(g2:GSTR {type:'GSTR-2B', period:$period})
        WHERE i.hsn_gstr1 <> i.hsn
        RETURN i.id AS invoice_id, i.hsn AS hsn_2b, i.hsn_gstr1 AS hsn_1,
               'HSN Mismatch' AS issue_type
        """
        return [dict(row) for row in tx.run(query, period=period)]
    
    def find_missing_ewaybills(self, period):
        """Find invoices above threshold with no e-Way Bill"""
        with self.driver.session() as session:
            return session.execute_read(self._query_missing_ewb, period=period)
    
    @staticmethod
    def _query_missing_ewb(tx, period):
        query = """
        MATCH (i:Invoice)-[:REPORTED_IN]->(g:GSTR {period:$period})
        WHERE i.taxable_amount > 50000
        AND NOT EXISTS { MATCH (i)-[:COVERS_SHIPMENT]->(:EWayBill) }
        RETURN i.id AS invoice_id, i.taxable_amount AS amount,
               'E-Way Bill Missing' AS issue_type
        """
        return [dict(row) for row in tx.run(query, period=period)]
    
    def classify_mismatch(self, invoice, vendor_history):
        """Rule-based risk classification with financial weighting"""
        if invoice['tax'] > 100000:
            return "High Risk"
        elif vendor_history.get('past_mismatches', 0) > 5:
            return "High Risk"
        elif invoice['tax'] > 50000:
            return "Medium Risk"
        elif vendor_history.get('past_mismatches', 0) > 2:
            return "Medium Risk"
        return "Low Risk"
    
    def full_reconciliation(self, period):
        """Run complete reconciliation for a period"""
        missing = self.find_missing_invoices(period)
        tax_diff = self.find_tax_mismatches(period)
        hsn_diff = self.find_hsn_mismatches(period)
        ewb_missing = self.find_missing_ewaybills(period)
        
        all_mismatches = missing + tax_diff + hsn_diff + ewb_missing
        
        # Sort by financial impact
        all_mismatches.sort(key=lambda x: x.get('tax', x.get('amount', 0)), reverse=True)
        
        return {
            "period": period,
            "total_mismatches": len(all_mismatches),
            "by_type": {
                "missing_in_gstr1": len(missing),
                "tax_amount_mismatch": len(tax_diff),
                "hsn_mismatch": len(hsn_diff),
                "eway_bill_missing": len(ewb_missing),
            },
            "mismatches": all_mismatches
        }


if __name__ == "__main__":
    engine = ReconciliationEngine()
    try:
        result = engine.full_reconciliation("2025-07")
        print(f"Found {result['total_mismatches']} mismatches")
        for m in result['mismatches'][:5]:
            print(f"  - {m['invoice_id']}: {m['issue_type']}")
    finally:
        engine.close()

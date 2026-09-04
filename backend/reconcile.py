"""
GST Reconciliation Engine
Detects mismatches between GSTR-1 and GSTR-2B using Neo4j graph traversal.

Two classes of check run here:

*Structural* checks derive a mismatch purely from the shape of the graph - an
absent :REPORTED_IN edge to GSTR-1, or an absent :COVERS_SHIPMENT edge to an
e-Way Bill. These are the checks a knowledge graph genuinely buys you, and they
need no precomputed label.

*Field-level* checks (tax amount, HSN) compare the same invoice as filed by the
supplier against the buyer's auto-populated copy. They need both source records
on the node - which the dual-source ingestion path (ingestion.py) provides via
the `*_gstr1` properties. When the graph is projected from the MongoDB store
instead (graph_sync.py), each invoice exists once with a `match_status` already
determined upstream, so those checks read that label. Each result carries a
`detection` field saying which of the two it was, so nothing is overstated.
"""

from neo4j import GraphDatabase


class ReconciliationEngine:
    """Graph-traversal reconciliation engine for GST filings."""

    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="gstreconcile",
                 driver=None):
        # An existing driver can be injected so the API reuses one connection pool.
        self._owns_driver = driver is None
        self.driver = driver or GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        if self._owns_driver:
            self.driver.close()

    # ------------------------------------------------------------------
    # Structural checks - derived from missing edges in the graph
    # ------------------------------------------------------------------
    def find_missing_invoices(self, period=None):
        """Invoices in GSTR-2B with no GSTR-1 counterpart.

        This is the ITC-blocking case under s.16(2)(aa) CGST Act: the buyer can
        see the invoice, but the supplier never reported it.
        """
        with self.driver.session() as session:
            return session.execute_read(self._query_missing, period=period)

    @staticmethod
    def _query_missing(tx, period):
        query = """
        MATCH (p:Invoice)-[:REPORTED_IN]->(g2:GSTR {type:'GSTR-2B'})
        WHERE $period IS NULL OR g2.period = $period
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(p)
        WHERE NOT EXISTS {
            MATCH (p)-[:REPORTED_IN]->(g1:GSTR {type:'GSTR-1'})
            WHERE g1.period = g2.period
        }
        RETURN p.id AS invoice_id,
               p.taxable_amount AS amount,
               coalesce(p.cgst, 0) + coalesce(p.sgst, 0) + coalesce(p.igst, 0) AS tax,
               p.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'Missing in GSTR-1' AS issue_type,
               'structural' AS detection
        ORDER BY tax DESC
        """
        return [dict(row) for row in tx.run(query, period=period)]

    def find_missing_ewaybills(self, period=None, threshold=50000):
        """Invoices above the e-Way Bill threshold with no linked EWayBill node."""
        with self.driver.session() as session:
            return session.execute_read(
                self._query_missing_ewb, period=period, threshold=threshold
            )

    @staticmethod
    def _query_missing_ewb(tx, period, threshold):
        query = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)
        WHERE ($period IS NULL OR i.period = $period)
          AND i.taxable_amount > $threshold
          AND NOT EXISTS { MATCH (i)-[:COVERS_SHIPMENT]->(:EWayBill) }
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.cgst, 0) + coalesce(i.sgst, 0) + coalesce(i.igst, 0) AS tax,
               i.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'E-Way Bill Missing' AS issue_type,
               'structural' AS detection
        ORDER BY amount DESC
        """
        return [dict(row) for row in tx.run(query, period=period, threshold=threshold)]

    def find_orphan_einvoices(self, period=None):
        """Invoices with no e-Invoice IRN despite being reported.

        e-Invoicing is mandatory above the turnover threshold, so a reported
        invoice with no IRN is a filing irregularity worth surfacing.
        """
        with self.driver.session() as session:
            return session.execute_read(self._query_orphan_einv, period=period)

    @staticmethod
    def _query_orphan_einv(tx, period):
        query = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)-[:REPORTED_IN]->(g:GSTR)
        WHERE ($period IS NULL OR i.period = $period)
          AND NOT EXISTS { MATCH (i)-[:ELECTRONIC_VERSION]->(:EInvoice) }
        RETURN DISTINCT i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.cgst, 0) + coalesce(i.sgst, 0) + coalesce(i.igst, 0) AS tax,
               i.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'e-Invoice Missing' AS issue_type,
               'structural' AS detection
        ORDER BY tax DESC
        """
        return [dict(row) for row in tx.run(query, period=period)]

    def find_unpaid_tax_chains(self, period=None):
        """Invoices reported in GSTR-1 whose supplier never filed GSTR-3B.

        This is the multi-hop check the whole graph model exists for. One hop
        out the invoice looks clean - it is in GSTR-1, so the supplier declared
        it. The second hop, through the vendor to their GSTR-3B, reveals the
        tax was never actually remitted. A flat GSTR-1 vs GSTR-2B table match
        cannot see this at all.

            (Invoice)-[:REPORTED_IN]->(GSTR-1)              declared
            (Invoice)<-[:ISSUED_INVOICE]-(Vendor)-[:FILED_RETURN]->(GSTR3B)
                                                            but not paid
        """
        with self.driver.session() as session:
            return session.execute_read(self._query_unpaid_chain, period=period)

    @staticmethod
    def _query_unpaid_chain(tx, period):
        query = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)-[:REPORTED_IN]->(g1:GSTR {type:'GSTR-1'})
        WHERE ($period IS NULL OR i.period = $period)
        MATCH (v)-[:FILED_RETURN]->(g3:GSTR3B {period: i.period})
        WHERE g3.filed = false
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.total_tax, 0) AS tax,
               i.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               g3.status AS gstr3b_status,
               'Supplier GSTR-3B Not Filed' AS issue_type,
               'structural' AS detection
        ORDER BY tax DESC
        """
        return [dict(row) for row in tx.run(query, period=period)]

    def find_purchase_register_gaps(self, period=None):
        """Mismatches between the buyer's Purchase Register and GSTR-2B.

        Both directions matter, and they mean opposite things:

        * in GSTR-2B but not in the PR - the buyer never booked a purchase the
          supplier says they made. Unrecorded liability, or a fake invoice
          raised against the taxpayer's GSTIN.
        * in the PR but not in GSTR-2B - the buyer booked it and expects the
          credit, but the supplier never reported it, so no ITC is available.
        """
        with self.driver.session() as session:
            return session.execute_read(self._query_pr_gaps, period=period)

    @staticmethod
    def _query_pr_gaps(tx, period):
        # In 2B, absent from the purchase register.
        not_booked = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)-[:REPORTED_IN]->(:GSTR {type:'GSTR-2B'})
        WHERE ($period IS NULL OR i.period = $period)
          AND NOT EXISTS { MATCH (:Taxpayer)-[:RECORDED_IN_PR]->(i) }
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.total_tax, 0) AS tax,
               i.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'Missing in Purchase Register' AS issue_type,
               'structural' AS detection
        ORDER BY tax DESC
        """
        rows = [dict(r) for r in tx.run(not_booked, period=period)]

        # Booked by the buyer, but the supplier never reported it into 2B.
        no_credit = """
        MATCH (:Taxpayer)-[:RECORDED_IN_PR]->(i:Invoice)<-[:ISSUED_INVOICE]-(v:Vendor)
        WHERE ($period IS NULL OR i.period = $period)
          AND NOT EXISTS { MATCH (i)-[:REPORTED_IN]->(:GSTR {type:'GSTR-2B'}) }
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.total_tax, 0) AS tax,
               i.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'In Purchase Register, Missing in GSTR-2B' AS issue_type,
               'structural' AS detection
        ORDER BY tax DESC
        """
        return rows + [dict(r) for r in tx.run(no_credit, period=period)]

    # ------------------------------------------------------------------
    # Field-level checks
    # ------------------------------------------------------------------
    def find_tax_mismatches(self, period=None):
        """Invoices whose tax amounts differ between GSTR-1 and GSTR-2B."""
        with self.driver.session() as session:
            return session.execute_read(self._query_tax_diff, period=period)

    @staticmethod
    def _query_tax_diff(tx, period):
        # Dual-source path: both filings' figures are on the node.
        dual = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)
        WHERE ($period IS NULL OR i.period = $period)
          AND i.cgst_gstr1 IS NOT NULL
          AND (i.cgst_gstr1 <> i.cgst OR i.sgst_gstr1 <> i.sgst)
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               abs(i.cgst - i.cgst_gstr1) + abs(i.sgst - i.sgst_gstr1) AS tax,
               i.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'Tax Amount Mismatch' AS issue_type,
               'field-level' AS detection
        ORDER BY tax DESC
        """
        rows = [dict(r) for r in tx.run(dual, period=period)]
        if rows:
            return rows

        # Single-source projection: fall back to the upstream label.
        labelled = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)
        WHERE ($period IS NULL OR i.period = $period)
          AND i.match_status = 'Tax Amount Mismatch'
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.total_tax, 0) AS tax,
               i.period AS period,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'Tax Amount Mismatch' AS issue_type,
               'label-carried' AS detection
        ORDER BY tax DESC
        """
        return [dict(r) for r in tx.run(labelled, period=period)]

    def find_hsn_mismatches(self, period=None):
        """Invoices whose HSN classification differs between filings."""
        with self.driver.session() as session:
            return session.execute_read(self._query_hsn_diff, period=period)

    @staticmethod
    def _query_hsn_diff(tx, period):
        dual = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)
        WHERE ($period IS NULL OR i.period = $period)
          AND i.hsn_gstr1 IS NOT NULL AND i.hsn_gstr1 <> i.hsn
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.total_tax, 0) AS tax,
               i.period AS period,
               i.hsn AS hsn_2b,
               i.hsn_gstr1 AS hsn_1,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'HSN Mismatch' AS issue_type,
               'field-level' AS detection
        """
        rows = [dict(r) for r in tx.run(dual, period=period)]
        if rows:
            return rows

        labelled = """
        MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)
        WHERE ($period IS NULL OR i.period = $period)
          AND i.match_status = 'HSN Mismatch'
        RETURN i.id AS invoice_id,
               i.taxable_amount AS amount,
               coalesce(i.total_tax, 0) AS tax,
               i.period AS period,
               i.hsn AS hsn_2b,
               v.name AS vendor_name,
               v.gstin AS vendor_gstin,
               'HSN Mismatch' AS issue_type,
               'label-carried' AS detection
        """
        return [dict(r) for r in tx.run(labelled, period=period)]

    # ------------------------------------------------------------------
    # Evidence path - what the audit trail cites
    # ------------------------------------------------------------------
    def get_evidence_path(self, invoice_id):
        """Return the concrete graph neighbourhood backing a flagged invoice."""
        with self.driver.session() as session:
            record = session.run(
                """
                MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice {id: $invoice_id})
                OPTIONAL MATCH (i)-[:REPORTED_IN]->(g:GSTR)
                OPTIONAL MATCH (i)-[:ELECTRONIC_VERSION]->(e:EInvoice)
                OPTIONAL MATCH (i)-[:COVERS_SHIPMENT]->(w:EWayBill)
                OPTIONAL MATCH (v)-[:FILED_RETURN]->(g3:GSTR3B {period: i.period})
                // Bind the taxpayer independently of the PR edge. Matching
                // through :RECORDED_IN_PR would leave `t` null in exactly the
                // case worth reporting - the purchase that was never booked.
                OPTIONAL MATCH (t:Taxpayer)
                OPTIONAL MATCH (t)-[pr:RECORDED_IN_PR]->(i)
                RETURN v.name AS vendor, v.gstin AS gstin, v.risk_score AS vendor_risk,
                       i.taxable_amount AS amount, i.total_tax AS tax,
                       i.match_status AS status, i.period AS period, i.hsn AS hsn,
                       collect(DISTINCT g.type) AS filings,
                       count(DISTINCT e) AS einvoices,
                       count(DISTINCT w) AS ewaybills,
                       head(collect(DISTINCT g3.filed)) AS gstr3b_filed,
                       count(pr) > 0 AS in_purchase_register,
                       head(collect(DISTINCT t.name)) AS taxpayer
                """,
                invoice_id=invoice_id,
            ).single()
        if not record:
            return None

        data = dict(record)
        data["invoice_id"] = invoice_id
        filings = data.get("filings") or []

        # Spell out the traversal that produced the finding, including the second
        # hop through the vendor to their GSTR-3B when that is what failed.
        path = (
            f"(Vendor {data['vendor']}) -[:ISSUED_INVOICE]-> (Invoice {invoice_id}) "
            f"-[:REPORTED_IN]-> {{{', '.join(filings) if filings else 'no GSTR return'}}}"
        )
        if data.get("gstr3b_filed") is not None:
            state = "filed" if data["gstr3b_filed"] else "NOT filed"
            path += (
                f"  |  (Vendor {data['vendor']}) -[:FILED_RETURN]-> "
                f"(GSTR-3B {data['period']}: {state})"
            )
        if data.get("taxpayer"):
            edge = "-[:RECORDED_IN_PR]->" if data.get("in_purchase_register") else "--X-- (not in PR)"
            path += f"  |  (Taxpayer {data['taxpayer']}) {edge} (Invoice {invoice_id})"

        data["graph_path"] = path
        data["missing_gstr1"] = "GSTR-1" not in filings
        return data

    # ------------------------------------------------------------------
    def classify_mismatch(self, invoice, vendor_history):
        """Rule-based risk classification with financial weighting."""
        tax = invoice.get("tax") or 0
        past = (vendor_history or {}).get("past_mismatches", 0)
        if tax > 100000 or past > 5:
            return "High Risk"
        if tax > 50000 or past > 2:
            return "Medium Risk"
        return "Low Risk"

    def full_reconciliation(self, period=None):
        """Run every check for a period (or all periods when period is None)."""
        missing = self.find_missing_invoices(period)
        tax_diff = self.find_tax_mismatches(period)
        hsn_diff = self.find_hsn_mismatches(period)
        ewb_missing = self.find_missing_ewaybills(period)
        einv_missing = self.find_orphan_einvoices(period)
        unpaid = self.find_unpaid_tax_chains(period)
        pr_gaps = self.find_purchase_register_gaps(period)

        all_mismatches = (
            missing + tax_diff + hsn_diff + ewb_missing + einv_missing + unpaid + pr_gaps
        )

        for m in all_mismatches:
            m["severity"] = self.classify_mismatch(m, {})

        all_mismatches.sort(key=lambda x: x.get("tax") or x.get("amount") or 0, reverse=True)

        pr_missing = sum(1 for m in pr_gaps if m["issue_type"] == "Missing in Purchase Register")

        return {
            "period": period or "all",
            "total_mismatches": len(all_mismatches),
            "total_tax_at_risk": sum(m.get("tax") or 0 for m in all_mismatches),
            "by_type": {
                "missing_in_gstr1": len(missing),
                "tax_amount_mismatch": len(tax_diff),
                "hsn_mismatch": len(hsn_diff),
                "eway_bill_missing": len(ewb_missing),
                "einvoice_missing": len(einv_missing),
                "supplier_gstr3b_not_filed": len(unpaid),
                "missing_in_purchase_register": pr_missing,
                "pr_not_in_gstr2b": len(pr_gaps) - pr_missing,
            },
            "mismatches": all_mismatches,
        }


if __name__ == "__main__":
    engine = ReconciliationEngine()
    try:
        result = engine.full_reconciliation()
        print(f"Found {result['total_mismatches']} mismatches")
        for m in result["mismatches"][:10]:
            print(f"  - {m['invoice_id']}: {m['issue_type']} ({m['detection']}) "
                  f"Rs.{m.get('tax', 0):,.0f}")
    finally:
        engine.close()

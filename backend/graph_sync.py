"""
MongoDB -> Neo4j Knowledge Graph sync.

MongoDB is the system of record for vendors and invoices. Neo4j is the graph
projection those documents are reconciled in. This module pushes the Mongo
collections into the node/relationship schema that reconcile.py queries:

    (Vendor)-[:ISSUED_INVOICE]->(Invoice)-[:REPORTED_IN]->(GSTR {type, period})
    (Invoice)-[:ELECTRONIC_VERSION]->(EInvoice)
    (Invoice)-[:COVERS_SHIPMENT]->(EWayBill)

Neo4j is optional. If it is unreachable the API keeps serving Mongo-derived
results and reports the graph as offline rather than failing.
"""

import os

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import Neo4jError, ServiceUnavailable

    NEO4J_AVAILABLE = True
except ImportError:  # driver not installed
    GraphDatabase = None
    Neo4jError = ServiceUnavailable = Exception
    NEO4J_AVAILABLE = False


NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "gstreconcile")

# Constraints keep MERGE fast and prevent duplicate nodes across repeated syncs.
CONSTRAINTS = [
    "CREATE CONSTRAINT vendor_gstin IF NOT EXISTS FOR (v:Vendor) REQUIRE v.gstin IS UNIQUE",
    "CREATE CONSTRAINT invoice_id IF NOT EXISTS FOR (i:Invoice) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT einvoice_irn IF NOT EXISTS FOR (e:EInvoice) REQUIRE e.irn IS UNIQUE",
    "CREATE CONSTRAINT ewaybill_id IF NOT EXISTS FOR (w:EWayBill) REQUIRE w.id IS UNIQUE",
]


class GraphSync:
    """Projects MongoDB documents into the Neo4j knowledge graph."""

    def __init__(self, uri=None, user=None, password=None):
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self._driver = None

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------
    @property
    def driver(self):
        if not NEO4J_AVAILABLE:
            raise RuntimeError("neo4j driver is not installed")
        if self._driver is None:
            kwargs = {"auth": (self.user, self.password)}
            # The field-level checks probe for `*_gstr1` properties that only the
            # dual-source ingestion path populates. Their absence is expected, not
            # a fault, so ask the server not to emit "property key does not exist"
            # notifications rather than spamming them on every reconcile.
            # (notifications_min_severity suppresses them server-side;
            # warn_notification_severity only gates the client-side warning.)
            try:
                from neo4j import NotificationMinimumSeverity

                kwargs["notifications_min_severity"] = NotificationMinimumSeverity.OFF
            except ImportError:
                pass  # older driver: notifications stay on, harmless
            self._driver = GraphDatabase.driver(self.uri, **kwargs)
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def status(self):
        """Report graph connectivity without raising. Safe to call on every request."""
        if not NEO4J_AVAILABLE:
            return {"connected": False, "reason": "neo4j driver not installed", "uri": self.uri}
        try:
            self.driver.verify_connectivity()
            with self.driver.session() as session:
                counts = session.run(
                    """
                    MATCH (n)
                    WITH labels(n)[0] AS label, count(*) AS c
                    RETURN collect({label: label, count: c}) AS nodes
                    """
                ).single()
                rels = session.run("MATCH ()-[r]->() RETURN count(r) AS c").single()["c"]
            return {
                "connected": True,
                "uri": self.uri,
                "nodes": {row["label"]: row["count"] for row in (counts["nodes"] if counts else [])},
                "relationships": rels,
            }
        except Exception as exc:
            self.close()
            return {"connected": False, "reason": str(exc).split("\n")[0], "uri": self.uri}

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------
    def ensure_constraints(self):
        with self.driver.session() as session:
            for stmt in CONSTRAINTS:
                session.run(stmt)

    def sync(self, vendors, invoices, wipe=True):
        """Project vendors and invoices into Neo4j. Returns a summary dict."""
        self.ensure_constraints()

        with self.driver.session() as session:
            if wipe:
                # The graph is a derived projection, so a clean rebuild keeps it
                # consistent with Mongo after deletes.
                session.run("MATCH (n) DETACH DELETE n")
                self.ensure_constraints()

            session.execute_write(self._write_vendors, vendors=vendors)
            session.execute_write(self._write_invoices, invoices=invoices)
            matched = session.execute_write(self._mark_matched)

        return {
            "vendors": len(vendors),
            "invoices": len(invoices),
            "matched": matched,
        }

    @staticmethod
    def _write_vendors(tx, vendors):
        tx.run(
            """
            UNWIND $vendors AS v
            MERGE (vendor:Vendor {gstin: v.gstin})
            SET vendor.id = v.id,
                vendor.name = v.name,
                vendor.state = v.state,
                vendor.risk_score = v.riskScore,
                vendor.status = v.status,
                vendor.transaction_volume = v.totalTransactions,
                vendor.missed_filings = v.missedFilings,
                vendor.filing_delay_days = v.avgDaysLate
            """,
            vendors=vendors,
        )

    @staticmethod
    def _write_invoices(tx, invoices):
        # Invoice -> Vendor, and Invoice -> the GSTR returns it was reported in.
        tx.run(
            """
            UNWIND $invoices AS inv
            MERGE (i:Invoice {id: inv.id})
            SET i.date = inv.date,
                i.taxable_amount = inv.taxableAmount,
                i.cgst = inv.cgst,
                i.sgst = inv.sgst,
                i.igst = inv.igst,
                i.total_tax = inv.totalTax,
                i.hsn = inv.hsn,
                i.period = inv.period,
                i.match_status = inv.matchStatus,
                i.risk_level = inv.riskLevel
            WITH i, inv
            MATCH (v:Vendor {gstin: inv.gstin})
            MERGE (v)-[:ISSUED_INVOICE]->(i)

            FOREACH (_ IN CASE WHEN inv.gstr1Reported THEN [1] ELSE [] END |
                MERGE (g1:GSTR {type: 'GSTR-1', period: inv.period})
                MERGE (i)-[:REPORTED_IN]->(g1))

            FOREACH (_ IN CASE WHEN inv.gstr2bReported THEN [1] ELSE [] END |
                MERGE (g2:GSTR {type: 'GSTR-2B', period: inv.period})
                MERGE (i)-[:REPORTED_IN]->(g2))

            FOREACH (_ IN CASE WHEN inv.eInvoice THEN [1] ELSE [] END |
                MERGE (e:EInvoice {irn: 'IRN-' + inv.id})
                MERGE (i)-[:ELECTRONIC_VERSION]->(e))

            FOREACH (_ IN CASE WHEN inv.eWayBill THEN [1] ELSE [] END |
                MERGE (w:EWayBill {id: 'EWB-' + inv.id})
                MERGE (i)-[:COVERS_SHIPMENT]->(w))
            """,
            invoices=invoices,
        )

    @staticmethod
    def _mark_matched(tx):
        result = tx.run(
            """
            MATCH (i:Invoice)-[:REPORTED_IN]->(:GSTR {type: 'GSTR-1'})
            MATCH (i)-[:REPORTED_IN]->(:GSTR {type: 'GSTR-2B'})
            SET i.reconciled = true
            RETURN count(DISTINCT i) AS matched
            """
        )
        return result.single()["matched"]

    # ------------------------------------------------------------------
    # Read the graph back for visualisation
    # ------------------------------------------------------------------
    # Neo4j label -> the group key the frontend renders with.
    _GROUPS = {
        "Vendor": "vendor",
        "Invoice": "invoice",
        "GSTR": "gstr",
        "EInvoice": "einvoice",
        "EWayBill": "ewaybill",
    }
    # Relationship type -> the frontend's edge style key.
    _EDGE_TYPES = {
        "ISSUED_INVOICE": "issued",
        "REPORTED_IN": "reported",
        "ELECTRONIC_VERSION": "einvoice",
        "COVERS_SHIPMENT": "ewaybill",
    }

    def fetch_graph(self):
        """Return the graph as {nodes, links} for the visualisation.

        This is the real thing - read back out of Neo4j rather than rebuilt in
        the browser from flat MongoDB rows.
        """
        with self.driver.session() as session:
            node_rows = session.run(
                """
                MATCH (n)
                WHERE n:Vendor OR n:Invoice OR n:GSTR OR n:EInvoice OR n:EWayBill
                OPTIONAL MATCH (n)-[r]-()
                RETURN elementId(n) AS eid,
                       labels(n)[0] AS label,
                       properties(n) AS props,
                       count(r) AS degree
                """
            ).data()

            link_rows = session.run(
                """
                MATCH (a)-[r]->(b)
                RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS rel
                """
            ).data()

        nodes = []
        for row in node_rows:
            props, label = row["props"], row["label"]
            group = self._GROUPS.get(label, "invoice")
            node = {
                "id": row["eid"],
                "group": group,
                "degree": row["degree"],
                "neo4jLabel": label,
            }

            if group == "vendor":
                name = props.get("name", "Vendor")
                node.update({
                    "label": name if len(name) <= 14 else name[:13] + "…",
                    "fullName": name,
                    "gstin": props.get("gstin"),
                    "state": props.get("state"),
                    "risk": props.get("risk_score"),
                    "status": props.get("status"),
                    "centrality": props.get("pagerank"),
                })
            elif group == "invoice":
                inv_id = props.get("id", "")
                match_status = props.get("match_status")
                node.update({
                    "label": inv_id.replace("INV-2025-", "INV-"),
                    "invoiceId": inv_id,
                    "amount": (props.get("taxable_amount") or 0) + (props.get("total_tax") or 0),
                    "taxableAmount": props.get("taxable_amount"),
                    "totalTax": props.get("total_tax"),
                    "hsn": props.get("hsn"),
                    "period": props.get("period"),
                    "matchStatus": match_status,
                    "riskLevel": props.get("risk_level"),
                    "status": "flagged" if match_status and match_status != "Matched" else "matched",
                })
            elif group == "gstr":
                gtype, period = props.get("type", "GSTR"), props.get("period", "")
                node.update({
                    "label": f"{gtype} {period}", "type": gtype, "period": period,
                })
            elif group == "einvoice":
                irn = props.get("irn", "")
                node.update({"label": irn.replace("IRN-INV-2025-", "IRN-"), "irn": irn})
            else:  # ewaybill
                wid = props.get("id", "")
                node.update({"label": wid.replace("EWB-INV-2025-", "EWB-"), "ewbId": wid})

            nodes.append(node)

        links = [
            {
                "source": r["source"],
                "target": r["target"],
                "label": r["rel"],
                "type": self._EDGE_TYPES.get(r["rel"], "reported"),
            }
            for r in link_rows
        ]
        return {"nodes": nodes, "links": links, "source": "neo4j"}

    # ------------------------------------------------------------------
    # Graph analytics used as ML features
    # ------------------------------------------------------------------
    def compute_centrality(self):
        """Degree centrality per vendor, normalised to [0, 1].

        Written in plain Cypher rather than GDS PageRank so it runs on a stock
        Neo4j image with no plugins installed.
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (v:Vendor)
                OPTIONAL MATCH (v)-[:ISSUED_INVOICE]->(i:Invoice)
                WITH v, count(i) AS degree
                WITH collect({v: v, d: degree}) AS rows
                // reduce() rather than max(): the aggregate warns about null
                // elimination when a vendor has no invoices.
                WITH rows, reduce(m = 0, r IN rows |
                        CASE WHEN r.d > m THEN r.d ELSE m END) AS maxDeg
                UNWIND rows AS row
                SET row.v.pagerank = CASE WHEN maxDeg > 0
                                          THEN toFloat(row.d) / maxDeg
                                          ELSE 0.0 END
                """
            )


_SYNC = None


def get_sync():
    """Process-wide singleton."""
    global _SYNC
    if _SYNC is None:
        _SYNC = GraphSync()
    return _SYNC


if __name__ == "__main__":
    from pymongo import MongoClient

    mongo = MongoClient(os.environ.get("MONGODB_URI", "mongodb://localhost:27017"))
    db = mongo["gst_reconcile_ai"]

    sync = get_sync()
    print("Status:", sync.status())
    summary = sync.sync(
        list(db["vendors"].find({}, {"_id": 0})),
        list(db["invoices"].find({}, {"_id": 0})),
    )
    sync.compute_centrality()
    print("Synced:", summary)
    print("Status:", sync.status())
    sync.close()

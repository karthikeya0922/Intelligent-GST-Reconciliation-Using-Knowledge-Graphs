import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            # Suppress header/footer on cover page
            return
        
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Header
        self.drawString(54, 750, "GST ReconcileAI — System Architecture & Technical Report")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 742, 558, 742)
        
        # Footer
        self.line(54, 50, 558, 50)
        self.drawString(54, 36, "Confidential — For Internal Audit & Technical Review")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.restoreState()

def create_pdf(filename="GST_ReconcileAI_Comprehensive_Report.pdf"):
    target_path = os.path.abspath(filename)
    doc = SimpleDocTemplate(
        target_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#1E293B")     # Dark Slate
    ACCENT = colors.HexColor("#2563EB")      # Royal Blue
    SECONDARY = colors.HexColor("#0F766E")   # Teal
    DARK_TEXT = colors.HexColor("#0F172A")   # Near Black
    MUTED_TEXT = colors.HexColor("#475569")  # Slate Muted
    BG_LIGHT = colors.HexColor("#F8FAFC")    # Off-white
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Modify existing styles safely
    styles['Normal'].textColor = DARK_TEXT
    styles['Normal'].fontSize = 10
    styles['Normal'].leading = 14
    styles['Normal'].fontName = 'Helvetica'

    # Custom typography styles
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        leading=32,
        textColor=PRIMARY,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=13,
        leading=18,
        textColor=ACCENT,
        spaceAfter=25
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=17,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=18,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=ACCENT,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=DARK_TEXT,
        spaceAfter=8
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
        backColor=colors.HexColor("#F1F5F9"),
        borderColor=colors.HexColor("#CBD5E1"),
        borderWidth=0.5,
        borderPadding=6,
        spaceBefore=6,
        spaceAfter=8
    )

    callout_style = ParagraphStyle(
        'Callout_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=14,
        textColor=PRIMARY,
        backColor=colors.HexColor("#EFF6FF"),
        borderColor=ACCENT,
        borderWidth=1,
        borderPadding=8,
        spaceBefore=8,
        spaceAfter=10
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=DARK_TEXT
    )

    story = []

    # =========================================================================
    # COVER / HEADER TITLE
    # =========================================================================
    story.append(Spacer(1, 20))
    story.append(Paragraph("Intelligent GST Reconciliation Using Knowledge Graphs", title_style))
    story.append(Paragraph("Comprehensive Project Architecture, Machine Learning & Technical Report", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT, spaceAfter=20))

    # Meta Table
    meta_data = [
        [Paragraph("<b>Author / Engineer:</b>", table_cell_style), Paragraph("Karthikeya (Full-Stack & ML Engineer)", table_cell_style),
         Paragraph("<b>Date:</b>", table_cell_style), Paragraph("September 2026", table_cell_style)],
        [Paragraph("<b>Frontend Stack:</b>", table_cell_style), Paragraph("React 19 + Vite + Framer Motion", table_cell_style),
         Paragraph("<b>Backend Stack:</b>", table_cell_style), Paragraph("FastAPI + Python 3.11", table_cell_style)],
        [Paragraph("<b>Primary Database:</b>", table_cell_style), Paragraph("MongoDB Atlas (System of Record)", table_cell_style),
         Paragraph("<b>Graph Database:</b>", table_cell_style), Paragraph("Neo4j 5 Community / Enterprise", table_cell_style)],
        [Paragraph("<b>ML Engine:</b>", table_cell_style), Paragraph("RandomForestClassifier (300 trees)", table_cell_style),
         Paragraph("<b>Status:</b>", table_cell_style), Paragraph("Production Ready / Verified", table_cell_style)]
    ]
    t_meta = Table(meta_data, colWidths=[1.3*inch, 2.3*inch, 1.1*inch, 2.3*inch])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 20))

    # =========================================================================
    # 1. EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Problem Statement", h1_style))
    story.append(Paragraph(
        "India's Goods and Services Tax (GST) system requires businesses to rigorously reconcile invoices across "
        "multiple monthly returns (GSTR-1, GSTR-2B, GSTR-3B) before claiming <b>Input Tax Credit (ITC)</b>. "
        "Discrepancies lead to blocked credit worth crores of rupees, legal penalties under Section 73/74 of the CGST Act, "
        "and severe cash flow disruptions.", body_style
    ))

    story.append(Paragraph("Why Traditional SQL Systems Fail:", h2_style))
    story.append(Paragraph("• <b>Single-hop Table Limits:</b> Flat SQL table-matching verifies if an invoice exists in GSTR-1, but cannot traverse to the supplier's GSTR-3B return to confirm if tax was remitted.", bullet_style))
    story.append(Paragraph("• <b>Opaque Audit Trails:</b> Traditional software flags an invoice as 'Unmatched' without providing statutory evidence or legal citations required during tax audits.", bullet_style))
    story.append(Paragraph("• <b>Reactive Risk Management:</b> Audits happen months after filing when tax credits are already lost, rather than predicting vendor non-compliance risk proactively.", bullet_style))

    story.append(Paragraph(
        "<b>The GST ReconcileAI Solution:</b> This application models the complete GST supply chain as a <b>Knowledge Graph</b> (Neo4j), "
        "detects multi-hop discrepancies via Cypher graph traversal, predicts vendor risk using a <b>Random Forest classifier</b>, "
        "and generates <b>legally grounded explainable audit trails</b>.", callout_style
    ))

    # =========================================================================
    # 2. SYSTEM ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("2. System Architecture & Design", h1_style))
    story.append(Paragraph(
        "The application is built on a 4-tier modular architecture designed for high availability, sub-second query performance, "
        "and graceful degradation when underlying services are offline.", body_style
    ))

    arch_table_data = [
        [Paragraph("Layer", table_header_style), Paragraph("Technology Stack", table_header_style), Paragraph("Core Responsibilities", table_header_style)],
        [Paragraph("<b>Frontend</b>", table_cell_style), Paragraph("React 19, Vite, Framer Motion, Chart.js, react-force-graph-2d", table_cell_style), Paragraph("Single-page interactive UI, real-time KPI dashboards, interactive force graph, filterable reconciliation tables, audit cards.", table_cell_style)],
        [Paragraph("<b>State Layer</b>", table_cell_style), Paragraph("React Context API (DataContext, AuthContext, ThemeContext)", table_cell_style), Paragraph("Central state, live telemetry polling, API dispatching, client-side fallback graph projection when Neo4j is down.", table_cell_style)],
        [Paragraph("<b>Backend API</b>", table_cell_style), Paragraph("FastAPI, Python 3.11, PyMongo, Uvicorn", table_cell_style), Paragraph("High-performance async REST API, CORS middleware, MongoDB data access, model serving, auth security.", table_cell_style)],
        [Paragraph("<b>Database Layer</b>", table_cell_style), Paragraph("MongoDB Atlas (Primary) + Neo4j 5 (Knowledge Graph)", table_cell_style), Paragraph("MongoDB serves as system of record; Neo4j maintains graph projection of Vendors, Invoices, Returns, IRNs, e-Way Bills.", table_cell_style)],
        [Paragraph("<b>Machine Learning</b>", table_cell_style), Paragraph("Scikit-Learn RandomForestClassifier (300 trees)", table_cell_style), Paragraph("Predicts vendor compliance risk from 8 graph-derived features (held-out accuracy 76.8%, ROC-AUC 0.853).", table_cell_style)]
    ]
    t_arch = Table(arch_table_data, colWidths=[1.1*inch, 2.2*inch, 3.7*inch])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_arch)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 3. DATABASE SCHEMAS & ENTITY RELATIONSHIPS
    # =========================================================================
    story.append(Paragraph("3. Dual-Database Storage & Entity Schema", h1_style))
    story.append(Paragraph(
        "To combine document flexibility with graph traversal speed, the system uses a dual-database pattern:", body_style
    ))

    story.append(Paragraph("A. MongoDB Collections (System of Record)", h2_style))
    story.append(Paragraph("• <b>vendors:</b> Stores vendor profiles, state, risk score, transaction count, missed filings, average days late.", bullet_style))
    story.append(Paragraph("• <b>invoices:</b> Stores taxable amount, CGST/SGST/IGST breakdown, total tax, HSN code, filing period, status flags.", bullet_style))
    story.append(Paragraph("• <b>taxpayer:</b> Stores entity details for the buyer claiming credit (e.g., Quadric Manufacturing Pvt Ltd).", bullet_style))
    story.append(Paragraph("• <b>returns:</b> Stores per-vendor, per-period GSTR-3B filing records (tracks actual tax payment).", bullet_style))
    story.append(Paragraph("• <b>users & alerts:</b> User authentication accounts (bcrypt hashed) and real-time alert logs.", bullet_style))

    story.append(Paragraph("B. Neo4j Knowledge Graph Schema", h2_style))
    story.append(Paragraph(
        "Data from MongoDB is projected into Neo4j via <code>graph_sync.py</code> into 7 Node types and 8 Relationship types:", body_style
    ))

    schema_table_data = [
        [Paragraph("Entity (Node Label)", table_header_style), Paragraph("Properties Stored", table_header_style), Paragraph("Relationships (Edges)", table_header_style)],
        [Paragraph("<b>(:Taxpayer)</b>", table_cell_style), Paragraph("gstin, name, state, legal_name", table_cell_style), Paragraph("<code>-[:RECORDED_IN_PR]-> (:Invoice)</code><br/><code>-[:RECEIVES]-> (:GSTR {type:'GSTR-2B'})</code>", table_cell_style)],
        [Paragraph("<b>(:Vendor)</b>", table_cell_style), Paragraph("gstin, name, state, risk_score, status, pagerank", table_cell_style), Paragraph("<code>-[:ISSUED_INVOICE]-> (:Invoice)</code><br/><code>-[:FILED_RETURN]-> (:GSTR3B)</code>", table_cell_style)],
        [Paragraph("<b>(:Invoice)</b>", table_cell_style), Paragraph("id, taxable_amount, total_tax, hsn, period, match_status", table_cell_style), Paragraph("<code>-[:REPORTED_IN]-> (:GSTR)</code><br/><code>-[:ELECTRONIC_VERSION]-> (:EInvoice)</code><br/><code>-[:COVERS_SHIPMENT]-> (:EWayBill)</code>", table_cell_style)],
        [Paragraph("<b>(:GSTR)</b>", table_cell_style), Paragraph("type ('GSTR-1', 'GSTR-2B'), period", table_cell_style), Paragraph("Target of <code>:REPORTED_IN</code> from invoices.", table_cell_style)],
        [Paragraph("<b>(:GSTR3B)</b>", table_cell_style), Paragraph("gstin, period, filed (boolean), status", table_cell_style), Paragraph("Target of <code>:FILED_RETURN</code> from vendors.", table_cell_style)],
        [Paragraph("<b>(:EInvoice)</b>", table_cell_style), Paragraph("irn", table_cell_style), Paragraph("Target of <code>:ELECTRONIC_VERSION</code>.", table_cell_style)],
        [Paragraph("<b>(:EWayBill)</b>", table_cell_style), Paragraph("id", table_cell_style), Paragraph("Target of <code>:COVERS_SHIPMENT</code>.", table_cell_style)]
    ]
    t_schema = Table(schema_table_data, colWidths=[1.4*inch, 2.3*inch, 3.3*inch])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_schema)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 4. RECONCILIATION ENGINE & CYPHER QUERIES
    # =========================================================================
    story.append(Paragraph("4. Graph-Traversal Reconciliation Engine", h1_style))
    story.append(Paragraph(
        "The reconciliation engine (<code>reconcile.py</code>) executes Cypher graph traversals across 7 distinct mismatch classes. "
        "It distinguishes between <b>Structural Checks</b> (derived from absent graph edges) and <b>Field-Level Checks</b>:", body_style
    ))

    story.append(Paragraph("Key Cypher Reconciliation Patterns:", h2_style))
    
    code_text = (
        "// 1. Missing in GSTR-1 (Structural Check under s.16(2)(aa))\n"
        "MATCH (i:Invoice)-[:REPORTED_IN]->(g2:GSTR {type:'GSTR-2B'})\n"
        "WHERE NOT EXISTS {\n"
        "    MATCH (i)-[:REPORTED_IN]->(g1:GSTR {type:'GSTR-1'})\n"
        "    WHERE g1.period = g2.period\n"
        "}\n"
        "RETURN i.id AS invoice_id, i.total_tax AS tax;\n\n"
        "// 2. Multi-Hop Tax Payment Chain (Unpaid Tax under s.16(2)(c))\n"
        "MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice)-[:REPORTED_IN]->(:GSTR {type:'GSTR-1'})\n"
        "MATCH (v)-[:FILED_RETURN]->(g3:GSTR3B {period: i.period})\n"
        "WHERE g3.filed = false\n"
        "RETURN i.id AS invoice_id, v.name AS vendor_name, g3.status AS status;"
    )
    story.append(Paragraph(code_text.replace("\n", "<br/>").replace(" ", "&nbsp;"), code_style))

    # =========================================================================
    # 5. PREDICTIVE VENDOR RISK MODEL (ML)
    # =========================================================================
    story.append(Paragraph("5. Predictive Vendor Compliance ML Model", h1_style))
    story.append(Paragraph(
        "To move from reactive audits to proactive risk prevention, the system includes a <b>Random Forest Classifier</b> "
        "(300 trees, depth 8, balanced class weights) served directly via FastAPI (<code>risk_model.py</code>).", body_style
    ))

    story.append(Paragraph("8 Graph-Derived Feature Dimensions:", h2_style))
    ml_features = [
        [Paragraph("Feature Name", table_header_style), Paragraph("Description & Extraction Source", table_header_style)],
        [Paragraph("<code>mismatch_count</code>", table_cell_style), Paragraph("Count of past mismatched invoices issued by vendor.", table_cell_style)],
        [Paragraph("<code>total_tax_at_risk</code>", table_cell_style), Paragraph("Total monetary tax value in disputed invoices (INR).", table_cell_style)],
        [Paragraph("<code>filing_delay_days</code>", table_cell_style), Paragraph("Average delay in days for return submissions.", table_cell_style)],
        [Paragraph("<code>graph_centrality</code>", table_cell_style), Paragraph("PageRank degree centrality score in the supply graph.", table_cell_style)],
        [Paragraph("<code>transaction_volume</code>", table_cell_style), Paragraph("Total transaction history volume.", table_cell_style)],
        [Paragraph("<code>community_cluster</code>", table_cell_style), Paragraph("Network community detection ID / State cluster.", table_cell_style)],
        [Paragraph("<code>einvoice_compliance_rate</code>", table_cell_style), Paragraph("Proportion of vendor invoices carrying valid IRN.", table_cell_style)],
        [Paragraph("<code>state_risk_factor</code>", table_cell_style), Paragraph("Historical state-level prior compliance risk score.", table_cell_style)]
    ]
    t_ml = Table(ml_features, colWidths=[2.2*inch, 4.8*inch])
    t_ml.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('PADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_ml)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Avoiding the Bayes Error Trap:</b> Synthetic training data uses a <b>stochastic logistic process</b> with Bernoulli sampling "
        "rather than a deterministic threshold. This introduces realistic noise, producing calibrated metrics: "
        "<b>Held-out Accuracy: 76.8%</b>, <b>ROC-AUC: 0.853</b>, <b>5-Fold CV: 76.8%</b>.", callout_style
    ))

    # =========================================================================
    # 6. EXPLAINABLE AUDIT TRAILS & STATUTORY CITATIONS
    # =========================================================================
    story.append(Paragraph("6. Explainable Audit Trail Engine", h1_style))
    story.append(Paragraph(
        "Audit trails (<code>audit_trail.py</code>) are built from live graph facts rather than static hand-written text strings. "
        "Every audit card maps to statutory provisions under Indian Tax Law:", body_style
    ))

    statute_table_data = [
        [Paragraph("Mismatch Category", table_header_style), Paragraph("CGST Act Provision", table_header_style), Paragraph("Statutory Legal Explanation & Action Plan", table_header_style)],
        [Paragraph("<b>Missing in GSTR-1</b>", table_cell_style), Paragraph("Section 16(2)(aa)", table_cell_style), Paragraph("ITC restricted unless invoice is reported by supplier in GSTR-1 and appears in GSTR-2B. Withhold credit and request Table 9A amendment.", table_cell_style)],
        [Paragraph("<b>GSTR-3B Not Filed</b>", table_cell_style), Paragraph("Section 16(2)(c)", table_cell_style), Paragraph("Credit is illegal unless tax collected by supplier was actually remitted to government. Do not utilize credit until return is filed.", table_cell_style)],
        [Paragraph("<b>Not in Purchase Reg.</b>", table_cell_style), Paragraph("Section 35(1)", table_cell_style), Paragraph("Requirement to maintain true/correct books of accounts. Confirm goods receipt to guard against fake invoice scams.", table_cell_style)],
        [Paragraph("<b>E-Way Bill Missing</b>", table_cell_style), Paragraph("Rule 138", table_cell_style), Paragraph("Consignments above ₹50,000 require proof of physical movement via an e-Way Bill.", table_cell_style)],
        [Paragraph("<b>e-Invoice Missing</b>", table_cell_style), Paragraph("Rule 48(4)", table_cell_style), Paragraph("Notified suppliers must issue IRN. Invoice lacking IRN is not a valid tax invoice.", table_cell_style)]
    ]
    t_statute = Table(statute_table_data, colWidths=[1.5*inch, 1.5*inch, 4.0*inch])
    t_statute.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_statute)
    story.append(Spacer(1, 10))

    # =========================================================================
    # 7. SUBSYSTEM RESILIENCE & API ENDPOINTS
    # =========================================================================
    story.append(Paragraph("7. Subsystem Resilience & API Endpoints", h1_style))
    story.append(Paragraph(
        "The system degrades gracefully across all layers if any component is offline:", body_style
    ))

    resilience_data = [
        [Paragraph("Subsystem", table_header_style), Paragraph("Primary Provider", table_header_style), Paragraph("Fallback Mechanism", table_header_style), Paragraph("User Impact", table_header_style)],
        [Paragraph("<b>Database</b>", table_cell_style), Paragraph("MongoDB Atlas", table_cell_style), Paragraph("Bundled mock dataset (mockData.js)", table_cell_style), Paragraph("Zero downtime; offline banner displayed.", table_cell_style)],
        [Paragraph("<b>Knowledge Graph</b>", table_cell_style), Paragraph("Neo4j 5 Server", table_cell_style), Paragraph("Client-side graph projection (DataContext)", table_cell_style), Paragraph("Force graph still renders; engine reports 'client'.", table_cell_style)],
        [Paragraph("<b>Risk AI Model</b>", table_cell_style), Paragraph("RandomForest PKL", table_cell_style), Paragraph("Weighted-sum heuristic algorithm", table_cell_style), Paragraph("Risk scores continue generating smoothly.", table_cell_style)]
    ]
    t_res = Table(resilience_data, colWidths=[1.2*inch, 1.6*inch, 2.2*inch, 2.0*inch])
    t_res.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), PRIMARY),
        ('PADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT])
    ]))
    story.append(t_res)
    story.append(Spacer(1, 10))

    story.append(Paragraph("Core REST API Endpoints Summary:", h2_style))
    story.append(Paragraph("• <code>GET /api/vendors</code> & <code>POST /api/vendors</code> — Vendor CRUD with real-time ML risk prediction.", bullet_style))
    story.append(Paragraph("• <code>GET /api/invoices</code> & <code>POST /api/invoices</code> — Invoice CRUD with auto mismatch classification.", bullet_style))
    story.append(Paragraph("• <code>POST /api/predict-risk</code> — Scores vendor feature vectors using the Random Forest model.", bullet_style))
    story.append(Paragraph("• <code>GET /api/reconcile</code> — Runs graph-traversal reconciliation across specified filing periods.", bullet_style))
    story.append(Paragraph("• <code>GET /api/audit-trail/{id}</code> — Generates legally grounded explainable audit reports from graph facts.", bullet_style))
    story.append(Paragraph("• <code>POST /api/graph/sync</code> — Projects MongoDB collections into Neo4j nodes and edges.", bullet_style))

    story.append(Spacer(1, 15))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=15))
    story.append(Paragraph("<b>Report Summary:</b> This technical report documents the complete architectural, database, machine learning, and legal design of GST ReconcileAI. All systems have been verified operational.", body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"PDF successfully generated: {target_path}")

if __name__ == "__main__":
    create_pdf()

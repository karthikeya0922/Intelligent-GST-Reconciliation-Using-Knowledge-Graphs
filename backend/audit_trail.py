"""
Explainable audit trail generator.

Produces a natural-language explanation for any flagged invoice, grounded in
facts read out of the knowledge graph rather than written by hand. Every
sentence is derived from something the graph actually asserts - a present or
absent relationship, a node property - so the explanation cannot drift from the
data the way a stored blob of prose does.

The output is deliberately structured the way an auditor reads a case:

    summary        what is wrong, in one sentence, with the amount at stake
    evidence       the specific graph facts, each traceable to an edge or node
    graph_path     the traversal that produced the finding
    statute        the CGST Act provision that applies
    recommendation what the taxpayer should actually do
    severity       financial-risk banding, so a queue can be prioritised

`explain.py` holds the optional LLM variant (LangChain + GraphRAG over the same
graph). This module is the deterministic one: no API key, no network call, and
its claims are checkable against the graph.
"""


def _inr(amount):
    """Format a number in the Indian numbering system."""
    try:
        amount = float(amount or 0)
    except (TypeError, ValueError):
        return "₹0"
    whole = int(round(amount))
    s = str(abs(whole))
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return f"₹{'-' if whole < 0 else ''}{s}"


# Each mismatch type maps to the statutory hook an auditor would cite, plus the
# action that actually resolves it.
ISSUE_PLAYBOOK = {
    "Missing in GSTR-1": {
        "statute": "Section 16(2)(aa), CGST Act 2017",
        "statute_text": (
            "ITC may be availed only if the supplier has furnished the invoice in "
            "their GSTR-1 and it appears in the recipient's GSTR-2B."
        ),
        "action": (
            "Withhold the credit and require the supplier to report this invoice in "
            "an amended GSTR-1 (Table 9A). Recover the tax from the supplier under "
            "the indemnity clause if they do not."
        ),
    },
    "Supplier GSTR-3B Not Filed": {
        "statute": "Section 16(2)(c), CGST Act 2017",
        "statute_text": (
            "ITC is available only where the tax charged has actually been paid to "
            "the government by the supplier, in cash or through utilisation of ITC."
        ),
        "action": (
            "The invoice is reported but the tax was never remitted. Do not utilise "
            "this credit. Escalate to the supplier for immediate GSTR-3B filing and "
            "hold further payments until the return is filed."
        ),
    },
    "Missing in Purchase Register": {
        "statute": "Section 35(1), CGST Act 2017",
        "statute_text": (
            "Every registered person shall keep a true and correct account of all "
            "goods and services received."
        ),
        "action": (
            "The supplier has declared a supply the books do not record. Confirm "
            "whether goods or services were actually received. If not, this may be "
            "an invoice raised fraudulently against your GSTIN — report it to the "
            "supplier and your jurisdictional officer."
        ),
    },
    "In Purchase Register, Missing in GSTR-2B": {
        "statute": "Section 16(2)(aa), CGST Act 2017",
        "statute_text": (
            "ITC may be availed only on invoices communicated to the recipient in "
            "GSTR-2B."
        ),
        "action": (
            "The purchase is booked but no credit is available. Reverse any ITC "
            "provisionally taken and pursue the supplier to report the invoice."
        ),
    },
    "Tax Amount Mismatch": {
        "statute": "Section 16(2)(a), CGST Act 2017",
        "statute_text": "ITC is restricted to the tax actually charged on a valid tax invoice.",
        "action": (
            "Claim only the lower of the two figures until reconciled. Ask the "
            "supplier to issue a debit or credit note under Section 34."
        ),
    },
    "HSN Mismatch": {
        "statute": "Notification 78/2020 – Central Tax",
        "statute_text": "HSN reporting at the prescribed digit level is mandatory.",
        "action": (
            "Classification differs between the filings, which changes the applicable "
            "rate. Confirm the correct HSN with the supplier and have the return amended."
        ),
    },
    "E-Way Bill Missing": {
        "statute": "Rule 138, CGST Rules 2017",
        "statute_text": (
            "An e-Way Bill is mandatory for movement of goods where the consignment "
            "value exceeds ₹50,000."
        ),
        "action": (
            "Obtain the e-Way Bill from the supplier. Without proof of movement the "
            "supply itself can be questioned during assessment."
        ),
    },
    "e-Invoice Missing": {
        "statute": "Rule 48(4), CGST Rules 2017",
        "statute_text": (
            "A notified registered person must issue an invoice carrying an IRN "
            "obtained from the Invoice Registration Portal. An invoice without a "
            "valid IRN is not a valid tax invoice."
        ),
        "action": (
            "Ask the supplier for the IRN. If the supplier is covered by e-invoicing "
            "and did not generate one, ITC on this invoice is not available."
        ),
    },
    "Late Filing": {
        "statute": "Section 16(4), CGST Act 2017",
        "statute_text": (
            "ITC cannot be availed after 30 November following the end of the "
            "financial year to which the invoice relates."
        ),
        "action": "Confirm the claim falls inside the Section 16(4) window before availing.",
    },
}

DEFAULT_PLAYBOOK = {
    "statute": "Section 16, CGST Act 2017",
    "statute_text": "Conditions and eligibility for taking input tax credit.",
    "action": "Reconcile with the supplier before availing the credit.",
}


# How serious each issue is on its own, before money is considered. An invoice
# the supplier never paid tax on outranks a late filing regardless of amount, so
# the headline and the statute cited must come from the worst finding rather than
# from whichever label happened to be stored on the record.
ISSUE_GRAVITY = {
    "Supplier GSTR-3B Not Filed": 100,
    "Missing in GSTR-1": 90,
    "Missing in Purchase Register": 85,
    "In Purchase Register, Missing in GSTR-2B": 80,
    "Missing in GSTR-2B": 80,
    "Tax Amount Mismatch": 60,
    "e-Invoice Missing": 55,
    "HSN Mismatch": 45,
    "E-Way Bill Missing": 40,
    "Late Filing": 30,
}

_SEVERITY_RANK = {"Low": 0, "Medium": 1, "High": 2}


def rank_issues(issues):
    """Order findings worst-first so the headline reports the real problem."""
    return sorted(issues, key=lambda i: -ISSUE_GRAVITY.get(i, 50))


def severity_for(tax, issue_type):
    """Band one finding by money at stake, escalating the fraud-shaped issues."""
    tax = float(tax or 0)
    if issue_type in (
        "Supplier GSTR-3B Not Filed",
        "Missing in Purchase Register",
        "Missing in GSTR-1",
    ):
        return "High" if tax > 25000 else "Medium"
    if tax > 100000:
        return "High"
    if tax > 25000:
        return "Medium"
    return "Low"


def overall_severity(tax, issues):
    """Worst severity across every finding on the invoice."""
    if not issues:
        return severity_for(tax, None)
    worst = max(issues, key=lambda i: _SEVERITY_RANK[severity_for(tax, i)])
    return severity_for(tax, worst)


def build_audit_trail(facts):
    """Turn graph facts about one invoice into a structured audit trail.

    `facts` is what ReconciliationEngine.get_evidence_path returns, enriched by
    the caller with the invoice's issue list.
    """
    invoice_id = facts.get("invoice_id") or facts.get("id") or "this invoice"
    vendor = facts.get("vendor") or "the supplier"
    gstin = facts.get("gstin") or "unknown GSTIN"
    taxable = facts.get("amount") or 0
    tax = facts.get("tax") or 0
    period = facts.get("period") or "the period"
    filings = facts.get("filings") or []
    # Worst-first, so the summary, statute and action all describe the most
    # serious finding rather than whichever label happened to be stored.
    issues = rank_issues(facts.get("issues") or [])
    primary = issues[0] if issues else (facts.get("status") or "Unmatched")

    play = ISSUE_PLAYBOOK.get(primary, DEFAULT_PLAYBOOK)

    # ---- Summary -----------------------------------------------------------
    summary = (
        f"Invoice {invoice_id} from {vendor} ({gstin}), taxable value "
        f"{_inr(taxable)} with {_inr(tax)} of tax, is flagged for period {period}: "
        f"{primary}."
    )
    if len(issues) > 1:
        summary += (
            f" {len(issues) - 1} further issue(s) were also found: "
            + ", ".join(issues[1:]) + "."
        )

    # ---- Evidence, each line tied to a graph fact ---------------------------
    evidence = []

    if "GSTR-1" in filings:
        evidence.append(f"Invoice reaches GSTR-1 for {period} via :REPORTED_IN — the supplier declared it.")
    else:
        evidence.append(
            f"No :REPORTED_IN edge from {invoice_id} to GSTR-1 for {period} — "
            f"the supplier never declared this invoice."
        )

    if "GSTR-2B" in filings:
        evidence.append(f"Invoice appears in the recipient's GSTR-2B for {period}.")
    else:
        evidence.append(f"Invoice is absent from GSTR-2B for {period} — no credit was communicated.")

    if facts.get("gstr3b_filed") is False:
        evidence.append(
            f"{vendor} has NOT filed GSTR-3B for {period} — tax on this invoice was "
            f"reported but never remitted to the government."
        )
    elif facts.get("gstr3b_filed") is True:
        evidence.append(f"{vendor} filed GSTR-3B for {period}; the tax was remitted.")

    if facts.get("in_purchase_register") is False:
        evidence.append(
            "No :RECORDED_IN_PR edge from the taxpayer — this purchase is not in the buyer's books."
        )
    elif facts.get("in_purchase_register") is True:
        evidence.append("Purchase is recorded in the taxpayer's Purchase Register.")

    einvoices = facts.get("einvoices") or 0
    evidence.append(
        f"e-Invoice IRN linked via :ELECTRONIC_VERSION." if einvoices
        else "No :ELECTRONIC_VERSION edge — no e-Invoice IRN was generated."
    )

    ewaybills = facts.get("ewaybills") or 0
    if ewaybills:
        evidence.append("e-Way Bill linked via :COVERS_SHIPMENT.")
    elif float(taxable or 0) > 50000:
        evidence.append(
            f"No :COVERS_SHIPMENT edge to an e-Way Bill, though the consignment value "
            f"{_inr(taxable)} exceeds the ₹50,000 threshold in Rule 138."
        )

    risk = facts.get("vendor_risk")
    if risk is not None:
        evidence.append(f"Supplier compliance risk score: {float(risk) * 100:.0f}%.")

    if len(issues) > 1:
        evidence.append("All findings on this invoice: " + "; ".join(issues) + ".")

    # ---- Recommendation ----------------------------------------------------
    recommendation = (
        f"{_inr(tax)} of input tax credit is at risk on this invoice. {play['action']}"
    )

    return {
        "invoice_id": invoice_id,
        "summary": summary,
        "evidence": evidence,
        "graph_path": facts.get("graph_path"),
        "statute": play["statute"],
        "statute_text": play["statute_text"],
        "recommendation": recommendation,
        "severity": overall_severity(tax, issues),
        "tax_at_risk": tax,
        "issues": issues,
        "generated_from": facts.get("source", "graph"),
    }

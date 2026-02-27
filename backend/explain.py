"""
Explainable Audit Trail Generator
Uses LangChain + Neo4j GraphRAG to generate natural-language explanations
grounded in Knowledge Graph facts.
"""

from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
import os


class AuditTrailGenerator:
    """LLM-powered audit trail generator using Knowledge Graph"""
    
    def __init__(self, neo4j_uri="bolt://localhost:7687", neo4j_user="neo4j", 
                 neo4j_password="password", openai_api_key=None):
        
        self.graph = Neo4jGraph(
            url=neo4j_uri,
            username=neo4j_user,
            password=neo4j_password
        )
        
        self.llm = OpenAI(
            model_name="gpt-4",
            temperature=0,
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Custom prompt for GST-specific explanations
        self.cypher_prompt = PromptTemplate(
            input_variables=["question", "schema"],
            template="""You are a GST compliance expert with access to a Neo4j Knowledge Graph.
            
Graph Schema:
{schema}

Generate a Cypher query to answer this GST-related question:
{question}

Focus on retrieving:
1. Invoice details (amount, date, HSN code)
2. Vendor information (GSTIN, name, compliance history)
3. Filing status (which GSTR returns contains this invoice)
4. Match status (is it reconciled between GSTR-1 and GSTR-2B?)

Return ONLY the Cypher query, no explanation."""
        )
        
        self.explanation_prompt = PromptTemplate(
            input_variables=["question", "context"],
            template="""You are a GST compliance auditor. Based on the following data from the 
Knowledge Graph, provide a clear, factual audit explanation.

Question: {question}

Knowledge Graph Data:
{context}

Provide:
1. A clear summary of why this invoice is flagged
2. Specific evidence from the graph data
3. The relevant CGST Act section
4. A recommendation for the taxpayer

Use professional but readable language. Cite specific amounts in INR."""
        )
        
        # Build the chain
        self.chain = GraphCypherQAChain.from_llm(
            self.llm,
            graph=self.graph,
            cypher_prompt=self.cypher_prompt,
            qa_prompt=self.explanation_prompt,
            verbose=True,
            top_k=10,
        )
    
    def explain_invoice(self, invoice_id):
        """Generate an explanation for why a specific invoice is flagged"""
        question = f"Why is invoice {invoice_id} flagged for ITC risk? Show all related entities."
        answer = self.chain.run(question)
        return {
            "invoice_id": invoice_id,
            "explanation": answer,
            "source": "LangChain + Neo4j GraphRAG",
            "model": "GPT-4"
        }
    
    def explain_vendor_risk(self, vendor_gstin):
        """Generate explanation for a vendor's risk score"""
        question = f"""What is the compliance history of vendor with GSTIN {vendor_gstin}? 
        Show their filing patterns, mismatch history, and connection to other entities."""
        answer = self.chain.run(question)
        return {
            "vendor_gstin": vendor_gstin,
            "explanation": answer,
            "source": "LangChain + Neo4j GraphRAG"
        }
    
    def explain_itc_claim(self, period):
        """Explain ITC risk for a specific period"""
        question = f"""Summarize the ITC risk for period {period}. 
        How many invoices are unmatched? What is the total tax at risk? 
        Which vendors are the biggest contributors?"""
        answer = self.chain.run(question)
        return {
            "period": period,
            "explanation": answer,
            "source": "LangChain + Neo4j GraphRAG"
        }
    
    def get_graph_context(self, invoice_id):
        """Fetch raw graph context for an invoice (for manual review)"""
        with self.graph._driver.session() as session:
            result = session.run("""
                MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice {id: $invoice_id})
                OPTIONAL MATCH (i)-[:REPORTED_IN]->(g:GSTR)
                OPTIONAL MATCH (i)-[:ELECTRONIC_VERSION]->(e:EInvoice)
                OPTIONAL MATCH (i)-[:COVERS_SHIPMENT]->(w:EWayBill)
                RETURN v, i, collect(DISTINCT g) AS returns, 
                       collect(DISTINCT e) AS einvoices,
                       collect(DISTINCT w) AS ewaybills
            """, invoice_id=invoice_id)
            return result.data()


# Simpler alternative using direct Cypher + LLM
class SimpleAuditTrail:
    """Simplified audit trail without LangChain dependency"""
    
    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
    
    def generate_explanation(self, invoice_id):
        """Generate explanation using template"""
        with self.driver.session() as session:
            data = session.run("""
                MATCH (v:Vendor)-[:ISSUED_INVOICE]->(i:Invoice {id: $inv_id})
                OPTIONAL MATCH (i)-[:REPORTED_IN]->(g:GSTR)
                RETURN v.name AS vendor, v.gstin AS gstin,
                       i.taxable_amount AS amount, i.match_status AS status,
                       collect(g.type + ' (' + g.period + ')') AS filings
            """, inv_id=invoice_id).single()
        
        if not data:
            return f"No data found for invoice {invoice_id}"
        
        filings = data['filings']
        has_gstr1 = any('GSTR-1' in f for f in filings)
        has_gstr2b = any('GSTR-2B' in f for f in filings)
        
        explanation = f"Invoice {invoice_id} (₹{data['amount']:,.0f}) from {data['vendor']} "
        explanation += f"(GSTIN: {data['gstin']}) "
        
        if has_gstr2b and not has_gstr1:
            explanation += "appears in GSTR-2B but is MISSING from the vendor's GSTR-1 filing. "
            explanation += "ITC cannot be claimed under Section 16(2)(aa) CGST Act until the vendor reports this invoice."
        elif data['status'] == 'Tax Amount Mismatch':
            explanation += "shows conflicting tax amounts between GSTR-1 and GSTR-2B. "
            explanation += "The correct amount must be reconciled before claiming ITC."
        else:
            explanation += f"status: {data['status']}. "
        
        return explanation


if __name__ == "__main__":
    # Example usage (requires running Neo4j and OpenAI API key)
    print("Audit Trail Generator ready.")
    print("Usage: AuditTrailGenerator().explain_invoice('INV-2025-001')")


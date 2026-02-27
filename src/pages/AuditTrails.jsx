import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Sparkles, FileText, ArrowRight, AlertTriangle, Info, Bot } from 'lucide-react';
import { useData } from '../context/DataContext';

function formatINR(num) {
    return '₹' + num.toLocaleString('en-IN');
}

function TypingEffect({ text, speed = 12 }) {
    const [displayed, setDisplayed] = useState('');
    const [done, setDone] = useState(false);

    useEffect(() => {
        setDisplayed('');
        setDone(false);
        let i = 0;
        const interval = setInterval(() => {
            if (i < text.length) {
                setDisplayed(text.substring(0, i + 1));
                i++;
            } else {
                clearInterval(interval);
                setDone(true);
            }
        }, speed);
        return () => clearInterval(interval);
    }, [text, speed]);

    return (
        <span>
            {displayed}
            {!done && <span className="typing-cursor" style={{ borderRight: '2px solid var(--accent-primary)', animation: 'blink 0.7s step-end infinite', paddingLeft: '1px' }}>
                <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }`}</style>
            </span>}
        </span>
    );
}

export default function AuditTrails() {
    const { mismatches, auditExplanations } = useData();
    const [selectedInvoice, setSelectedInvoice] = useState(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [showExplanation, setShowExplanation] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');

    const flaggedInvoices = mismatches.filter(m =>
        auditExplanations[m.id] &&
        (searchTerm === '' || m.id.toLowerCase().includes(searchTerm.toLowerCase()) || m.vendorName.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    const handleGenerate = (invoice) => {
        setSelectedInvoice(invoice);
        setShowExplanation(false);
        setIsGenerating(true);

        // Simulate LLM processing
        setTimeout(() => {
            setIsGenerating(false);
            setShowExplanation(true);
        }, 1800);
    };

    const explanation = selectedInvoice ? auditExplanations[selectedInvoice.id] : null;

    return (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.4 }}>
            <div className="page-header">
                <h2>🤖 Explainable Audit Trail Generator</h2>
                <p>LLM-powered natural language explanations via GraphRAG — Deliverable 4</p>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '20px', alignItems: 'start' }}>
                {/* Left: Invoice Select */}
                <div className="card" style={{ position: 'sticky', top: '24px' }}>
                    <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <FileText size={16} />
                        Flagged Invoices
                    </h3>
                    <div style={{ position: 'relative', marginBottom: '12px' }}>
                        <Search size={14} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                            className="filter-input"
                            style={{ paddingLeft: '30px', width: '100%', fontSize: '0.8rem' }}
                            placeholder="Search..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '480px', overflowY: 'auto' }}>
                        {flaggedInvoices.map(inv => (
                            <div
                                key={inv.id}
                                onClick={() => handleGenerate(inv)}
                                style={{
                                    padding: '12px 14px',
                                    borderRadius: 'var(--radius-sm)',
                                    cursor: 'pointer',
                                    border: `1px solid ${selectedInvoice?.id === inv.id ? 'var(--accent-primary)' : 'var(--border-primary)'}`,
                                    background: selectedInvoice?.id === inv.id ? 'var(--accent-glow)' : 'transparent',
                                    transition: 'all 0.2s ease',
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span className="mono" style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-primary)' }}>{inv.id}</span>
                                    <span className={`badge ${inv.riskLevel.toLowerCase()}`}>{inv.riskLevel}</span>
                                </div>
                                <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{inv.vendorName}</div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '4px', fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                                    <span>{inv.matchStatus}</span>
                                    <span className="amount">{formatINR(inv.totalTax)}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right: Explanation Panel */}
                <div>
                    {!selectedInvoice && (
                        <div className="card" style={{ textAlign: 'center', padding: '60px 40px' }}>
                            <Bot size={48} style={{ color: 'var(--text-muted)', margin: '0 auto 16px' }} />
                            <h3 style={{ color: 'var(--text-secondary)', marginBottom: '8px' }}>Select a flagged invoice</h3>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                                Click on any flagged invoice to generate an AI-powered audit explanation using LangChain + Neo4j GraphRAG
                            </p>
                        </div>
                    )}

                    {isGenerating && (
                        <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
                            <div style={{ marginBottom: '16px' }}>
                                <Sparkles size={24} style={{ color: 'var(--accent-primary)', animation: 'pulse 1s ease-in-out infinite' }} />
                            </div>
                            <h3 style={{ marginBottom: '12px' }}>Generating Audit Trail...</h3>
                            <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginBottom: '16px' }}>
                                Querying Knowledge Graph → Running Cypher traversal → LLM synthesis
                            </p>
                            <div className="typing-indicator" style={{ justifyContent: 'center' }}>
                                <span className="typing-dot"></span>
                                <span className="typing-dot"></span>
                                <span className="typing-dot"></span>
                            </div>
                        </div>
                    )}

                    <AnimatePresence>
                        {showExplanation && explanation && (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5 }}
                            >
                                {/* LLM Pipeline Info */}
                                <div className="card mb-2" style={{ padding: '14px 20px' }}>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '0.78rem', color: 'var(--text-secondary)', flexWrap: 'wrap' }}>
                                        <span className="badge info">LangChain</span>
                                        <ArrowRight size={12} />
                                        <span className="badge" style={{ background: 'rgba(34,197,94,0.1)', color: '#22c55e', border: '1px solid rgba(34,197,94,0.2)' }}>Neo4j Cypher</span>
                                        <ArrowRight size={12} />
                                        <span className="badge" style={{ background: 'rgba(139,92,246,0.1)', color: '#8b5cf6', border: '1px solid rgba(139,92,246,0.2)' }}>GPT-4 Synthesis</span>
                                        <ArrowRight size={12} />
                                        <span className="badge success">Explanation Ready</span>
                                    </div>
                                </div>

                                {/* Main Explanation */}
                                <div className="audit-bubble">
                                    <div className="audit-summary">
                                        <TypingEffect text={explanation.summary} speed={8} />
                                    </div>

                                    <h4 style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <Info size={14} /> Evidence from Knowledge Graph
                                    </h4>
                                    <ul className="audit-evidence">
                                        {explanation.evidence.map((ev, idx) => (
                                            <li key={idx}>{ev}</li>
                                        ))}
                                    </ul>

                                    <h4 style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <AlertTriangle size={14} /> Recommendation
                                    </h4>
                                    <div className="audit-recommendation">
                                        {explanation.recommendation}
                                    </div>

                                    <h4 style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '8px' }}>Graph Traversal Path</h4>
                                    <div className="audit-graph-path">
                                        {explanation.graphPath}
                                    </div>
                                </div>


                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    );
}

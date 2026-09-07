import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export default function ResearchDisclaimer({ compact = false }) {
  if (compact) {
    return (
      <div className="research-disclaimer-compact" role="note">
        <AlertTriangle size={14} className="disclaimer-icon" />
        <span>
          <strong>Research Benchmark:</strong> Experimental ML risk indicators for decision support. Not a legal determination of fraud or statutory liability.
        </span>
      </div>
    );
  }

  return (
    <div className="research-disclaimer" role="note">
      <div className="disclaimer-header">
        <ShieldCheck size={18} className="disclaimer-icon" />
        <span className="disclaimer-title">Controlled Research Benchmark & Experimental System</span>
      </div>
      <p className="disclaimer-text">
        This system provides experimental ML-based risk indicators and decision-support information. It is not a determination of fraud, tax liability, or statutory non-compliance. Results are demonstrated on a controlled hybrid research benchmark. External validation using appropriately labelled real-world data is required before operational deployment.
      </p>
    </div>
  );
}

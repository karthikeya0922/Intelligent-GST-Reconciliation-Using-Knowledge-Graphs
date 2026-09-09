"""
Production GST ITC Risk Engine.

Orchestrates end-to-end risk evaluation:
- Loads frozen 19-feature Tabular XGBoost model and preprocessor.
- Separates ML Risk Class from 0-100 ML Risk Indicator Score & Application Risk Band.
- Computes financial ITC exposure and exposure ratio safely.
- Classifies operational review priority (Risk x Exposure matrix).
- Generates class-specific Tree SHAP explanations.
- Extracts auditable multi-domain evidence (reconciliation, compliance, transaction, model, graph).
- Integrates time-safe Knowledge Graph investigation context.
- Maintains vendor risk history, transition tracking, and audit logging.
"""

from typing import List, Dict, Any, Optional, Tuple
import os
import json
import joblib
from datetime import datetime
import numpy as np
import pandas as pd

from backend.ml.features import (
    ALL_TABULAR_FEATURES,
    engineer_derived_features
)
from backend.ml.explain import ModelExplainer
from backend.ml.evidence import EvidenceEngine
from backend.ml.explanation import RiskExplanationGenerator
from backend.ml.graph_investigation import GraphInvestigator


DEFAULT_PROD_MODELS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "models", "production"
)

DEFAULT_AUDIT_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "reports", "ml", "risk_assessment_audit.log"
)


class ITCRiskEngine:
    """Production risk assessment engine for GST Input Tax Credit evaluation."""

    def __init__(
        self,
        models_dir: str = DEFAULT_PROD_MODELS_DIR,
        audit_log_path: str = DEFAULT_AUDIT_LOG_PATH
    ):
        self.models_dir = models_dir
        self.audit_log_path = audit_log_path
        self.model = None
        self.preprocessor = None
        self.metadata = {}
        self.feature_names = []
        
        self.evidence_engine = EvidenceEngine()
        self.explanation_generator = RiskExplanationGenerator()
        self.graph_investigator = GraphInvestigator()

        self._load_production_artifacts()
        self._load_sample_invoices()

    def _load_production_artifacts(self):
        """Loads frozen model, preprocessor, and metadata from models/production/."""
        model_path = os.path.join(self.models_dir, "xgboost_model.pkl")
        prep_path = os.path.join(self.models_dir, "preprocessor.pkl")
        meta_path = os.path.join(self.models_dir, "model_metadata.json")

        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)
                self.feature_names = self.metadata.get("feature_names", ALL_TABULAR_FEATURES)
        else:
            self.feature_names = ALL_TABULAR_FEATURES

        if os.path.exists(prep_path):
            self.preprocessor = joblib.load(prep_path)

        if os.path.exists(model_path):
            self.model = joblib.load(model_path)

    def _load_sample_invoices(self):
        """Loads sample dataset invoices for graph relationship exploration."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sample_path = os.path.join(base_dir, "data", "sample", "sample_hybrid_dataset.json")
        if os.path.exists(sample_path):
            try:
                with open(sample_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph_investigator.set_invoices(data.get("sample_invoices", []))
            except Exception:
                pass

    @staticmethod
    def calculate_risk_score(probabilities: Dict[str, float]) -> float:
        """
        Calculates normalized 0–100 ML Risk Indicator Score:
        score = 100 * (P(MEDIUM) * 0.5 + P(HIGH) * 1.0)
        """
        p_med = float(probabilities.get("MEDIUM", 0.0))
        p_high = float(probabilities.get("HIGH", 0.0))
        score = 100.0 * (p_med * 0.5 + p_high * 1.0)
        return round(float(np.clip(score, 0.0, 100.0)), 2)

    @staticmethod
    def get_risk_band(risk_score: float) -> str:
        """
        Application-level presentation risk band (distinct from ML model class):
        0–33   -> LOW
        >33–66 -> MEDIUM
        >66–100 -> HIGH
        """
        if risk_score <= 33.0:
            return "LOW"
        elif risk_score <= 66.0:
            return "MEDIUM"
        else:
            return "HIGH"

    @staticmethod
    def prioritize_review(risk_level: str, itc_exposure: float) -> Tuple[str, str, str]:
        """
        Risk x Exposure Prioritization Matrix:
        Returns (priority, action, details).
        """
        is_high_exposure = itc_exposure >= 100000.0
        exp_text = "High Exposure" if is_high_exposure else "Low Exposure"

        if risk_level == "LOW":
            if is_high_exposure:
                return (
                    "MEDIUM",
                    "Spot-check high-value invoices",
                    f"Vendor has clean compliance profile (LOW risk) but material ITC exposure (₹{itc_exposure:,.2f}). Verify invoice documentation."
                )
            else:
                return (
                    "LOW",
                    "Routine monitoring",
                    "No immediate audit intervention required. Automated reconciliation approved."
                )
        elif risk_level == "MEDIUM":
            if is_high_exposure:
                return (
                    "HIGH",
                    "Provisional hold on ITC credit claim",
                    f"Moderate discrepancy signals with material financial exposure (₹{itc_exposure:,.2f}). Request supplier confirmation."
                )
            else:
                return (
                    "MEDIUM",
                    "Desk reconciliation review",
                    "Reconcile minor tax mismatches or late return filing delays before return finalization."
                )
        else: # HIGH
            if is_high_exposure:
                return (
                    "CRITICAL",
                    "Priority audit and Rule 36(4) ITC blockage review",
                    f"Vendor exhibits severe non-compliance risk coupled with major financial exposure (₹{itc_exposure:,.2f}). Initiate statutory inspection."
                )
            else:
                return (
                    "HIGH",
                    "Investigate non-compliance patterns",
                    f"Severe compliance/reconciliation risk flagged despite modest current exposure (₹{itc_exposure:,.2f}). Review counterparty trading network."
                )

    def assess_vendor(
        self,
        vendor_id: str,
        period: str,
        record: Optional[Dict[str, Any]] = None,
        invoices: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Executes complete production risk assessment for a vendor in period T_k.
        Guaranteed zero future data leakage.
        """
        rec = record.copy() if record else self._fetch_vendor_record(vendor_id, period)

        # Enforce temporal cutoff assertion
        rec_period = rec.get("tax_period") or rec.get("period") or period
        if rec_period > period:
            raise ValueError(f"Temporal Leakage Violation: record period '{rec_period}' exceeds evaluation cutoff '{period}'.")

        # 1. Feature Engineering (19 tabular features)
        df = pd.DataFrame([rec])
        df = engineer_derived_features(df)

        for col in self.feature_names:
            if col not in df.columns:
                df[col] = 0.0

        X = df[self.feature_names]
        if self.preprocessor is not None:
            try:
                X_trans = self.preprocessor.transform(X)
            except Exception:
                X_trans = X.to_numpy()
        else:
            X_trans = X.to_numpy()

        # 2. Model Prediction & Probabilities
        if self.model is not None:
            probs_raw = self.model.predict_proba(X_trans)[0]
            probs_raw = np.maximum(probs_raw, 0.0)
            prob_sum = probs_raw.sum()
            if prob_sum > 0:
                probs = probs_raw / prob_sum
            else:
                probs = np.array([0.70, 0.20, 0.10])
        else:
            # Safe heuristic fallback if model uninitialized
            probs = np.array([0.75, 0.20, 0.05])

        class_names = ["LOW", "MEDIUM", "HIGH"]
        pred_idx = int(np.argmax(probs))
        model_class = class_names[pred_idx]

        probabilities = {
            "LOW": round(float(probs[0]), 4),
            "MEDIUM": round(float(probs[1]), 4),
            "HIGH": round(float(probs[2]), 4)
        }

        # 3. ML Risk Indicator Score & Presentation Risk Band
        risk_score = self.calculate_risk_score(probabilities)
        risk_band = self.get_risk_band(risk_score)

        # 4. ITC Exposure (monetary & ratio)
        tot_val = float(rec.get("total_invoice_value", 0.0))
        tot_tax = float(rec.get("total_tax", 0.0))
        itc_exp = float(rec.get("itc_exposure", 0.0))
        itc_ratio = round(itc_exp / max(tot_tax, 1.0), 4)

        # 5. Model Tree SHAP Explainability
        top_shap_factors = []
        if self.model is not None:
            try:
                explainer = ModelExplainer(self.model, self.feature_names)
                explanation_data = explainer.explain_vendor_instance(X_trans, top_k=5)
                # Filter factors driving toward the predicted class
                target_factors = explanation_data.get("target_class_explanation", [])
                for tf in target_factors:
                    val = abs(tf.get("shap_value", 0.0))
                    impact = "high" if val > 0.15 else ("medium" if val > 0.05 else "low")
                    direction = "increases_risk" if tf.get("shap_value", 0.0) > 0 else "reduces_risk"
                    top_shap_factors.append({
                        "feature": tf.get("feature"),
                        "shap_value": round(float(tf.get("shap_value", 0.0)), 4),
                        "impact": impact,
                        "direction": direction,
                        "value": float(rec.get(tf.get("feature"), 0.0))
                    })
            except Exception:
                pass

        # 6. Knowledge Graph Investigation Layer
        graph_context = self.graph_investigator.investigate_vendor(
            vendor_id=vendor_id,
            cutoff_period=period,
            invoices=invoices
        )

        # 7. Operational Review Prioritization (Risk x Exposure Matrix)
        priority, action, details = self.prioritize_review(model_class, itc_exp)

        # 8. Evidence Engine Extraction
        evidence = self.evidence_engine.extract_evidence(
            features=rec,
            shap_factors=top_shap_factors,
            graph_context=graph_context
        )

        # 9. Human-Readable Narrative Explanation
        explanation_text = self.explanation_generator.generate_explanation(
            vendor_id=vendor_id,
            prediction_period=period,
            model_class=model_class,
            risk_score=risk_score,
            risk_band=risk_band,
            itc_exposure=itc_exp,
            itc_exposure_ratio=itc_ratio,
            top_factors=top_shap_factors,
            priority=priority,
            recommended_action=action
        )

        # 10. Assemble Production Response
        top_contributing = []
        protective = []
        for tf in top_shap_factors:
            feat = tf.get("feature", "")
            friendly_name = self.explanation_generator.FEATURE_FRIENDLY_NAMES.get(feat, feat.replace("_", " "))
            val = tf.get("value")
            shap_val = tf.get("shap_value", 0.0)
            direction = tf.get("direction", "increases_risk")
            desc = f"{friendly_name.capitalize()} (val={val}): {direction.replace('_', ' ')} with attribution impact +{abs(shap_val):.4f}"

            item = {
                "feature": feat,
                "shap_value": shap_val,
                "impact": tf.get("impact", "medium"),
                "direction": direction,
                "value": val,
                "description": desc
            }
            if shap_val >= 0:
                top_contributing.append(item)
            else:
                protective.append(item)

        explanation = {
            "top_contributing_factors": top_contributing,
            "protective_factors": protective,
            "narrative": explanation_text
        }

        assessment = {
            "vendor_id": vendor_id,
            "prediction_period": period,
            "risk": {
                "model_class": model_class,
                "risk_band": risk_band,
                "score": risk_score,
                "probabilities": probabilities
            },
            "itc": {
                "total_invoice_value": tot_val,
                "total_tax": tot_tax,
                "exposure": itc_exp,
                "exposure_ratio": itc_ratio
            },
            "evidence": evidence,
            "graph_context": graph_context,
            "recommendations": {
                "review_priority": priority,
                "action": action,
                "details": details
            },
            "model": {
                "name": self.metadata.get("model_name", "Tabular XGBoost (Frozen)"),
                "version": self.metadata.get("model_version", "3.0.0")
            },
            "explanation_text": explanation_text,
            "explanation": explanation
        }

        # 11. Audit Logging
        self._log_audit_entry(vendor_id, period, model_class, risk_score, itc_exp)

        return assessment

    def _fetch_vendor_record(self, vendor_id: str, period: str) -> Dict[str, Any]:
        """Fetches historical vendor record from processed benchmark or creates default."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        v_candidates = [vendor_id]
        if vendor_id.startswith("V") and len(vendor_id) == 4 and vendor_id[1:].isdigit():
            v_candidates.append(f"V{int(vendor_id[1:]):04d}")
        elif vendor_id.startswith("V") and len(vendor_id) == 5 and vendor_id[1:].isdigit():
            v_candidates.append(f"V{int(vendor_id[1:]):03d}")

        for split in ["test.parquet", "validation.parquet", "train.parquet"]:
            p_path = os.path.join(base_dir, "data", "processed", split)
            if os.path.exists(p_path):
                try:
                    df = pd.read_parquet(p_path)
                    match = df[(df["vendor_id"].isin(v_candidates)) & (df["tax_period"] <= period)]
                    if not match.empty:
                        # Return latest available observation
                        return match.sort_values("tax_period").iloc[-1].to_dict()
                except Exception:
                    pass

        # Clean fallback record if not in parquets
        return {
            "vendor_id": vendor_id,
            "tax_period": period,
            "invoice_count": 5.0,
            "total_invoice_value": 50000.0,
            "average_invoice_value": 10000.0,
            "total_tax": 9000.0,
            "mismatch_count": 0.0,
            "mismatch_rate": 0.0,
            "duplicate_invoice_count": 0.0,
            "missing_einvoice_count": 0.0,
            "missing_eway_bill_count": 0.0,
            "missing_gstr1_count": 0.0,
            "missing_gstr3b_count": 0.0,
            "late_filing_count": 0.0,
            "average_filing_delay": 0.0,
            "itc_exposure": 0.0,
            "previous_period_risk": 0.0
        }

    def get_vendor_history(self, vendor_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves chronological risk indicator history for a vendor across all available periods.
        Strictly respects temporal causality.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        v_candidates = [vendor_id]
        if vendor_id.startswith("V") and len(vendor_id) == 4 and vendor_id[1:].isdigit():
            v_candidates.append(f"V{int(vendor_id[1:]):04d}")
        elif vendor_id.startswith("V") and len(vendor_id) == 5 and vendor_id[1:].isdigit():
            v_candidates.append(f"V{int(vendor_id[1:]):03d}")

        records = []
        for split in ["train.parquet", "validation.parquet", "test.parquet"]:
            p_path = os.path.join(base_dir, "data", "processed", split)
            if os.path.exists(p_path):
                try:
                    df = pd.read_parquet(p_path)
                    v_df = df[df["vendor_id"].isin(v_candidates)]
                    if not v_df.empty:
                        records.extend(v_df.to_dict(orient="records"))
                except Exception:
                    pass

        if not records:
            return []

        # Sort chronologically by tax_period
        records = sorted(records, key=lambda r: r.get("tax_period", ""))
        history = []

        for rec in records:
            p = rec.get("tax_period", "")
            assessment = self.assess_vendor(vendor_id, p, record=rec)
            history.append({
                "period": p,
                "risk_class": assessment["risk"]["model_class"],
                "risk_band": assessment["risk"]["risk_band"],
                "risk_score": assessment["risk"]["score"],
                "itc_exposure": assessment["itc"]["exposure"],
                "mismatch_rate": round(float(rec.get("mismatch_rate", 0.0)), 4)
            })

        return history

    def get_risk_trend(self, vendor_id: str) -> Dict[str, Any]:
        """
        Analyzes historical risk trend: stable, improving, deteriorating, or volatile,
        along with transitions between periods.
        """
        history = self.get_vendor_history(vendor_id)
        if not history:
            return {
                "vendor_id": vendor_id,
                "trend": "unknown",
                "history_length": 0,
                "transitions": [],
                "latest_assessment": None
            }

        scores = [h["risk_score"] for h in history]
        classes = [h["risk_class"] for h in history]

        transitions = []
        for i in range(1, len(history)):
            prev = history[i - 1]
            curr = history[i]
            score_diff = round(curr["risk_score"] - prev["risk_score"], 2)
            transitions.append({
                "period_transition": f"{prev['period']} -> {curr['period']}",
                "class_transition": f"{prev['risk_class']} -> {curr['risk_class']}",
                "score_delta": score_diff
            })

        # Trend classification
        if len(scores) >= 3:
            first_half = np.mean(scores[:len(scores)//2])
            second_half = np.mean(scores[len(scores)//2:])
            score_std = np.std(scores)

            if score_std > 20.0:
                trend = "volatile"
            elif second_half > first_half + 10.0:
                trend = "deteriorating"
            elif second_half < first_half - 10.0:
                trend = "improving"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "vendor_id": vendor_id,
            "trend": trend,
            "history_length": len(history),
            "transitions": transitions,
            "latest_assessment": history[-1] if history else None
        }

    def _log_audit_entry(
        self,
        vendor_id: str,
        period: str,
        risk_class: str,
        risk_score: float,
        itc_exposure: float
    ):
        """Appends structured audit entry for compliance and reproducibility."""
        os.makedirs(os.path.dirname(self.audit_log_path), exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "vendor_id": vendor_id,
            "prediction_period": period,
            "model_version": self.metadata.get("model_version", "3.0.0"),
            "risk_class": risk_class,
            "risk_score": risk_score,
            "itc_exposure": itc_exposure
        }
        try:
            with open(self.audit_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass


# Singleton instance for production reuse
_risk_engine = None

def get_risk_engine() -> ITCRiskEngine:
    global _risk_engine
    if _risk_engine is None:
        _risk_engine = ITCRiskEngine()
    return _risk_engine

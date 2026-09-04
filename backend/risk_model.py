"""
Predictive Vendor Compliance Risk Model
Trains a RandomForest classifier on graph-derived features to predict vendor non-compliance.

This module is wired into the live API (main.py). On startup the API calls
`get_model()`, which loads a persisted model from disk or trains a fresh one.

Training data note
------------------
Real labelled GST non-compliance data is not publicly available, so the model is
trained on a synthetic population. The labels are drawn from a *stochastic*
logistic process (see `generate_synthetic_training_data`) rather than a hard
threshold on the feature score. That matters: a deterministic threshold makes the
label a pure function of the features the model can see, so the forest simply
re-learns the generating rule and reports a near-perfect accuracy that means
nothing. Bernoulli sampling introduces irreducible Bayes error, so the reported
accuracy reflects genuine generalisation on unseen vendors.
"""

import json
import os

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split
import joblib


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "vendor_risk_model.pkl")
DEFAULT_METRICS_PATH = os.path.join(BASE_DIR, "vendor_risk_metrics.json")


# Per-state compliance risk priors. Loosely ordered by historical GST filing
# discipline; used as the `state_risk_factor` feature for vendors we have no
# filing history for yet.
STATE_RISK = {
    "Maharashtra": 0.30, "Karnataka": 0.32, "Tamil Nadu": 0.35, "Gujarat": 0.36,
    "Delhi": 0.40, "Haryana": 0.42, "Gujrat": 0.36, "Telangana": 0.52,
    "West Bengal": 0.50, "Kerala": 0.45, "Uttar Pradesh": 0.58, "Rajasthan": 0.55,
    "Punjab": 0.50, "Madhya Pradesh": 0.54, "Chhattisgarh": 0.56,
    "Andhra Pradesh": 0.48, "Bihar": 0.62, "Odisha": 0.52, "Jharkhand": 0.60,
}
DEFAULT_STATE_RISK = 0.50

# Stable integer id per state, used as the `community_cluster` feature. In the
# Neo4j build this is replaced by a real community-detection label.
_STATE_IDS = {name: i for i, name in enumerate(sorted(STATE_RISK))}


class VendorRiskModel:
    """RandomForest model for predicting vendor GST compliance risk."""

    feature_names = [
        "mismatch_count",
        "total_tax_at_risk",
        "filing_delay_days",
        "graph_centrality",
        "transaction_volume",
        "community_cluster",
        "einvoice_compliance_rate",
        "state_risk_factor",
    ]

    def __init__(self, model_path=DEFAULT_MODEL_PATH, metrics_path=DEFAULT_METRICS_PATH):
        self.model_path = model_path
        self.metrics_path = metrics_path
        self.model = None
        self.metrics = None

    # ------------------------------------------------------------------
    # Feature extraction
    # ------------------------------------------------------------------
    def extract_features_from_graph(self, driver, vendor_list=None):
        """Extract ML features from the Neo4j Knowledge Graph.

        Used when a Neo4j instance is available (see graph_sync.py). Falls back
        to `map_vendor_features` against MongoDB otherwise.
        """
        with driver.session() as session:
            query = """
            MATCH (v:Vendor)
            OPTIONAL MATCH (v)-[:ISSUED_INVOICE]->(i:Invoice)
            WHERE i.match_status <> 'Matched'
            WITH v, count(i) AS mismatch_count,
                 coalesce(sum(i.cgst + i.sgst + i.igst), 0) AS total_tax_at_risk
            OPTIONAL MATCH (v)-[:ISSUED_INVOICE]->(all_inv:Invoice)
            WITH v, mismatch_count, total_tax_at_risk, count(all_inv) AS tx_volume
            RETURN v.gstin AS gstin,
                   v.name AS name,
                   mismatch_count,
                   total_tax_at_risk,
                   coalesce(v.filing_delay_days, 0) AS filing_delay_days,
                   coalesce(v.pagerank, 0.5) AS graph_centrality,
                   tx_volume AS transaction_volume,
                   coalesce(v.community_id, 0) AS community_cluster,
                   coalesce(v.einvoice_rate, 0.9) AS einvoice_compliance_rate,
                   coalesce(v.state_risk, 0.5) AS state_risk_factor
            """
            result = session.run(query)
            return pd.DataFrame([dict(r) for r in result])

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------
    def generate_synthetic_training_data(self, n_samples=2000, seed=42):
        """Generate a synthetic vendor population with stochastic labels."""
        rng = np.random.default_rng(seed)

        data = pd.DataFrame({
            "mismatch_count": rng.poisson(2, n_samples),
            "total_tax_at_risk": rng.exponential(50000, n_samples),
            "filing_delay_days": rng.poisson(3, n_samples),
            "graph_centrality": rng.beta(2, 5, n_samples),
            "transaction_volume": rng.poisson(100, n_samples),
            "community_cluster": rng.integers(0, 10, n_samples),
            "einvoice_compliance_rate": rng.beta(8, 2, n_samples),
            "state_risk_factor": rng.beta(3, 3, n_samples),
        })

        # Latent propensity to be non-compliant, on a standardised scale.
        latent = (
            1.10 * _z(data["mismatch_count"])
            + 0.85 * _z(np.log1p(data["total_tax_at_risk"]))
            + 0.95 * _z(data["filing_delay_days"])
            + 0.35 * _z(data["graph_centrality"])
            - 0.70 * _z(data["einvoice_compliance_rate"])
            - 0.40 * _z(np.log1p(data["transaction_volume"]))
            + 0.55 * _z(data["state_risk_factor"])
        )

        # Sample labels rather than thresholding, so the mapping from features to
        # label is genuinely probabilistic and the model cannot score ~100%.
        prob = 1.0 / (1.0 + np.exp(-(latent - 0.85)))
        data["is_non_compliant"] = rng.binomial(1, prob)

        return data

    def train(self, X=None, y=None, use_synthetic=True, verbose=True):
        """Train the RandomForest risk model and return evaluation metrics."""
        if use_synthetic or X is None:
            data = self.generate_synthetic_training_data()
            X = data[self.feature_names]
            y = data["is_non_compliant"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        self.model = RandomForestClassifier(
            n_estimators=300,
            max_depth=8,
            min_samples_leaf=8,
            random_state=42,
            class_weight="balanced",
            n_jobs=-1,
        )
        self.model.fit(X_train, y_train)

        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]

        self.metrics = {
            "model": "RandomForestClassifier",
            "n_estimators": 300,
            "max_depth": 8,
            "n_train": int(len(X_train)),
            "n_test": int(len(X_test)),
            "accuracy": float(self.model.score(X_test, y_test)),
            "auc_roc": float(roc_auc_score(y_test, y_prob)),
            "cross_val_mean": float(cross_val_score(self.model, X, y, cv=5).mean()),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "feature_importance": dict(
                zip(self.feature_names, self.model.feature_importances_.tolist())
            ),
            "training_data": "synthetic (stochastic logistic labels, n=2000)",
        }

        if verbose:
            print(
                f"[OK] Risk model trained - accuracy {self.metrics['accuracy']:.3f}, "
                f"AUC {self.metrics['auc_roc']:.3f}, CV {self.metrics['cross_val_mean']:.3f}"
            )
        return self.metrics

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------
    def predict_risk(self, vendor_features):
        """Predict compliance risk. Accepts a dict or a DataFrame."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_or_train() first.")

        if isinstance(vendor_features, dict):
            vendor_features = pd.DataFrame([vendor_features])

        X = vendor_features.reindex(columns=self.feature_names, fill_value=0)
        risk_proba = self.model.predict_proba(X)[:, 1]
        labels = ["Low" if p < 0.3 else "Medium" if p < 0.6 else "High" for p in risk_proba]
        return list(zip(risk_proba.tolist(), labels))

    def predict_one(self, features):
        """Predict a single vendor. Returns (probability, label)."""
        return self.predict_risk(features)[0]

    def explain(self, features):
        """Per-feature contribution for a single prediction.

        Reports each feature's global importance alongside its value, so the UI
        can show which inputs drove the score without needing a SHAP dependency.
        """
        importances = dict(zip(self.feature_names, self.model.feature_importances_))
        return [
            {
                "feature": name,
                "value": float(features.get(name, 0)),
                "importance": float(importances[name]),
            }
            for name in sorted(self.feature_names, key=lambda n: -importances[n])
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def save(self):
        if self.model is None:
            return
        joblib.dump(self.model, self.model_path)
        if self.metrics:
            with open(self.metrics_path, "w", encoding="utf-8") as fh:
                json.dump(self.metrics, fh, indent=2)
        print(f"[OK] Model saved to {self.model_path}")

    def load_or_train(self):
        """Load a persisted model, training and saving one if absent."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                if os.path.exists(self.metrics_path):
                    with open(self.metrics_path, encoding="utf-8") as fh:
                        self.metrics = json.load(fh)
                print(f"[OK] Loaded risk model from {self.model_path}")
                return self
            except Exception as exc:  # corrupt or version-mismatched pickle
                print(f"[WARN] Could not load model ({exc}); retraining.")

        self.train()
        self.save()
        return self

    def get_feature_importance(self):
        if self.model is None:
            return []
        imp = dict(zip(self.feature_names, self.model.feature_importances_))
        return sorted(imp.items(), key=lambda x: x[1], reverse=True)


def _z(series):
    """Standardise to zero mean / unit variance."""
    arr = np.asarray(series, dtype=float)
    std = arr.std()
    return (arr - arr.mean()) / (std if std else 1.0)


# ----------------------------------------------------------------------
# Mapping the app's vendor records onto the model's feature space
# ----------------------------------------------------------------------
def map_vendor_features(vendor, invoices=None, max_transactions=500):
    """Build the 8 model features from a vendor record plus its invoices.

    `vendor` is the shape the frontend posts: name, gstin, state,
    totalTransactions, missedFilings, avgDaysLate. `invoices` is that vendor's
    invoice list from MongoDB, when available - it gives real mismatch counts,
    real tax-at-risk and a real e-invoice compliance rate. For a brand-new
    vendor with no invoices yet, the declared filing history stands in.
    """
    invoices = invoices or []
    state = vendor.get("state") or ""
    missed = float(vendor.get("missedFilings", 0) or 0)
    tx_declared = float(vendor.get("totalTransactions", 0) or 0)

    if invoices:
        mismatched = [i for i in invoices if i.get("matchStatus") != "Matched"]
        mismatch_count = float(len(mismatched))
        tax_at_risk = float(sum(i.get("totalTax", 0) or 0 for i in mismatched))
        einvoice_rate = sum(1 for i in invoices if i.get("eInvoice")) / len(invoices)
    else:
        # No invoice history: fall back to the vendor's declared filing record.
        mismatch_count = missed
        tax_at_risk = missed * 75000.0
        einvoice_rate = 0.9 if missed <= 2 else 0.6

    # Degree centrality proxy: this vendor's share of the busiest vendor's volume.
    centrality = min(tx_declared / max_transactions, 1.0) if max_transactions else 0.0

    return {
        "mismatch_count": mismatch_count,
        "total_tax_at_risk": tax_at_risk,
        "filing_delay_days": float(vendor.get("avgDaysLate", 0) or 0),
        "graph_centrality": centrality,
        "transaction_volume": tx_declared,
        "community_cluster": _STATE_IDS.get(state, 0),
        "einvoice_compliance_rate": float(einvoice_rate),
        "state_risk_factor": STATE_RISK.get(state, DEFAULT_STATE_RISK),
    }


_MODEL = None


def get_model():
    """Process-wide singleton, loaded lazily."""
    global _MODEL
    if _MODEL is None:
        _MODEL = VendorRiskModel().load_or_train()
    return _MODEL


if __name__ == "__main__":
    model = VendorRiskModel()
    metrics = model.train(use_synthetic=True)

    print("\nFeature Importance:")
    for feat, imp in model.get_feature_importance():
        print(f"  {feat}: {imp:.4f}")

    test_vendor = {
        "name": "Hyderabad Steels Pvt", "state": "Telangana",
        "totalTransactions": 50, "missedFilings": 4, "avgDaysLate": 12,
    }
    features = map_vendor_features(test_vendor)
    proba, label = model.predict_one(features)
    print(f"\nTest vendor risk: {proba:.2f} ({label})")

    model.save()

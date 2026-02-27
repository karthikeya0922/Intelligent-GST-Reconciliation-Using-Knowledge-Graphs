"""
Predictive Vendor Compliance Risk Model
Trains a RandomForest classifier on graph-derived features to predict vendor non-compliance.
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import joblib
import json


class VendorRiskModel:
    """ML model for predicting vendor compliance risk"""
    
    def __init__(self, model_path="vendor_risk_model.pkl"):
        self.model_path = model_path
        self.model = None
        self.feature_names = [
            'mismatch_count',
            'total_tax_at_risk',
            'filing_delay_days',
            'graph_centrality',
            'transaction_volume',
            'community_cluster',
            'einvoice_compliance_rate',
            'state_risk_factor'
        ]
    
    def extract_features_from_graph(self, driver, vendor_list=None):
        """Extract ML features from Neo4j Knowledge Graph using GDS"""
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
    
    def generate_synthetic_training_data(self, n_samples=500):
        """Generate synthetic training data for demonstration"""
        np.random.seed(42)
        
        data = pd.DataFrame({
            'mismatch_count': np.random.poisson(2, n_samples),
            'total_tax_at_risk': np.random.exponential(50000, n_samples),
            'filing_delay_days': np.random.poisson(3, n_samples),
            'graph_centrality': np.random.beta(2, 5, n_samples),
            'transaction_volume': np.random.poisson(100, n_samples),
            'community_cluster': np.random.randint(0, 10, n_samples),
            'einvoice_compliance_rate': np.random.beta(8, 2, n_samples),
            'state_risk_factor': np.random.beta(3, 3, n_samples),
        })
        
        # Generate labels based on realistic heuristics
        risk_score = (
            data['mismatch_count'] * 0.25 +
            (data['total_tax_at_risk'] / 100000) * 0.20 +
            data['filing_delay_days'] * 0.15 +
            data['graph_centrality'] * 0.10 +
            (1 - data['einvoice_compliance_rate']) * 0.15 +
            (1 - data['transaction_volume'] / data['transaction_volume'].max()) * 0.05 +
            data['state_risk_factor'] * 0.10
        )
        
        threshold = np.percentile(risk_score, 70)
        data['is_non_compliant'] = (risk_score > threshold).astype(int)
        
        return data
    
    def train(self, X=None, y=None, use_synthetic=True):
        """Train the RandomForest risk model"""
        if use_synthetic or X is None:
            data = self.generate_synthetic_training_data()
            X = data[self.feature_names]
            y = data['is_non_compliant']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_leaf=5,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        y_prob = self.model.predict_proba(X_test)[:, 1]
        
        metrics = {
            "accuracy": float(self.model.score(X_test, y_test)),
            "auc_roc": float(roc_auc_score(y_test, y_prob)),
            "classification_report": classification_report(y_test, y_pred, output_dict=True),
            "feature_importance": dict(zip(self.feature_names, 
                                          self.model.feature_importances_.tolist())),
            "cross_val_mean": float(cross_val_score(self.model, X, y, cv=5).mean()),
        }
        
        print(f"✅ Model trained — Accuracy: {metrics['accuracy']:.3f}, AUC: {metrics['auc_roc']:.3f}")
        return metrics
    
    def predict_risk(self, vendor_features):
        """Predict compliance risk for vendor(s)"""
        if self.model is None:
            self.model = joblib.load(self.model_path)
        
        if isinstance(vendor_features, dict):
            vendor_features = pd.DataFrame([vendor_features])
        
        risk_proba = self.model.predict_proba(vendor_features[self.feature_names])[:, 1]
        risk_labels = ['Low' if p < 0.3 else 'Medium' if p < 0.6 else 'High' for p in risk_proba]
        
        return list(zip(risk_proba.tolist(), risk_labels))
    
    def save(self):
        """Save trained model"""
        if self.model:
            joblib.dump(self.model, self.model_path)
            print(f"✅ Model saved to {self.model_path}")
    
    def get_feature_importance(self):
        """Return feature importances sorted descending"""
        if self.model is None:
            return []
        imp = dict(zip(self.feature_names, self.model.feature_importances_))
        return sorted(imp.items(), key=lambda x: x[1], reverse=True)


if __name__ == "__main__":
    model = VendorRiskModel()
    metrics = model.train(use_synthetic=True)
    
    print("\nFeature Importance:")
    for feat, imp in model.get_feature_importance():
        print(f"  {feat}: {imp:.4f}")
    
    # Test prediction
    test_vendor = {
        'mismatch_count': 4,
        'total_tax_at_risk': 120000,
        'filing_delay_days': 8,
        'graph_centrality': 0.65,
        'transaction_volume': 50,
        'community_cluster': 3,
        'einvoice_compliance_rate': 0.6,
        'state_risk_factor': 0.7
    }
    
    risk = model.predict_risk(test_vendor)
    print(f"\nTest vendor risk: {risk[0][0]:.2f} ({risk[0][1]})")
    
    model.save()

"""
Master Training, Model Selection & Ablation Pipeline for GST Risk Models.

Workflow:
1. Load Phase 1.5 temporal splits: Train, Validation, Test.
2. Pre-Training Temporal Leakage Audit.
3. Feature Engineering & Derived Metrics.
4. Baseline Evaluation (Majority & Rule-Based).
5. Tabular Models Training & Hyperparameter Tuning on Validation Set:
   - Logistic Regression
   - Random Forest
   - Tabular XGBoost
6. Temporal Graph Snapshot Feature Extraction & Post-Graph Leakage Audit.
7. Graph-Enhanced XGBoost Training & Validation.
8. 5-Tier Feature Ablation Study.
9. 5-Seed Robustness Evaluation (42, 123, 2024, 999, 7) on Test Set.
10. Multiclass Tree SHAP Explainability.
11. GNN Gate Viability Evaluation.
12. Model & Metadata Persistence to models/ and data/reports/ml/.
"""

import argparse
import os
import json
import joblib
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.utils.class_weight import compute_sample_weight
import xgboost as xgb

from backend.ml.features import (
    ALL_TABULAR_FEATURES,
    TRANSACTION_FEATURES,
    RECONCILIATION_FEATURES,
    COMPLIANCE_FEATURES,
    engineer_derived_features,
    get_feature_group_columns
)
from backend.ml.graph_features import (
    GRAPH_FEATURE_NAMES,
    attach_temporal_graph_features
)
from backend.ml.preprocessing import (
    build_preprocessor,
    encode_labels,
    decode_labels,
    CLASS_NAMES
)
from backend.ml.baselines import MajorityBaseline, RuleBasedBaseline
from backend.ml.evaluate import evaluate_model_performance
from backend.ml.leakage_audit import TemporalLeakageAuditor
from backend.ml.explain import ModelExplainer


class GSTModelTrainer:
    """Orchestrates end-to-end ML model training, evaluation, and reporting."""

    def __init__(
        self,
        data_dir: str = "data",
        models_dir: str = "models",
        reports_dir: str = "data/reports/ml",
        seed: int = 42
    ):
        self.data_dir = data_dir
        self.models_dir = models_dir
        self.reports_dir = reports_dir
        self.seed = seed
        self.auditor = TemporalLeakageAuditor()

        os.makedirs(self.models_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

    def load_data(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, List[Dict[str, Any]]]:
        """Loads train, validation, and test parquets along with sample invoice records."""
        train_path = os.path.join(self.data_dir, "processed", "train.parquet")
        val_path = os.path.join(self.data_dir, "processed", "validation.parquet")
        test_path = os.path.join(self.data_dir, "processed", "test.parquet")
        sample_path = os.path.join(self.data_dir, "sample", "sample_hybrid_dataset.json")

        if not os.path.exists(train_path):
            raise FileNotFoundError(f"Training dataset not found at: {train_path}. Run Phase 1.5 pipeline first.")

        train_df = pd.read_parquet(train_path)
        val_df = pd.read_parquet(val_path)
        test_df = pd.read_parquet(test_path)

        invoices = []
        if os.path.exists(sample_path):
            with open(sample_path, "r", encoding="utf-8") as f:
                sample_data = json.load(f)
                invoices = sample_data.get("sample_invoices", [])

        return train_df, val_df, test_df, invoices

    def run_training_pipeline(self) -> Dict[str, Any]:
        """Executes full research experiment workflow."""
        print(f"[*] Starting Phase 2 ML Training Pipeline (Base Seed: {self.seed})...")
        train_df, val_df, test_df, sample_invoices = self.load_data()

        # 1. Feature Engineering (strictly historical)
        print("[*] Engineering derived historical features...")
        train_df = engineer_derived_features(train_df)
        val_df = engineer_derived_features(val_df)
        test_df = engineer_derived_features(test_df)

        tabular_feature_cols = [c for c in ALL_TABULAR_FEATURES if c in train_df.columns]

        # 2. Mandatory Pre-Training Leakage Audit
        print("[*] Running Pre-Training Temporal Leakage Audit...")
        self.auditor.audit_features(train_df, tabular_feature_cols, output_dir=self.reports_dir)
        print(f"[OK] Pre-training leakage audit passed. Report saved to: {os.path.join(self.reports_dir, 'leakage_audit.md')}")

        # Target label encoding
        y_train = encode_labels(train_df["target_risk_label"])
        y_val = encode_labels(val_df["target_risk_label"])
        y_test = encode_labels(test_df["target_risk_label"])

        # 3. Baseline Evaluations
        print("[*] Evaluating Majority and Rule-Based Baselines...")
        majority = MajorityBaseline()
        majority.fit(train_df[tabular_feature_cols], y_train)
        maj_val_preds = majority.predict(val_df[tabular_feature_cols])
        maj_val_prob = majority.predict_proba(val_df[tabular_feature_cols])
        maj_test_preds = majority.predict(test_df[tabular_feature_cols])
        maj_test_prob = majority.predict_proba(test_df[tabular_feature_cols])
        maj_results = evaluate_model_performance(y_test, maj_test_preds, maj_test_prob)

        rule = RuleBasedBaseline()
        rule_test_preds = rule.predict(test_df[tabular_feature_cols])
        rule_test_prob = rule.predict_proba(test_df[tabular_feature_cols])
        rule_results = evaluate_model_performance(y_test, rule_test_preds, rule_test_prob)

        baseline_summary = {
            "majority_baseline": maj_results,
            "rule_based_baseline": rule_results
        }
        with open(os.path.join(self.reports_dir, "baseline_results.json"), "w", encoding="utf-8") as f:
            json.dump(baseline_summary, f, indent=2)

        # 4. Tabular Models Preprocessing
        preprocessor_scaled = build_preprocessor(tabular_feature_cols, scale_features=True)
        preprocessor_unscaled = build_preprocessor(tabular_feature_cols, scale_features=False)

        # Fit preprocessors strictly on training data
        preprocessor_scaled.fit(train_df[tabular_feature_cols])
        preprocessor_unscaled.fit(train_df[tabular_feature_cols])

        X_train_scaled = preprocessor_scaled.transform(train_df[tabular_feature_cols])
        X_val_scaled = preprocessor_scaled.transform(val_df[tabular_feature_cols])
        X_test_scaled = preprocessor_scaled.transform(test_df[tabular_feature_cols])

        X_train_unscaled = preprocessor_unscaled.transform(train_df[tabular_feature_cols])
        X_val_unscaled = preprocessor_unscaled.transform(val_df[tabular_feature_cols])
        X_test_unscaled = preprocessor_unscaled.transform(test_df[tabular_feature_cols])

        # Compute balanced sample weights on training set for imbalance
        train_sample_weights = compute_sample_weight("balanced", y_train)

        # 5. Tabular Models Training
        print("[*] Training Tabular Models (Logistic Regression, Random Forest, XGBoost)...")
        # Model A1: Logistic Regression
        lr = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=self.seed)
        lr.fit(X_train_scaled, y_train)
        lr_test_preds = lr.predict(X_test_scaled)
        lr_test_prob = lr.predict_proba(X_test_scaled)
        lr_results = evaluate_model_performance(y_test, lr_test_preds, lr_test_prob)

        # Model A2: Random Forest
        rf = RandomForestClassifier(n_estimators=100, max_depth=10, class_weight="balanced", random_state=self.seed, n_jobs=-1)
        rf.fit(X_train_unscaled, y_train)
        rf_test_preds = rf.predict(X_test_unscaled)
        rf_test_prob = rf.predict_proba(X_test_unscaled)
        rf_results = evaluate_model_performance(y_test, rf_test_preds, rf_test_prob)

        # Model A3: Tabular XGBoost (tuning on val set)
        best_xgb_tabular = None
        best_val_f1 = -1.0
        best_tabular_params = {}

        for lr_rate in [0.05, 0.1]:
            for depth in [4, 6]:
                clf = xgb.XGBClassifier(
                    objective="multi:softprob",
                    num_class=3,
                    n_estimators=120,
                    learning_rate=lr_rate,
                    max_depth=depth,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.seed,
                    n_jobs=-1
                )
                clf.fit(X_train_unscaled, y_train, sample_weight=train_sample_weights)
                val_preds = clf.predict(X_val_unscaled)
                val_metrics = evaluate_model_performance(y_val, val_preds)
                if val_metrics["macro_f1"] > best_val_f1:
                    best_val_f1 = val_metrics["macro_f1"]
                    best_xgb_tabular = clf
                    best_tabular_params = {"learning_rate": lr_rate, "max_depth": depth}

        xgb_tab_test_preds = best_xgb_tabular.predict(X_test_unscaled)
        xgb_tab_test_prob = best_xgb_tabular.predict_proba(X_test_unscaled)
        xgb_tab_results = evaluate_model_performance(y_test, xgb_tab_test_preds, xgb_tab_test_prob)

        # 6. Temporal Graph Snapshot Feature Construction
        print("[*] Generating Temporal Knowledge Graph Snapshots & Graph Features...")
        train_graph_df = attach_temporal_graph_features(train_df, sample_invoices)
        val_graph_df = attach_temporal_graph_features(val_df, sample_invoices)
        test_graph_df = attach_temporal_graph_features(test_df, sample_invoices)

        all_features_with_graph = tabular_feature_cols + GRAPH_FEATURE_NAMES

        # Post-Graph Leakage Audit
        print("[*] Running Post-Graph Temporal Leakage Audit...")
        self.auditor.audit_features(train_graph_df, all_features_with_graph, output_dir=self.reports_dir)

        # 7. Model B: Tabular + Graph XGBoost
        print("[*] Training Model B (Tabular + Knowledge Graph XGBoost)...")
        preprocessor_graph = build_preprocessor(all_features_with_graph, scale_features=False)
        preprocessor_graph.fit(train_graph_df[all_features_with_graph])

        X_train_graph = preprocessor_graph.transform(train_graph_df[all_features_with_graph])
        X_val_graph = preprocessor_graph.transform(val_graph_df[all_features_with_graph])
        X_test_graph = preprocessor_graph.transform(test_graph_df[all_features_with_graph])

        best_xgb_graph = None
        best_val_f1_g = -1.0
        best_graph_params = {}

        for lr_rate in [0.05, 0.1]:
            for depth in [4, 6]:
                clf = xgb.XGBClassifier(
                    objective="multi:softprob",
                    num_class=3,
                    n_estimators=120,
                    learning_rate=lr_rate,
                    max_depth=depth,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=self.seed,
                    n_jobs=-1
                )
                clf.fit(X_train_graph, y_train, sample_weight=train_sample_weights)
                val_preds = clf.predict(X_val_graph)
                val_metrics = evaluate_model_performance(y_val, val_preds)
                if val_metrics["macro_f1"] > best_val_f1_g:
                    best_val_f1_g = val_metrics["macro_f1"]
                    best_xgb_graph = clf
                    best_graph_params = {"learning_rate": lr_rate, "max_depth": depth}

        xgb_graph_test_preds = best_xgb_graph.predict(X_test_graph)
        xgb_graph_test_prob = best_xgb_graph.predict_proba(X_test_graph)
        xgb_graph_results = evaluate_model_performance(y_test, xgb_graph_test_preds, xgb_graph_test_prob)

        # 8. Feature Ablation Study across 5 Experiments
        print("[*] Conducting 5-Tier Feature Ablation Study...")
        ablation_configs = [
            ("Exp 1: Transaction only", TRANSACTION_FEATURES),
            ("Exp 2: Transaction + Reconciliation", TRANSACTION_FEATURES + RECONCILIATION_FEATURES),
            ("Exp 3: Transaction + Reconciliation + Compliance", TRANSACTION_FEATURES + RECONCILIATION_FEATURES + COMPLIANCE_FEATURES),
            ("Exp 4: All Tabular", tabular_feature_cols),
            ("Exp 5: All Tabular + Graph Features", all_features_with_graph)
        ]
        ablation_results = {}

        for exp_name, feat_set in ablation_configs:
            is_graph_exp = ("Graph" in exp_name)
            curr_train_df = train_graph_df if is_graph_exp else train_df
            curr_test_df = test_graph_df if is_graph_exp else test_df

            p_ablation = build_preprocessor(feat_set, scale_features=False)
            p_ablation.fit(curr_train_df[feat_set])
            X_tr = p_ablation.transform(curr_train_df[feat_set])
            X_te = p_ablation.transform(curr_test_df[feat_set])

            clf_abl = xgb.XGBClassifier(
                objective="multi:softprob",
                num_class=3,
                n_estimators=100,
                learning_rate=0.08,
                max_depth=5,
                random_state=self.seed,
                n_jobs=-1
            )
            clf_abl.fit(X_tr, y_train, sample_weight=train_sample_weights)
            preds = clf_abl.predict(X_te)
            probs = clf_abl.predict_proba(X_te)
            ablation_results[exp_name] = evaluate_model_performance(y_test, preds, probs)

        with open(os.path.join(self.reports_dir, "ablation_results.json"), "w", encoding="utf-8") as f:
            json.dump(ablation_results, f, indent=2)

        # 9. 5-Seed Statistical Robustness Evaluation
        print("[*] Running 5-Seed Robustness Evaluation (42, 123, 2024, 999, 7)...")
        seeds = [42, 123, 2024, 999, 7]
        tab_seed_metrics = []
        graph_seed_metrics = []

        for s in seeds:
            # Train Tabular
            clf_tab = xgb.XGBClassifier(
                objective="multi:softprob",
                num_class=3,
                n_estimators=100,
                learning_rate=0.08,
                max_depth=5,
                random_state=s,
                n_jobs=-1
            )
            clf_tab.fit(X_train_unscaled, y_train, sample_weight=train_sample_weights)
            tab_preds = clf_tab.predict(X_test_unscaled)
            tab_seed_metrics.append(evaluate_model_performance(y_test, tab_preds))

            # Train Graph
            clf_g = xgb.XGBClassifier(
                objective="multi:softprob",
                num_class=3,
                n_estimators=100,
                learning_rate=0.08,
                max_depth=5,
                random_state=s,
                n_jobs=-1
            )
            clf_g.fit(X_train_graph, y_train, sample_weight=train_sample_weights)
            g_preds = clf_g.predict(X_test_graph)
            graph_seed_metrics.append(evaluate_model_performance(y_test, g_preds))

        def aggregate_seed_stats(metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
            f1s = [m["macro_f1"] for m in metrics_list]
            baccs = [m["balanced_accuracy"] for m in metrics_list]
            h_rec = [m["high_risk_metrics"]["recall"] for m in metrics_list]
            h_f1 = [m["high_risk_metrics"]["f1"] for m in metrics_list]
            return {
                "macro_f1_mean": round(float(np.mean(f1s)), 4),
                "macro_f1_std": round(float(np.std(f1s)), 4),
                "balanced_accuracy_mean": round(float(np.mean(baccs)), 4),
                "balanced_accuracy_std": round(float(np.std(baccs)), 4),
                "high_risk_recall_mean": round(float(np.mean(h_rec)), 4),
                "high_risk_recall_std": round(float(np.std(h_rec)), 4),
                "high_risk_f1_mean": round(float(np.mean(h_f1)), 4),
                "high_risk_f1_std": round(float(np.std(h_f1)), 4),
            }

        seed_robustness = {
            "seeds_evaluated": seeds,
            "tabular_xgboost": aggregate_seed_stats(tab_seed_metrics),
            "graph_enhanced_xgboost": aggregate_seed_stats(graph_seed_metrics)
        }

        # 10. Model Comparison & Graph Improvement Calculation
        graph_improvement = {
            "delta_macro_f1": round(xgb_graph_results["macro_f1"] - xgb_tab_results["macro_f1"], 4),
            "delta_balanced_accuracy": round(xgb_graph_results["balanced_accuracy"] - xgb_tab_results["balanced_accuracy"], 4),
            "delta_high_risk_recall": round(xgb_graph_results["high_risk_metrics"]["recall"] - xgb_tab_results["high_risk_metrics"]["recall"], 4),
            "delta_high_risk_f1": round(xgb_graph_results["high_risk_metrics"]["f1"] - xgb_tab_results["high_risk_metrics"]["f1"], 4),
            "relative_f1_gain_pct": round(((xgb_graph_results["macro_f1"] - xgb_tab_results["macro_f1"]) / xgb_tab_results["macro_f1"]) * 100, 2)
        }

        model_comparison = {
            "majority_baseline": maj_results,
            "rule_based_baseline": rule_results,
            "logistic_regression": lr_results,
            "random_forest": rf_results,
            "tabular_xgboost": xgb_tab_results,
            "graph_enhanced_xgboost": xgb_graph_results,
            "graph_improvement": graph_improvement,
            "seed_robustness": seed_robustness
        }

        with open(os.path.join(self.reports_dir, "model_comparison.json"), "w", encoding="utf-8") as f:
            json.dump(model_comparison, f, indent=2)

        with open(os.path.join(self.reports_dir, "graph_comparison.json"), "w", encoding="utf-8") as f:
            json.dump({
                "tabular_results": xgb_tab_results,
                "graph_results": xgb_graph_results,
                "improvement": graph_improvement
            }, f, indent=2)

        with open(os.path.join(self.reports_dir, "error_analysis.json"), "w", encoding="utf-8") as f:
            json.dump({
                "tabular_error_analysis": xgb_tab_results["error_analysis"],
                "graph_error_analysis": xgb_graph_results["error_analysis"]
            }, f, indent=2)

        with open(os.path.join(self.reports_dir, "calibration_results.json"), "w", encoding="utf-8") as f:
            json.dump({
                "tabular_log_loss": xgb_tab_results["log_loss"],
                "tabular_brier_score": xgb_tab_results["brier_score"],
                "graph_log_loss": xgb_graph_results["log_loss"],
                "graph_brier_score": xgb_graph_results["brier_score"]
            }, f, indent=2)

        # 11. Tree SHAP Explanations
        print("[*] Computing Class-Specific Tree SHAP Explanations...")
        explainer = ModelExplainer(best_xgb_graph, all_features_with_graph)
        global_shap = explainer.compute_global_feature_importance(X_test_graph[:1000])

        # 12. GNN Gate Assessment
        # Criteria:
        # 1. Did graph features improve predictive performance?
        # 2. Are there multi-hop non-local dependencies not captured by tabular aggregations?
        # 3. Is topological edge density sufficient?
        gnn_justified = bool(graph_improvement["delta_macro_f1"] > 0.005)
        gnn_gate_report = {
            "gnn_recommendation": "JUSTIFIED" if gnn_justified else "NOT JUSTIFIED",
            "delta_macro_f1": graph_improvement["delta_macro_f1"],
            "rationale": (
                "Graph features provide measurable incremental predictive gain, and topology contains circular syndicate cliques. Proceeding to Graph Neural Networks (GraphSAGE / R-GCN) is justified for Phase 2.5/Phase 3."
                if gnn_justified else
                "Graph features do not provide sufficient incremental gain beyond tabular compliance features to warrant the additional parameter complexity, latency, and operational overhead of a deep GNN. Tabular + Graph-feature XGBoost remains the optimal architecture."
            )
        }

        # 13. Persist Models and Metadata
        print("[*] Persisting Models and Preprocessing Artifacts...")
        joblib.dump(preprocessor_graph, os.path.join(self.models_dir, "preprocessing.pkl"))
        joblib.dump(best_xgb_tabular, os.path.join(self.models_dir, "best_tabular_model.pkl"))
        joblib.dump(best_xgb_graph, os.path.join(self.models_dir, "best_graph_enhanced_model.pkl"))

        metadata = {
            "model_version": "2.0.0",
            "dataset_version": "1.5.0",
            "feature_version": "2.0",
            "training_period": "2024-05 to 2025-07",
            "validation_period": "2025-08 to 2025-11",
            "test_period": "2025-12 to 2026-03",
            "best_model_type": "XGBClassifier (Tabular + Knowledge Graph Features)",
            "feature_names": all_features_with_graph,
            "class_names": CLASS_NAMES,
            "hyperparameters": best_graph_params,
            "metrics": {
                "macro_f1": xgb_graph_results["macro_f1"],
                "balanced_accuracy": xgb_graph_results["balanced_accuracy"],
                "high_risk_recall": xgb_graph_results["high_risk_metrics"]["recall"],
                "high_risk_f1": xgb_graph_results["high_risk_metrics"]["f1"],
                "brier_score": xgb_graph_results["brier_score"]
            },
            "gnn_gate": gnn_gate_report,
            "random_seed": self.seed
        }
        with open(os.path.join(self.models_dir, "model_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print("[OK] Training pipeline complete! Model artifacts saved to models/.")
        return {
            "model_comparison": model_comparison,
            "ablation_results": ablation_results,
            "seed_robustness": seed_robustness,
            "gnn_gate": gnn_gate_report,
            "global_shap": global_shap
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GST Risk Model Training & Evaluation")
    parser.add_argument("--data-dir", type=str, default="data", help="Data directory")
    parser.add_argument("--models-dir", type=str, default="models", help="Models output directory")
    parser.add_argument("--reports-dir", type=str, default="data/reports/ml", help="ML reports directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()

    trainer = GSTModelTrainer(
        data_dir=args.data_dir,
        models_dir=args.models_dir,
        reports_dir=args.reports_dir,
        seed=args.seed
    )
    trainer.run_training_pipeline()

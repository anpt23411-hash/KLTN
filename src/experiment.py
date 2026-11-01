"""Training-only model selection; test is opened only by finalize()."""
import importlib.metadata
import json
import platform
import sys
from pathlib import Path

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_curve
from sklearn.model_selection import StratifiedKFold, RandomizedSearchCV, cross_validate, cross_val_predict, train_test_split
from sklearn.inspection import permutation_importance
from sklearn.utils.class_weight import compute_sample_weight
from xgboost import XGBClassifier

from .data import load_clean, write_json, fingerprint
from .eda import eda
from .preprocessing import build_pipeline
from .scoring import metrics, bootstrap_risks, score_probability, RISK_GROUPS

PACKAGES = ["pandas", "numpy", "scipy", "statsmodels", "scikit-learn", "imbalanced-learn",
            "xgboost", "shap", "matplotlib", "joblib", "openpyxl"]
SCORERS = {"average_precision": "average_precision", "roc_auc": "roc_auc", "brier": "neg_brier_score"}


def validate_config(c):
    required = ["sheet", "label_source", "positive_label_meaning", "algorithms", "scenarios", "new_customer_max_tenure"]
    missing = [k for k in required if c.get(k) is None]
    if missing:
        raise ValueError("User definitions required before benchmark: " + ", ".join(missing))
    if c["positive_label_meaning"] not in {"churn", "unverified_technical_class_1"}:
        raise ValueError("Declare verified churn or unverified technical positive class")
    if c["new_customer_max_tenure"] != 0:
        raise ValueError("Confirmed IsNewCustomer definition is Tenure == 0")
    if len(c["algorithms"]) != 5 or len(set(c["algorithms"])) != 5:
        raise ValueError("Exactly five distinct confirmed algorithms are required")
    if set(c["scenarios"]) != {"P0", "P1", "P2", "P3"}:
        raise ValueError("Define P0, P1, P2, P3 explicitly")
    for s in c["scenarios"].values():
        if set(s) != {"sampling", "class_weight", "log1p"}:
            raise ValueError("Each scenario needs sampling, class_weight, log1p")
        if not isinstance(s["class_weight"], bool) or not isinstance(s["log1p"], bool):
            raise ValueError("class_weight and log1p must be boolean")
        if s["sampling"] not in {"none", "smotenc", "random_over"}:
            raise ValueError("Unsupported sampling strategy")
        if s["sampling"] != "none" and s["class_weight"]:
            raise ValueError("Do not combine resampling and class weights")
    if c.get("bootstrap_iterations") != 1000:
        raise ValueError("Research run requires exactly 1000 bootstrap replicates")


def model_and_space(name, weighted, y):
    weight = "balanced" if weighted else None
    if name == "logistic_regression":
        return LogisticRegression(max_iter=3000, class_weight=weight, random_state=42), {"model__C": np.logspace(-3, 2, 20)}
    if name in {"random_forest", "extra_trees"}:
        cls = RandomForestClassifier if name == "random_forest" else ExtraTreesClassifier
        return cls(n_estimators=150, class_weight=weight, random_state=42, n_jobs=1), {
            "model__max_depth": [None, 4, 8, 12], "model__min_samples_leaf": [1, 2, 4, 8],
            "model__max_features": ["sqrt", .7, 1.]}
    if name == "hist_gradient_boosting":
        return HistGradientBoostingClassifier(class_weight=weight, random_state=42), {
            "model__learning_rate": [.03, .05, .1], "model__max_leaf_nodes": [7, 15, 31],
            "model__l2_regularization": [0., 1., 10.]}
    if name == "xgboost":
        return FoldWeightedXGB(n_estimators=150, max_depth=3, learning_rate=.05,
                               balanced=weighted, random_state=42, n_jobs=1,
                               eval_metric="logloss", tree_method="hist"), {
            "model__max_depth": [2, 3, 5, 7], "model__learning_rate": [.02, .05, .1],
            "model__subsample": [.7, 1.], "model__colsample_bytree": [.7, 1.]}
    raise ValueError(f"Unsupported confirmed algorithm {name}; extend registry first")


class FoldWeightedXGB(XGBClassifier):
    def __init__(self, balanced=False, **kwargs):
        self.balanced = balanced
        super().__init__(**kwargs)

    def get_xgb_params(self):
        params = super().get_xgb_params()
        params.pop("balanced", None)
        return params

    def fit(self, X, y, **kwargs):
        if self.balanced:
            kwargs["sample_weight"] = compute_sample_weight("balanced", y)
        self.fold_class_counts_ = {int(k): int((np.asarray(y) == k).sum()) for k in (0, 1)}
        return super().fit(X, y, **kwargs)


def prepare(c):
    validate_config(c)
    if Path("reports/metrics_test.json").exists():
        raise ValueError("Final test already evaluated; preserve existing run")
    d, audit = load_clean(c["data_path"], c["sheet"])
    audit.update(source_sha256=fingerprint(c["data_path"]), sheet=c["sheet"],
                 label_source=c["label_source"], positive_label_meaning=c["positive_label_meaning"])
    write_json("reports/data_audit.json", audit)
    X, y = d.drop(columns=["Churn", "CustomerID"]), d.Churn
    train, test = train_test_split(np.arange(len(d)), stratify=y, test_size=.2, random_state=42)
    # Row indices are internal references; never export CustomerID to result tables.
    bundle = {"X_train": X.iloc[train], "y_train": y.iloc[train], "X_test": X.iloc[test],
              "y_test": y.iloc[test], "source_sha256": audit["source_sha256"], "config": c}
    joblib.dump(bundle, "models/split.joblib")
    write_json("reports/split_manifest.json", {"train_rows": len(train), "test_rows": len(test),
               "random_state": 42, "test_policy": "sealed until finalize", "source_sha256": audit["source_sha256"]})
    # Ordinal and binary variables are categorical for association tests.
    eda_X = X.iloc[train].copy()
    for col in c["categorical_columns"]:
        eda_X[col] = eda_X[col].astype("string")
    eda(eda_X, y.iloc[train], Path("reports/eda"))


def get_bundle(c):
    b = joblib.load("models/split.joblib")
    if b["config"] != c or b["source_sha256"] != fingerprint(c["data_path"]):
        raise ValueError("Data/config changed; run prepare again")
    return b


def benchmark(c):
    validate_config(c)
    if Path("reports/metrics_test.json").exists():
        raise ValueError("Final test already evaluated; preserve existing run")
    if not Path("reports/smoke.json").exists():
        raise ValueError("Run smoke successfully before benchmark")
    smoke_report = json.loads(Path("reports/smoke.json").read_text(encoding="utf-8"))
    if (smoke_report.get("config") != c or
        smoke_report.get("source_sha256") != fingerprint(c["data_path"]) or
        smoke_report.get("research_pipeline") != "passed_all_confirmed_combinations"):
        raise ValueError("Run smoke with confirmed research config and current dataset before benchmark")
    b = get_bundle(c)
    X, y = b["X_train"], b["y_train"]
    cv = StratifiedKFold(3, shuffle=True, random_state=42)
    rows = []
    fold_rows = []
    write_json("reports/cv_manifest.json", {"scope": "train", "folds": [
        {"fold": i, "fit_row_references": X.index[fit].tolist(),
         "validation_row_references": X.index[val].tolist(),
         "fit_class_counts": y.iloc[fit].value_counts().to_dict(),
         "validation_class_counts": y.iloc[val].value_counts().to_dict()}
        for i, (fit, val) in enumerate(cv.split(X, y))]})
    for algorithm in c["algorithms"] + ["dummy_most_frequent", "dummy_prior"]:
        scenarios = c["scenarios"] if not algorithm.startswith("dummy") else {"baseline": {"sampling": "none", "log1p": False, "class_weight": False}}
        for name, scenario in scenarios.items():
            estimator = (DummyClassifier(strategy=algorithm.removeprefix("dummy_"), random_state=42)
                         if algorithm.startswith("dummy") else model_and_space(algorithm, scenario["class_weight"], y)[0])
            pipe = build_pipeline(X, estimator, c, scenario)
            scores = cross_validate(pipe, X, y, cv=cv, scoring=SCORERS, n_jobs=c["n_jobs"], error_score="raise")
            row = {"algorithm": algorithm, "scenario": name, "scope": "train_cv"}
            for metric in SCORERS:
                values = scores["test_"+metric] * (-1 if metric == "brier" else 1)
                row[metric] = values.mean()
                row[metric+"_std"] = values.std()
            rows.append(row)
            for fold in range(3):
                fold_rows.append({"algorithm": algorithm, "scenario": name, "fold": fold, "scope": "train_cv",
                                  **{metric: float(scores["test_"+metric][fold]) * (-1 if metric == "brier" else 1)
                                     for metric in SCORERS}})
            pd.DataFrame(rows).to_csv("reports/benchmark_train_cv.csv", index=False)
            pd.DataFrame(fold_rows).to_csv("reports/benchmark_folds_train_cv.csv", index=False)
            print(algorithm, name, row["average_precision"], flush=True)
    table = pd.DataFrame(rows)
    best = table[~table.algorithm.str.startswith("dummy")].sort_values(
        ["average_precision", "roc_auc", "brier"], ascending=[False, False, True]).drop_duplicates("algorithm").head(2)
    tuned = []
    for row in best.itertuples():
        scenario = c["scenarios"][row.scenario]
        estimator, space = model_and_space(row.algorithm, scenario["class_weight"], y)
        search = RandomizedSearchCV(build_pipeline(X, estimator, c, scenario), space, n_iter=10,
                                    cv=cv, random_state=42, scoring=SCORERS, refit="average_precision",
                                    n_jobs=c["n_jobs"], error_score="raise")
        search.fit(X, y)
        pd.DataFrame(search.cv_results_).to_csv(f"reports/tuning_{row.algorithm}.csv", index=False)
        tuned.append((search.best_score_, row.algorithm, row.scenario, search.best_estimator_))
    tuned.sort(key=lambda item: item[0], reverse=True)
    _, name, scenario, winner = tuned[0]
    # Calibration choice uses only training CV, with calibration fitted inside each outer fold.
    calibrated = CalibratedClassifierCV(clone(winner), method="sigmoid", cv=StratifiedKFold(3, shuffle=True, random_state=42))
    choices = []
    for candidate in [winner, calibrated]:
        p = cross_val_predict(clone(candidate), X, y, cv=cv, method="predict_proba", n_jobs=c["n_jobs"])[:, 1]
        choices.append((metrics(y, p), p, candidate))
    use_calibration = choices[1][0]["brier"] < choices[0][0]["brier"]
    m, p, final = choices[int(use_calibration)]
    precision, recall, thresholds = precision_recall_curve(y, p)
    f1 = 2*precision[:-1]*recall[:-1] / np.maximum(precision[:-1]+recall[:-1], 1e-15)
    threshold = float(thresholds[np.argmax(f1)])
    final.fit(X, y)
    # Retain uncalibrated base for faithful coefficient/tree interpretation.
    winner.fit(X, y)
    artifact = {"pipeline": final, "base_pipeline": winner, "algorithm": name, "scenario": scenario,
                "threshold": threshold, "calibrated": bool(use_calibration), "config": c,
                "source_sha256": b["source_sha256"], "oof_metrics": m}
    joblib.dump(artifact, "models/trained.joblib")
    export_predictions(y, p, threshold, "oof", "reports/predictions_oof.csv")
    bootstrap_risks(y, p, threshold, 1000).to_csv("reports/risk_oof.csv", index=False)
    write_json("reports/selection.json", {"algorithm": name, "scenario": scenario, "threshold": threshold,
               "sigmoid_selected": bool(use_calibration), "uncalibrated_oof": choices[0][0],
               "calibrated_oof": choices[1][0], "scope": "train_oof",
               "limitation": "Hyperparameters and calibration selected on same training dataset; OOF metrics are selection diagnostics, not unbiased final performance."})
    plot_calibration(y, [("uncalibrated OOF", choices[0][1]), ("sigmoid OOF", choices[1][1])], "reports/calibration_oof.png")


def export_predictions(y, p, threshold, scope, path):
    scores = score_probability(p)
    pd.DataFrame({"row_reference": y.index, "scope": scope, "observed_label": y.to_numpy(),
                  "probability": p, "prediction": (p >= threshold).astype(int), "score": scores,
                  "risk_group": np.where(scores <= 3, "low", np.where(scores <= 6, "medium", "high"))}).to_csv(path, index=False)


def plot_calibration(y, curves, path):
    fig, ax = plt.subplots()
    for name, p in curves:
        fraction, mean = calibration_curve(y, p, n_bins=10, strategy="quantile")
        ax.plot(mean, fraction, "o-", label=name)
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set(xlabel="Mean predicted P(label=1)", ylabel="Observed label=1 fraction")
    ax.legend()
    fig.savefig(path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def transformed(pipe, X):
    z = pipe.named_steps["features"].transform(X)
    z = pipe.named_steps["pre"].transform(z)
    return pipe.named_steps["onehot"].transform(z)


def explanations(base, X, y, c):
    importance = permutation_importance(base, X, y, scoring="average_precision", n_repeats=5, random_state=42, n_jobs=c["n_jobs"])
    pd.DataFrame({"feature": X.columns, "importance": importance.importances_mean,
                  "std": importance.importances_std}).to_csv("reports/permutation_train.csv", index=False)
    # Always fit LR on training data for an interpretable reference.
    lr, _ = model_and_space("logistic_regression", False, y)
    lr_pipe = build_pipeline(X, lr, c, {"sampling": "none", "log1p": True})
    lr_pipe.fit(X, y)
    coef = lr_pipe.named_steps["model"].coef_[0]
    pd.DataFrame({"feature": lr_pipe.named_steps["onehot"].get_feature_names_out(),
                  "coefficient_log_odds": coef, "odds_ratio": np.exp(coef)}).to_csv("reports/lr_coefficients_train.csv", index=False)
    write_json("reports/lr_interpretation.json", {"intercept_log_odds": float(lr_pipe.named_steps["model"].intercept_[0]),
               "notes": "Reference LR, not necessarily selected model. Numeric odds ratios per training SD of transformed feature. Full one-hot, regularized; coefficients not causal or p-values."})
    model = base.named_steps["model"]
    tree_base = base
    if isinstance(model, (LogisticRegression, HistGradientBoostingClassifier)):
        # Explicit surrogate reference, never presented as explanation of the selected model.
        tree_base = build_pipeline(X, RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=1), c,
                                   {"sampling": "none", "log1p": True})
        tree_base.fit(X, y)
        model = tree_base.named_steps["model"]
        reference = "reference_random_forest_on_train"
    else:
        reference = "selected_uncalibrated_tree"
    import shap
    small = X.sample(min(150, len(X)), random_state=42)
    z = transformed(tree_base, small)
    explainer = shap.TreeExplainer(model)
    values = np.asarray(explainer.shap_values(z))
    if values.ndim == 3:
        values = values[:, :, 1]
    if isinstance(model, XGBClassifier):
        np.testing.assert_allclose(values.sum(axis=1) + explainer.expected_value,
                                   model.predict(z, output_margin=True), atol=1e-4)
    else:
        np.testing.assert_allclose(values.sum(axis=1) + explainer.expected_value[1],
                                   model.predict_proba(z)[:, 1], atol=1e-5)
    names = tree_base.named_steps["onehot"].get_feature_names_out()
    pd.DataFrame({"feature": names, "mean_abs_shap": np.abs(values).mean(axis=0)}).to_csv("reports/shap_train.csv", index=False)
    write_json("reports/shap_scale.json", {"scope": "train", "model": reference,
               "scale": "log_odds" if isinstance(model, XGBClassifier) else "probability",
               "additivity_check": "passed",
               "note": "Explains uncalibrated base/reference tree, not the sigmoid-calibrated probability. Values aggregate transformed features."})


def finalize(c):
    if Path("reports/metrics_test.json").exists():
        raise ValueError("Final test already evaluated. Preserve it; do not repeatedly optimize on test.")
    b = get_bundle(c)
    a = joblib.load("models/trained.joblib")
    if a["config"] != c or a["source_sha256"] != b["source_sha256"]:
        raise ValueError("Stale trained artifact")
    # Finish training-only interpretation before opening the holdout.
    explanations(a["base_pipeline"], b["X_train"], b["y_train"], c)
    p = a["pipeline"].predict_proba(b["X_test"])[:, 1]
    y = b["y_test"]
    write_json("reports/metrics_test.json", dict(metrics(y, p), scope="test", threshold=a["threshold"]))
    export_predictions(y, p, a["threshold"], "test", "reports/predictions_test.csv")
    bootstrap_risks(y, p, a["threshold"], 1000).to_csv("reports/risk_test.csv", index=False)
    plot_calibration(y, [("final test", p)], "reports/calibration_test.png")
    joblib.dump(a["pipeline"], "models/churn_pipeline.joblib")
    # Check persisted estimator predictions exactly reproduce evaluation probabilities.
    np.testing.assert_allclose(joblib.load("models/churn_pipeline.joblib").predict_proba(b["X_test"])[:, 1], p)
    write_json("models/metadata.json", {"python": sys.version, "platform": platform.platform(),
               "versions": {k: importlib.metadata.version(k) for k in PACKAGES},
               "input_columns": list(b["X_train"].columns), "input_dtypes": b["X_train"].dtypes.astype(str).to_dict(),
               "threshold": a["threshold"], "score_rule": "min(10, 1 + floor(10*p))", "risk_groups": RISK_GROUPS,
               "algorithm": a["algorithm"], "scenario": a["scenario"],
               "base_model_hyperparameters": a["base_pipeline"].named_steps["model"].get_params(),
               "source_sha256": a["source_sha256"], "config": c, "random_state": 42,
               "calibrated": a["calibrated"], "prediction_scopes": ["oof", "test"],
               "target_semantics": c["positive_label_meaning"], "label_semantics_verified": c["label_semantics_verified"],
               "deployment_input": "Cleaned feature-only DataFrame; normalize aliases with src.data.ALIASES; no CustomerID or Churn",
               "bootstrap": "1000 stratified replicates; conditional on fixed fitted model and class prevalence; percentile 95% intervals"})
    from .reporting import completed_report
    completed_report()

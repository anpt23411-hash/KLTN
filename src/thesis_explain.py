"""Validation-fold importance, real-background SHAP and CPU timing."""
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.base import clone
from sklearn.inspection import permutation_importance
from .data import write_json
from .evaluation import positive_probability
from .thesis_preprocessing import build_thesis_pipeline, NOMINAL
from .thesis_visuals import save


def transform(pipe, X):
    return pipe.named_steps["finish"].transform(pipe.named_steps["prepare"].transform(X))


def explain(a, X, y, c):
    from .thesis import cv, model
    r = Path(c["report_dir"])
    r.mkdir(parents=True, exist_ok=True)
    pipe = a["base_pipeline"]
    parts = []
    for fold, (tr, va) in enumerate(cv(c).split(X, y)):
        fitted = clone(a["pipeline"]).fit(X.iloc[tr], y.iloc[tr])
        result = permutation_importance(fitted, X.iloc[va], y.iloc[va], scoring="average_precision",
                                        n_repeats=5, random_state=c["seed"], n_jobs=1)
        parts.append(pd.DataFrame({"feature": X.columns, "fold": fold, "mean_ap_decrease": result.importances_mean,
                                   "within_fold_std": result.importances_std, "scope": "train_validation_fold"}))
        print("Validation permutation importance fold", fold, flush=True)
    table = pd.concat(parts)
    table.to_csv(r/"permutation_folds.csv", index=False)
    summary = table.groupby("feature").mean_ap_decrease.agg(["mean", "std"]).sort_values("mean", ascending=False)
    summary.to_csv(r/"permutation_importance.csv")
    fig, ax = plt.subplots(figsize=(8, 6))
    summary["mean"].sort_values().plot.barh(ax=ax, xerr=summary["std"].sort_index().reindex(summary["mean"].sort_values().index))
    ax.set(xlabel="Validation AP decrease (fold SD is not a CI)")
    save(fig, r/"figures/permutation_importance.png")
    lr = build_thesis_pipeline(model("logistic_regression")[0], "logistic_regression", c["scenarios"]["P0"], a["features"]["features"])
    lr.fit(X, y)
    coef = lr.named_steps["model"].coef_[0]
    pd.DataFrame({"feature": lr.named_steps["finish"].get_feature_names_out(), "coefficient_log_odds": coef,
                  "odds_ratio": np.exp(coef)}).to_csv(r/"lr_coefficients.csv", index=False)
    write_json(r/"lr_reference.json", {"reference_categories": lr.named_steps["prepare"].categories_,
               "scaled_columns": lr.named_steps["finish"].scaled_, "log_columns": lr.named_steps["prepare"].log_columns_,
               "scope": "reference_LR_fit_on_train", "note": "First category per nominal field omitted; conditional regularized odds ratios, not causal effects"})
    names = list(pipe.named_steps["finish"].get_feature_names_out())
    estimator = pipe.named_steps["model"]
    if hasattr(estimator, "feature_importances_"):
        pd.DataFrame({"feature": names, "importance": estimator.feature_importances_}).to_csv(r/"intrinsic_importance.csv", index=False)
    # Explain the actual selected tree; LR uses a transparent reference RF only if selected.
    if a["algorithm"] == "logistic_regression":
        tree = build_thesis_pipeline(model("random_forest")[0], "random_forest", c["scenarios"]["P0"], a["features"]["features"])
        tree.fit(X, y)
        explained_model, model_name = tree, "reference_random_forest_not_selected_LR"
    else:
        explained_model, model_name = pipe, a["algorithm"]
    import shap
    sample = X.sample(min(150, len(X)), random_state=c["seed"])
    background = X.sample(min(100, len(X)), random_state=c["seed"])
    z, bg = transform(explained_model, sample), transform(explained_model, background)
    est = explained_model.named_steps["model"]
    background_description = "100 real train observations, never synthetic"
    explanation_method = "TreeExplainer_interventional"
    try:
        explainer = shap.TreeExplainer(est, data=bg, feature_perturbation="interventional", model_output="raw")
        values = np.asarray(explainer.shap_values(z, check_additivity=True))
        base = explainer.expected_value
    except shap.utils._exceptions.ExplainerError as error:
        write_json(r/"shap_interventional_failure.json", {"error": str(error), "action": "Use a compatible explainer and independently verify additivity; never disable the check"})
        if "sample" not in explained_model.named_steps:
            explainer = shap.TreeExplainer(est, feature_perturbation="tree_path_dependent", model_output="raw")
            values = np.asarray(explainer.shap_values(z, check_additivity=True))
            base = explainer.expected_value
            explanation_method = "TreeExplainer_tree_path_dependent"
            background_description = "Training tree-node path frequencies; real training observations, no sampler in selected pipeline. Explicit 100-row background rejected after additivity failure."
        else:
            output_function = (lambda v: est.predict(v, output_margin=True)) if model_name == "xgboost" else (
                est.decision_function if model_name == "hist_gradient_boosting" else lambda v: est.predict_proba(v)[:, 1])
            explainer = shap.PermutationExplainer(output_function, bg, seed=c["seed"])
            explanation = explainer(z, max_evals=2*z.shape[1]+1)
            values, base = explanation.values, explanation.base_values
            explanation_method = "PermutationExplainer_real_background"
    if values.ndim == 3:
        values, base = values[:, :, 1], base[1]
    scale = "log_odds" if model_name in {"hist_gradient_boosting", "xgboost"} else "probability"
    output = (est.predict(z, output_margin=True) if model_name == "xgboost" else
              est.decision_function(z) if model_name == "hist_gradient_boosting" else est.predict_proba(z)[:, 1])
    np.testing.assert_allclose(values.sum(axis=1)+base, output, atol=1e-4)
    names = list(explained_model.named_steps["finish"].get_feature_names_out())
    groups = {}
    for i, name in enumerate(names):
        original = next((c for c in NOMINAL if name.startswith(c+"_")), name)
        groups.setdefault(original, []).append(i)
    grouped = np.column_stack([values[:, idx].sum(axis=1) for idx in groups.values()])
    shap_table = pd.DataFrame(grouped, columns=list(groups), index=sample.index)
    shap_table.index.name = "row_reference"
    shap_table.to_csv(r/"shap_local_contributions.csv")
    importance = shap_table.abs().mean().sort_values(ascending=False)
    importance.rename("mean_abs_grouped_shap").to_csv(r/"shap_grouped_importance.csv")
    fig, ax = plt.subplots(figsize=(8, 6))
    importance.sort_values().plot.barh(ax=ax)
    ax.set(xlabel=f"mean(abs(sum of grouped SHAP)) [{scale}]")
    save(fig, r/"figures/shap_grouped_bar.png")
    shap.summary_plot(values, z, feature_names=names, show=False, max_display=18)
    plt.gca().set_xlabel(f"SHAP contribution [{scale}]; base model output")
    save(plt.gcf(), r/"figures/shap_beeswarm.png")
    # Representatives selected by predicted probability, without inspecting their labels.
    probabilities = positive_probability(a["pipeline"], sample)
    order = np.argsort(probabilities)
    representatives = [order[0], order[len(order)//2], order[-1]]
    for name, i in zip(["low", "middle", "high"], representatives):
        e = shap.Explanation(values=grouped[i], base_values=float(np.asarray(base).ravel()[0]), feature_names=list(groups))
        shap.plots.waterfall(e, show=False, max_display=12)
        plt.gca().set_xlabel(f"Base model output [{scale}]; train example row {sample.index[i]}")
        save(plt.gcf(), r/f"figures/shap_waterfall_{name}.png")
    pd.DataFrame({"row_reference": sample.index, "base_value": float(np.asarray(base).ravel()[0]), "explained_output": output,
                  "final_pipeline_probability": probabilities, "scope": "in_sample_explanation_not_evaluation"}).to_csv(r/"shap_prediction_context.csv", index=False)
    write_json(r/"shap_metadata.json", {"model": model_name, "scale": scale, "background": background_description,
               "explainer": explanation_method,
               "background_row_references": background.index.tolist() if explanation_method != "TreeExplainer_tree_path_dependent" else [], "explained_rows": sample.index.tolist(), "seed": c["seed"],
               "scope": "in_sample_explanation_not_evaluation", "additivity": "passed", "grouping": "sum one-hot contributions per row BEFORE mean absolute value",
               "calibrated_pipeline": bool(a["calibrated"]), "note": "SHAP explains base tree output; does not decompose a sigmoid-calibrated probability"})


def refresh_local_figure_labels(report_dir):
    """Re-render saved explanations with explicit units; never fit or evaluate a model."""
    import json
    import shap
    r = Path(report_dir)
    metadata = json.loads((r/"shap_metadata.json").read_text())
    local = pd.read_csv(r/"shap_local_contributions.csv", index_col="row_reference")
    context = pd.read_csv(r/"shap_prediction_context.csv").set_index("row_reference").loc[local.index]
    order = np.argsort(context.final_pipeline_probability.to_numpy())
    for name, i in zip(["low", "middle", "high"], [order[0], order[len(order)//2], order[-1]]):
        explanation = shap.Explanation(values=local.iloc[i].to_numpy(), base_values=float(context.base_value.iloc[i]), feature_names=list(local))
        shap.plots.waterfall(explanation, show=False, max_display=12)
        plt.gca().set_xlabel(f"Base model output [{metadata['scale']}]; train example row {local.index[i]}")
        save(plt.gcf(), r/f"figures/shap_waterfall_{name}.png")


def operational_timing(a, X, y, c):
    rows = []
    for i in range(5):
        candidate = clone(a["pipeline"])
        start = time.perf_counter()
        candidate.fit(X, y)
        rows.append(dict(operation="fit", repetition=i, seconds=time.perf_counter()-start))
        start = time.perf_counter()
        candidate.predict_proba(X)
        rows.append(dict(operation="batch_predict", repetition=i, seconds=time.perf_counter()-start))
    for _ in range(10):
        a["pipeline"].predict_proba(X.iloc[:1])
    for i in range(200):
        start = time.perf_counter()
        a["pipeline"].predict_proba(X.iloc[:1])
        rows.append(dict(operation="single_predict", repetition=i, seconds=time.perf_counter()-start))
    t = pd.DataFrame(rows)
    r = Path(c["report_dir"])
    t.to_csv(r/"operational_timing_draws.csv", index=False)
    t.groupby("operation").seconds.agg(count="size", median="median", q1=lambda v: v.quantile(.25),
                                       q3=lambda v: v.quantile(.75), p95=lambda v: v.quantile(.95)).to_csv(r/"operational_timing.csv")

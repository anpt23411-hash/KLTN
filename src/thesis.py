"""Reproducible ML-only thesis experiment, isolated from the earlier pilot."""
import argparse
import importlib.metadata
import json
import platform
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.calibration import CalibratedClassifierCV
from sklearn.dummy import DummyClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import StratifiedKFold, RepeatedStratifiedKFold, train_test_split, RandomizedSearchCV
from sklearn.inspection import permutation_importance
from sklearn.metrics import get_scorer

from .data import load_clean, write_json, fingerprint
from .eda import eda
from .experiment import model_and_space, PACKAGES
from .thesis_preprocessing import build_thesis_pipeline, missing_association, ratios, NOMINAL, SENSITIVE
from .evaluation import evaluate, positive_probability, calibration_bins, choose_threshold, prediction_table, bootstrap, figures


def locations(c):
    r, m = Path(c["report_dir"]), Path(c["model_dir"])
    r.mkdir(parents=True, exist_ok=True)
    m.mkdir(parents=True, exist_ok=True)
    return r, m


def model(name, weighted=False):
    if name == "decision_tree":
        return DecisionTreeClassifier(class_weight="balanced" if weighted else None, random_state=42), {
            "model__max_depth": [None, 3, 5, 8, 12], "model__min_samples_split": [2, 5, 10],
            "model__min_samples_leaf": [1, 2, 4, 8], "model__criterion": ["gini", "entropy"]}
    estimator, space = model_and_space(name, weighted, pd.Series([0, 1]))
    if name == "random_forest":
        space.update(model__n_estimators=[100, 150, 250], model__min_samples_split=[2, 5, 10])
    elif name == "hist_gradient_boosting":
        space.update(model__max_iter=[100, 150, 200], model__max_depth=[None, 3, 6], model__min_samples_leaf=[10, 20, 40])
    elif name == "xgboost":
        space.update(model__n_estimators=[100, 150, 250], model__reg_lambda=[1., 5., 10.])
    return estimator, space


def bundle(c):
    _, m = locations(c)
    b = joblib.load(m/"split.joblib")
    if b["config"] != c or b["sha256"] != fingerprint(c["data_path"]):
        raise ValueError("Config/data changed: use a new run directory and prepare")
    return b


def prepare(c):
    r, m = locations(c)
    if (m/"split.joblib").exists():
        bundle(c)
        print("Existing identical split reused", flush=True)
        return
    d, audit = load_clean(c["data_path"], c["sheet"])
    tr, te = train_test_split(np.arange(len(d)), test_size=.2, stratify=d.Churn, random_state=c["seed"])
    assert not set(d.iloc[tr].CustomerID) & set(d.iloc[te].CustomerID)
    X, y = d.drop(columns=["Churn", "CustomerID"]), d.Churn
    b = dict(X_train=X.iloc[tr], y_train=y.iloc[tr], X_holdout=X.iloc[te], y_holdout=y.iloc[te],
             config=c, sha256=fingerprint(c["data_path"]))
    joblib.dump(b, m/"split.joblib")
    write_json(r/"config_snapshot.json", c)
    write_json(r/"data_audit.json", dict(audit, raw_sha256=b["sha256"],
               raw_missing=int(pd.read_excel(c["data_path"], sheet_name=c["sheet"]).isna().sum().sum()),
               rows_with_missing=int(d.isna().any(axis=1).sum()), max_missing_per_row=int(d.isna().sum(axis=1).max()),
               id_overlap=0, alias_equivalence="Mobile/Mobile Phone category merge remains an explicit assumption"))
    write_json(r/"split_manifest.json", {"train_rows": len(tr), "holdout_rows": len(te),
               "train_row_references": b["X_train"].index.tolist(), "holdout_row_references": b["X_holdout"].index.tolist(),
               "train_class_counts": b["y_train"].value_counts().to_dict(), "holdout_class_counts": b["y_holdout"].value_counts().to_dict(),
               "holdout_previously_observed": True, "test_not_used_for_selection": True})
    X, y = b["X_train"], b["y_train"]
    ex = ratios(X)
    for col in NOMINAL + ["Complain", "CityTier", "SatisfactionScore"]:
        ex[col] = ex[col].astype("string")
    eda(ex, y, r/"eda")
    missing_association(X, y).to_csv(r/"eda/missing_association_train.csv", index=False)
    X.median(numeric_only=True).to_csv(r/"eda/medians_train.csv")
    from .thesis_visuals import eda_figures
    eda_figures(X, y, r/"eda")
    write_json(r/"cv_manifest.json", {"seed": c["seed"], "scope": "train", "folds": [
        dict(fold=i, train_row_references=X.index[a].tolist(), validation_row_references=X.index[b].tolist())
        for i, (a, b) in enumerate(cv(c).split(X, y))]})
    print("Prepared real data and training EDA", len(tr), len(te), flush=True)


def cv(c, repeated=False):
    if repeated:
        return RepeatedStratifiedKFold(n_splits=c["cv_folds"], n_repeats=c["cv_repeats"], random_state=c["seed"])
    return StratifiedKFold(c["cv_folds"], shuffle=True, random_state=c["seed"])


def run_cv(pipe, X, y, splits, scope="train_cv", oof=False):
    rows, predictions = [], np.full(len(y), np.nan)
    seen = np.zeros(len(y), dtype=int)
    for fold, (a, b) in enumerate(splits):
        fitted = clone(pipe)
        start = time.perf_counter()
        fitted.fit(X.iloc[a], y.iloc[a])
        fit_seconds = time.perf_counter()-start
        start = time.perf_counter()
        p = positive_probability(fitted, X.iloc[b])
        predict_seconds = time.perf_counter()-start
        rows.append(dict(fold=fold, scope=scope, fit_seconds=fit_seconds, predict_seconds=predict_seconds,
                         **evaluate(y.iloc[b], p)))
        if oof:
            predictions[b] = p
            seen[b] += 1
    if oof and not (seen == 1).all():
        raise ValueError("OOF requires an exact partition, not repeated CV")
    return pd.DataFrame(rows), predictions


def feature_study(c):
    r, _ = locations(c)
    b = bundle(c)
    X, y = b["X_train"], b["y_train"]
    definitions = {"A": {"flags": "none", "include_new": False},
                   "B": {"flags": "significant", "include_new": False},
                   "C": {"flags": "significant", "include_new": False, "ratio": "CashbackPerOrder"},
                   "D": {"flags": "significant", "include_new": False, "ratio": "CouponRate"},
                   "E": {"flags": "significant", "include_new": True, "tenure_threshold": c["tenure_threshold"]},
                   "F": {"flags": "significant", "include_new": False}}
    rows = []
    for name, settings in definitions.items():
        data = X.drop(columns=["HourSpendOnApp", "OrderCount", "CouponUsed"]) if name == "F" else X
        for algorithm in ["logistic_regression", "hist_gradient_boosting"]:
            pipe = build_thesis_pipeline(model(algorithm)[0], algorithm, c["scenarios"]["P0"], settings)
            scores, _ = run_cv(pipe, data, y, cv(c, repeated=True).split(data, y))
            scores["variant"], scores["algorithm"] = name, algorithm
            rows.append(scores)
            pd.concat(rows).to_csv(r/"feature_study_folds.csv", index=False)
            print("Feature study", name, algorithm, scores.average_precision.mean(), flush=True)
    table = pd.concat(rows).groupby(["variant", "algorithm"]).average_precision.agg(["mean", "std"]).reset_index()
    table.to_csv(r/"feature_study.csv", index=False)
    means = table.pivot(index="variant", columns="algorithm", values="mean")
    def keep(delta, minimum=.005):
        return bool(delta.max() >= minimum and delta.min() >= -.005)
    flags = keep(means.loc["B"]-means.loc["A"])
    selected = {"flags": "significant" if flags else "none", "include_new": keep(means.loc["E"]-means.loc["B"]),
                "tenure_threshold": c["tenure_threshold"], "ratio": []}
    for name, ratio in [("C", "CashbackPerOrder"), ("D", "CouponRate")]:
        if keep(means.loc[name]-means.loc["B"]):
            selected["ratio"].append(ratio)
    # F is evaluated as an ablation; retain all raw variables unless both models meet the predeclared rule.
    drop = ["HourSpendOnApp", "OrderCount", "CouponUsed"] if ((means.loc["F"]-means.loc["B"]) >= -.002).all() else []
    if drop and selected["ratio"]:
        drop = []  # A retained ratio needs its raw components.
    write_json(r/"feature_selection.json", {"features": selected, "drop_columns": drop,
               "basis": "training repeated 5x3 AP; fold-local FDR flag selection",
               "limitation": "Selection diagnostics on development data; no claim of independent feature-selection performance"})


def selected(c):
    r, _ = locations(c)
    s = json.loads((r/"feature_selection.json").read_text())
    b = bundle(c)
    return b["X_train"].drop(columns=s["drop_columns"]), b["y_train"], s


def smoke(c):
    r, _ = locations(c)
    X, y, s = selected(c)
    a, _ = train_test_split(np.arange(len(X)), train_size=240, stratify=y, random_state=c["seed"])
    import shap
    for algorithm in c["algorithms"]:
        for scenario in c["scenarios"].values():
            pipe = build_thesis_pipeline(model(algorithm, scenario["class_weight"])[0], algorithm, scenario, s["features"])
            pipe.fit(X.iloc[a], y.iloc[a])
            assert np.isfinite(positive_probability(pipe, X.iloc[a[:8]])).all()
        if algorithm != "logistic_regression":
            z = pipe.named_steps["finish"].transform(pipe.named_steps["prepare"].transform(X.iloc[a[:8]]))
            explainer = shap.TreeExplainer(pipe.named_steps["model"])
            vals = np.asarray(explainer.shap_values(z))
            expected = explainer.expected_value
            if vals.ndim == 3:
                vals, expected = vals[:, :, 1], expected[1]
            output = (pipe.named_steps["model"].predict(z, output_margin=True) if algorithm == "xgboost" else
                      pipe.named_steps["model"].decision_function(z) if algorithm == "hist_gradient_boosting" else
                      pipe.named_steps["model"].predict_proba(z)[:, 1])
            np.testing.assert_allclose(vals.sum(axis=1)+expected, output, atol=1e-4)
    write_json(r/"smoke.json", {"status": "passed", "rows": 240, "scope": "train_only",
               "all_20_pipelines": "passed", "all_four_tree_shap_additivity": "passed",
               "resources": json.loads(Path("reports/smoke.json").read_text()).get("resources", {}), "config": c})
    print("All 20 thesis pipelines and four tree SHAP compatibility checks passed", flush=True)


def benchmark(c):
    r, _ = locations(c)
    if json.loads((r/"smoke.json").read_text())["config"] != c:
        raise ValueError("Stale smoke")
    X, y, s = selected(c)
    allrows = []
    for algorithm in c["algorithms"] + ["dummy_most_frequent", "dummy_prior"]:
        scenarios = c["scenarios"] if not algorithm.startswith("dummy_") else {"baseline": {"sampling": "none", "class_weight": False}}
        for name, scenario in scenarios.items():
            estimator = (DummyClassifier(strategy=algorithm.removeprefix("dummy_"), random_state=c["seed"])
                         if algorithm.startswith("dummy_") else model(algorithm, scenario["class_weight"])[0])
            pipe = build_thesis_pipeline(estimator, algorithm, scenario, s["features"])
            scores, _ = run_cv(pipe, X, y, cv(c, True).split(X, y))
            scores["algorithm"], scores["scenario"] = algorithm, name
            allrows.append(scores)
            pd.concat(allrows).to_csv(r/"benchmark_repeated_folds.csv", index=False)
            print("Benchmark", algorithm, name, scores.average_precision.iloc[:5].mean(), flush=True)
    t = pd.concat(allrows)
    cols = list(evaluate([0, 1], [.1, .9]))+["fit_seconds", "predict_seconds"]
    for filename, data in [("benchmark", t[t.fold < 5]), ("imbalance_repeated", t)]:
        summary = data.groupby(["algorithm", "scenario"])[cols].agg(["mean", "std"])
        summary.columns = ["_".join(x) for x in summary.columns]
        summary.reset_index().to_csv(r/f"{filename}.csv", index=False)
    # Paired descriptive deltas, never interpret 15 overlapping folds as independent observations.
    paired = t.pivot(index=["algorithm", "fold"], columns="scenario", values="average_precision")
    for p in ["P1", "P2", "P3"]:
        paired[p+"_minus_P0"] = paired[p]-paired.P0
    paired.to_csv(r/"paired_imbalance_deltas.csv")


def tune(c):
    r, m = locations(c)
    X, y, s = selected(c)
    table = pd.read_csv(r/"benchmark.csv")
    folds = pd.read_csv(r/"benchmark_repeated_folds.csv")
    chosen = []
    for algorithm in c["algorithms"]:
        subset = table[table.algorithm.eq(algorithm)].sort_values("average_precision_mean", ascending=False)
        best = subset.iloc[0]
        for scenario in c["scenarios"]:
            row = subset[subset.scenario.eq(scenario)].iloc[0]
            pair = folds[folds.algorithm.eq(algorithm)].pivot(index="fold", columns="scenario", values="average_precision")
            close = best.average_precision_mean-row.average_precision_mean <= max(c["ap_tolerance"], float((pair[best.scenario]-pair[scenario]).std()))
            if close and row.brier_mean <= best.brier_mean+c["brier_tolerance"]:
                best = row
                break
        chosen.append(best)
    chosen = pd.DataFrame(chosen).sort_values("average_precision_mean", ascending=False).head(2)
    chosen.to_csv(r/"tuning_shortlist.csv", index=False)
    candidates, post = [], []
    for row in chosen.itertuples():
        scenario = c["scenarios"][row.scenario]
        estimator, space = model(row.algorithm, scenario["class_weight"])
        if scenario["sampling"] == "smotenc":
            space["sample__k_neighbors"] = [3, 5, 7]
        search = RandomizedSearchCV(build_thesis_pipeline(estimator, row.algorithm, scenario, s["features"]), space,
                                    n_iter=c["tuning_iterations"], cv=StratifiedKFold(c["tuning_folds"], shuffle=True, random_state=c["seed"]),
                                    scoring={"ap": "average_precision", "roc_auc": "roc_auc", "brier": "neg_brier_score"},
                                    refit="ap", random_state=c["seed"], n_jobs=1, error_score="raise")
        start = time.perf_counter()
        search.fit(X, y)
        elapsed = time.perf_counter()-start
        pd.DataFrame(search.cv_results_).to_csv(r/f"tuning_{row.algorithm}.csv", index=False)
        for version, pipe in [("untuned", build_thesis_pipeline(estimator, row.algorithm, scenario, s["features"])), ("tuned", search.best_estimator_)]:
            scores, p = run_cv(pipe, X, y, cv(c).split(X, y), oof=True)
            scores["algorithm"], scores["scenario"], scores["version"] = row.algorithm, row.scenario, version
            post.append(scores)
            values = evaluate(y, p)
            values["average_precision"] = scores.average_precision.mean()
            candidates.append(dict(algorithm=row.algorithm, scenario=row.scenario, version=version, metrics=values,
                                   pipe=pipe, p=p, search_seconds=elapsed, params=search.best_params_ if version == "tuned" else {}))
        print("Tuning finished", row.algorithm, row.scenario, flush=True)
    pd.concat(post).to_csv(r/"post_tuning_folds.csv", index=False)
    # Retain the original benchmark candidate: random search is not guaranteed to improve it.
    candidates.sort(key=lambda x: x["metrics"]["average_precision"], reverse=True)
    best = candidates[0]
    for item in sorted(candidates, key=lambda x: x["metrics"]["brier"]):
        if (best["metrics"]["average_precision"]-item["metrics"]["average_precision"] <= c["ap_tolerance"] and
            item["metrics"]["brier"] < best["metrics"]["brier"] and item["metrics"]["ece"] <= best["metrics"]["ece"]):
            best = item
    pipe, p = best["pipe"], best["p"]
    calibrated = CalibratedClassifierCV(clone(pipe), method="sigmoid", cv=StratifiedKFold(3, shuffle=True, random_state=c["seed"]))
    cal_scores, cp = run_cv(calibrated, X, y, cv(c).split(X, y), oof=True)
    raw_values, cal_values = evaluate(y, p), evaluate(y, cp)
    use_cal = (cal_scores.average_precision.mean() >= best["metrics"]["average_precision"]-c["ap_tolerance"] and
               cal_values["brier"] < raw_values["brier"] and cal_values["ece"] < raw_values["ece"])
    final, probs = (calibrated, cp) if use_cal else (pipe, p)
    threshold, threshold_table = choose_threshold(y, probs)
    threshold_table.to_csv(r/"threshold_sweep_oof.csv", index=False)
    for name, values in [("uncalibrated", p), ("sigmoid", cp)]:
        calibration_bins(y, values).to_csv(r/f"calibration_bins_{name}_oof.csv", index=False)
    final.fit(X, y)
    pipe.fit(X, y)
    artifact = dict(pipeline=final, base_pipeline=pipe, algorithm=best["algorithm"], scenario=best["scenario"],
                    version=best["version"], threshold=threshold, calibrated=bool(use_cal), config=c, features=s,
                    source_sha256=bundle(c)["sha256"], params=best["params"])
    joblib.dump(artifact, m/"trained.joblib")
    write_json(r/"selection.json", {k: artifact[k] for k in ["algorithm", "scenario", "version", "threshold", "calibrated", "features", "params"]} |
               {"raw_oof": raw_values, "sigmoid_oof": cal_values, "oof_selection_bias": True,
                "candidates": [{k: v for k, v in item.items() if k not in {"pipe", "p"}} for item in candidates]})
    prediction_table(y, probs, threshold, c["risk_groups"], "oof").to_csv(r/"predictions_oof.csv", index=False)
    intervals, risk = bootstrap(y, probs, threshold, c["risk_groups"], c["bootstrap_iterations"], c["seed"])
    intervals.to_csv(r/"metrics_ci_oof.csv", index=False)
    risk.to_csv(r/"risk_oof.csv", index=False)
    figures(y, probs, threshold, r/"figures", "oof")
    from .thesis_visuals import calibration_comparison
    calibration_comparison(y, p, cp, r/"figures/calibration_comparison_oof.png")
    print("Selected and frozen", best["algorithm"], best["scenario"], best["version"], "sigmoid", use_cal, "threshold", threshold, flush=True)


def robustness(c):
    r, m = locations(c)
    a = joblib.load(m/"trained.joblib")
    X, y, s = selected(c)
    pipe = a["base_pipeline"]
    reduced = X.drop(columns=[col for col in SENSITIVE if col in X])
    # Rebuild all dependent features after dropping raw columns.
    spec = {**s["features"], "ratio": []}
    ablated = build_thesis_pipeline(clone(pipe.named_steps["model"]), a["algorithm"], c["scenarios"][a["scenario"]], spec)
    if "sample" in pipe.named_steps:
        ablated.set_params(sample__k_neighbors=pipe.named_steps["sample"].k_neighbors)
    rows = []
    for name, data, candidate in [("full", X, pipe), ("without_temporal_proxies", reduced, ablated)]:
        scores, _ = run_cv(candidate, data, y, cv(c, True).split(data, y))
        rows.append(scores.assign(variant=name))
    pd.concat(rows).to_csv(r/"sensitivity_folds.csv", index=False)
    # k study changes only sampler settings; not used to reopen final selection.
    study = []
    for scenario in ["P2", "P3"]:
        for k in [3, 5, 7]:
            setting = {**c["scenarios"][scenario], "k_neighbors": k}
            candidate = build_thesis_pipeline(model(a["algorithm"])[0], a["algorithm"], setting, s["features"])
            scores, _ = run_cv(candidate, X, y, cv(c).split(X, y))
            study.append(scores.assign(scenario=scenario, k_neighbors=k))
    pd.concat(study).to_csv(r/"smotenc_k_study.csv", index=False)
    print("Training-only sensitivity and SMOTE-NC k study completed", flush=True)


def finalize(c):
    r, m = locations(c)
    if (r/"metrics_holdout.json").exists():
        raise ValueError("Holdout already evaluated for this run; use saved predictions for reporting")
    b = bundle(c)
    a = joblib.load(m/"trained.joblib")
    from .thesis_explain import explain, operational_timing
    X, y, s = selected(c)
    explain(a, X, y, c)
    operational_timing(a, X, y, c)
    # All model decisions above are frozen before accessing holdout labels/probabilities.
    holdout = b["X_holdout"].drop(columns=s["drop_columns"])
    hy = b["y_holdout"]
    p = positive_probability(a["pipeline"], holdout)
    prior = np.full(len(hy), float(y.mean()))
    write_json(r/"metrics_holdout.json", {"scope": "previously_observed_holdout", "threshold": a["threshold"],
               "at_f1_threshold": evaluate(hy, p, a["threshold"]), "at_0_5": evaluate(hy, p),
               "prior_reference": evaluate(hy, prior), "label_semantics_verified": False})
    prediction_table(hy, p, a["threshold"], c["risk_groups"], "previously_observed_holdout").to_csv(r/"predictions_holdout.csv", index=False)
    intervals, risk = bootstrap(hy, p, a["threshold"], c["risk_groups"], c["bootstrap_iterations"], c["seed"])
    intervals.to_csv(r/"metrics_ci_holdout.csv", index=False)
    risk.to_csv(r/"risk_holdout.csv", index=False)
    figures(hy, p, a["threshold"], r/"figures", "holdout")
    from .thesis_visuals import score_and_group_figures
    for scope in ["oof", "holdout"]:
        score_and_group_figures(pd.read_csv(r/f"predictions_{scope}.csv"), c, r/"figures", scope)
    joblib.dump(a["pipeline"], m/"pipeline.joblib")
    np.testing.assert_allclose(positive_probability(joblib.load(m/"pipeline.joblib"), holdout), p, atol=0, rtol=0)
    pre = a["base_pipeline"].named_steps["prepare"]
    finish = a["base_pipeline"].named_steps["finish"]
    write_json(m/"metadata.json", {"algorithm": a["algorithm"], "scenario": a["scenario"], "version": a["version"],
               "threshold": a["threshold"], "calibrated": a["calibrated"], "input_columns": list(X.columns),
               "input_dtypes": X.dtypes.astype(str).to_dict(), "positive_class": 1, "label_semantics_verified": False,
               "score_rule": "min(10, 1 + floor(10*p))", "risk_groups": c["risk_groups"], "seed": c["seed"],
               "transformed_features": list(finish.get_feature_names_out()), "reference_categories": pre.categories_,
               "selected_missing_flags": pre.flag_columns_, "log_columns": pre.log_columns_, "config": c,
               "versions": {k: importlib.metadata.version(k) for k in PACKAGES}, "python": platform.python_version(),
               "source_sha256": a["source_sha256"], "holdout_previously_observed": True,
               "prediction_contract": "Raw feature-only DataFrame; aliases normalized inside pipeline; input columns reordered by saved schema; no ID/target/extra columns"})
    from .thesis_summary import build_summary
    build_summary(c)
    print("Completed thesis ML experiment; saved pipeline reload exactly matches holdout probabilities", flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("stage", choices=["prepare", "features", "smoke", "benchmark", "tune", "robustness", "finalize", "all", "report"])
    p.add_argument("--config", default="thesis_config.json")
    args = p.parse_args()
    c = json.loads(Path(args.config).read_text(encoding="utf-8"))
    r, m = locations(c)
    stages = {"prepare": prepare, "features": feature_study, "smoke": smoke, "benchmark": benchmark,
              "tune": tune, "robustness": robustness, "finalize": finalize}
    if args.stage == "report":
        from .thesis_summary import build_summary
        build_summary(c)
        return
    if args.stage != "prepare" and (r/"metrics_holdout.json").exists():
        raise ValueError("Completed experiment preserved; use report or a new run directory")
    tasks = list(stages) if args.stage == "all" else [args.stage]
    for name in tasks:
        write_json(r/"execution_status.json", {"stage": name, "status": "running", "holdout_previously_observed": True})
        start = time.perf_counter()
        stages[name](c)
        write_json(r/f"stage_{name}.json", {"status": "completed", "seconds": time.perf_counter()-start})
    write_json(r/"execution_status.json", {"status": "completed", "completed_stages": [path.stem.removeprefix("stage_") for path in r.glob("stage_*.json")]})


if __name__ == "__main__":
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        main()

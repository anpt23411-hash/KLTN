import argparse
import ctypes
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder

from .data import load_clean, write_json, fingerprint


def inspect(c, sheet):
    book = pd.ExcelFile(c["data_path"])
    report = {"file": c["data_path"], "sha256": fingerprint(c["data_path"]), "sheets": book.sheet_names,
              "requested_sheet_exists": "E Commerce Dataset(1)  " in book.sheet_names}
    if sheet:
        d, audit = load_clean(c["data_path"], sheet)
        report.update(inspected_sheet=sheet, audit=audit, columns=list(d.columns),
                      label_verification="Data Dict says Churn Flag only; 0/1 meaning not yet confirmed")
    write_json("reports/inspection.json", report)
    print(json.dumps(report, indent=2, ensure_ascii=False))


def smoke(c, sheet):
    """Real-data engineering compatibility check; not a research benchmark."""
    import shap
    d, _ = load_clean(c["data_path"], sheet)
    development, _ = train_test_split(d, test_size=.2, stratify=d.Churn, random_state=42)
    subset, _ = train_test_split(development, train_size=min(240, len(development)-2), stratify=development.Churn, random_state=42)
    X, y = subset.drop(columns=["Churn", "CustomerID"]), subset.Churn
    cats = list(X.select_dtypes(include=["object", "string"]).columns)
    nums = [col for col in X if col not in cats]
    pre = ColumnTransformer([
        ("numeric", SimpleImputer(strategy="median"), nums),
        ("categorical", make_pipeline(SimpleImputer(strategy="most_frequent"),
                                      OneHotEncoder(handle_unknown="ignore", sparse_output=False)), cats)])
    tree = RandomForestClassifier(n_estimators=10, max_depth=3, random_state=42, n_jobs=1)
    pipe = make_pipeline(pre, tree).fit(X, y)
    z = pre.transform(X.iloc[:12])
    explainer = shap.TreeExplainer(tree)
    values = np.asarray(explainer.shap_values(z))
    # RandomForest SHAP contributions are in probability space.
    np.testing.assert_allclose(values[:, :, 1].sum(axis=1) + explainer.expected_value[1],
                               tree.predict_proba(z)[:, 1], atol=1e-6)
    from xgboost import XGBClassifier
    xgb = XGBClassifier(n_estimators=10, max_depth=2, random_state=42, n_jobs=1).fit(pre.transform(X), y)
    xgb_explainer = shap.TreeExplainer(xgb)
    xgb_values = np.asarray(xgb_explainer.shap_values(z))
    np.testing.assert_allclose(xgb_values.sum(axis=1) + xgb_explainer.expected_value,
                               xgb.predict(z, output_margin=True), atol=1e-5)
    from .experiment import validate_config, model_and_space
    from .preprocessing import build_pipeline
    research_pipeline = "pending_definitions"
    try:
        validate_config(c)
    except ValueError:
        pass
    else:
        for algorithm in c["algorithms"]:
            for scenario in c["scenarios"].values():
                estimator, _ = model_and_space(algorithm, scenario["class_weight"], y)
                candidate = build_pipeline(X, estimator, c, scenario)
                candidate.fit(X, y)
                assert np.isfinite(candidate.predict_proba(X.iloc[:12])).all()
        research_pipeline = "passed_all_confirmed_combinations"
    resources = {"logical_cpus": os.cpu_count(), "cv_n_jobs": c.get("n_jobs", 1)}
    if os.name == "nt":
        class Memory(ctypes.Structure):
            _fields_ = [("length", ctypes.c_ulong), ("load", ctypes.c_ulong)] + [
                (name, ctypes.c_ulonglong) for name in ["total_physical", "available_physical", "total_page", "available_page", "total_virtual", "available_virtual", "extended"]]
        mem = Memory()
        mem.length = ctypes.sizeof(mem)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
            resources.update(total_ram_gib=mem.total_physical/2**30, available_ram_gib=mem.available_physical/2**30)
    write_json("reports/smoke.json", {"status": "passed", "scope": "engineering_only_not_research",
               "sheet": sheet, "rows": len(X), "shap_version": shap.__version__,
               "shap_shape": list(values.shape), "shap_additivity": "passed_probability_space",
               "xgboost_shap_additivity": "passed_log_odds_space",
               "resources": resources, "research_pipeline": research_pipeline,
               "config": c, "source_sha256": fingerprint(c["data_path"])})
    print("Real-data smoke and SHAP additivity passed", resources)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["inspect", "smoke", "prepare", "benchmark", "finalize", "all"])
    parser.add_argument("--config", default="config.json")
    parser.add_argument("--sheet", help="Explicit inspection/smoke sheet; does not silently change research config")
    args = parser.parse_args()
    c = json.loads(Path(args.config).read_text(encoding="utf-8"))
    for p in ["data/raw", "notebooks", "src", "models", "reports"]:
        Path(p).mkdir(parents=True, exist_ok=True)
    if args.stage == "inspect":
        inspect(c, args.sheet)
    elif args.stage == "smoke":
        if not (args.sheet or c["sheet"]):
            parser.error("smoke requires --sheet or confirmed config.sheet")
        smoke(c, args.sheet or c["sheet"])
    else:
        from .experiment import validate_config, prepare, benchmark, finalize
        validate_config(c)
        if args.stage == "all":
            if Path("reports/metrics_test.json").exists():
                raise ValueError("Final test already evaluated; preserve existing run")
            smoke(c, c["sheet"])
            prepare(c)
            benchmark(c)
            finalize(c)
        else:
            {"prepare": prepare, "benchmark": benchmark, "finalize": finalize}[args.stage](c)


if __name__ == "__main__":
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        main()

"""Audit completed artifacts without fitting or predicting on holdout."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from .data import fingerprint, write_json

EXPECTED = {
    "prepare": ["config_snapshot.json", "split_manifest.json", "data_audit.json", "cv_manifest.json", "eda/missing_association_train.csv"],
    "features": ["feature_selection.json", "feature_study.csv", "feature_study_folds.csv"],
    "smoke": ["smoke.json"],
    "benchmark": ["benchmark.csv", "benchmark_repeated_folds.csv", "imbalance_repeated.csv", "paired_imbalance_deltas.csv"],
    "tune": ["selection.json", "tuning_shortlist.csv", "post_tuning_folds.csv", "predictions_oof.csv", "metrics_ci_oof.csv", "risk_oof.csv"],
    "robustness": ["sensitivity_folds.csv", "smotenc_k_study.csv"],
    "finalize": ["metrics_holdout.json", "predictions_holdout.csv", "metrics_ci_holdout.csv", "risk_holdout.csv", "shap_metadata.json", "shap_local_contributions.csv", "shap_prediction_context.csv", "permutation_folds.csv", "operational_timing_draws.csv", "figures/roc_holdout.png", "figures/precision_recall_holdout.png", "figures/confusion_holdout.png", "figures/calibration_holdout.png", "figures/shap_beeswarm.png", "figures/shap_waterfall_high.png"],
}


def audit(c):
    r, m = Path(c["report_dir"]), Path(c["model_dir"])
    def read(p):
        return json.loads(Path(p).read_text(encoding="utf-8"))
    stages = []
    for name, outputs in EXPECTED.items():
        stamp = r/f"stage_{name}.json"
        missing = [p for p in outputs if not (r/p).is_file() or not (r/p).stat().st_size]
        record = read(stamp) if stamp.exists() else {}
        stages.append(dict(stage=name, status="completed" if record.get("status") == "completed" and not missing else "incomplete_or_error",
                           seconds=record.get("seconds"), missing_outputs=missing))
    assert read(r/"config_snapshot.json") == c, "Current config differs from run snapshot"
    metadata = read(m/"metadata.json")
    assert metadata["config"] == c, "Current config differs from final metadata"
    assert fingerprint(c["data_path"]) == metadata["source_sha256"], "Dataset fingerprint differs"
    for name in ["split.joblib", "trained.joblib", "pipeline.joblib", "metadata.json"]:
        assert (m/name).is_file() and (m/name).stat().st_size, f"Missing model artifact {name}"
    folds = c["cv_folds"]*c["cv_repeats"]
    count = len(c["algorithms"])*len(c["scenarios"])+2
    table = pd.read_csv(r/"benchmark_repeated_folds.csv")
    assert len(table) == count*folds
    assert table.groupby(["algorithm", "scenario"]).size().eq(folds).all()
    assert len(pd.read_csv(r/"benchmark.csv")) == count
    assert len(pd.read_csv(r/"feature_study_folds.csv")) == 6*2*folds
    assert len(pd.read_csv(r/"sensitivity_folds.csv")) == 2*folds
    assert len(pd.read_csv(r/"smotenc_k_study.csv")) == 2*3*c["cv_folds"]
    shortlist = pd.read_csv(r/"tuning_shortlist.csv")
    assert shortlist.algorithm.nunique() == 2
    for name in shortlist.algorithm:
        assert len(pd.read_csv(r/f"tuning_{name}.csv")) == c["tuning_iterations"]
    assert len(pd.read_csv(r/"post_tuning_folds.csv")) == 2*2*c["cv_folds"]
    oof, holdout = [pd.read_csv(r/f"predictions_{s}.csv") for s in ["oof", "holdout"]]
    assert not set(oof.row_reference) & set(holdout.row_reference)
    manifest = read(r/"split_manifest.json")
    assert set(oof.row_reference) == set(manifest["train_row_references"])
    assert set(holdout.row_reference) == set(manifest["holdout_row_references"])
    assert set(holdout.scope) == {"previously_observed_holdout"}
    local = pd.read_csv(r/"shap_local_contributions.csv", index_col="row_reference")
    context = pd.read_csv(r/"shap_prediction_context.csv").set_index("row_reference").loc[local.index]
    error = float(np.max(np.abs(local.sum(axis=1)+context.base_value-context.explained_output)))
    assert error < 1e-4, "Saved grouped SHAP additivity failed"
    assert read(r/"shap_metadata.json")["additivity"] == "passed"
    assert len(pd.read_csv(r/"permutation_folds.csv")) == len(metadata["input_columns"])*c["cv_folds"]
    times = pd.read_csv(r/"operational_timing_draws.csv").operation.value_counts().to_dict()
    assert times == {"single_predict": 200, "fit": 5, "batch_predict": 5}
    history = {"error": "SHAP interventional additivity failed in first finalize attempt",
               "resolution": read(r/"shap_metadata.json")["explainer"], "active_error": False}
    result = {"status": "passed", "method": "Read saved files only; no fit, predict_proba, holdout reevaluation or bootstrap rerun",
              "config_and_dataset_match": True, "stages": stages,
              "missing_or_failed_stages": [s["stage"] for s in stages if s["status"] != "completed"],
              "benchmark_rows": count, "repeated_fold_rows": len(table), "shap_saved_additivity_max_error": error,
              "historical_error": history, "holdout_previously_observed": True}
    assert not result["missing_or_failed_stages"], "Incomplete stage outputs"
    write_json(r/"experiment_audit.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    audit(json.loads(Path("thesis_config.json").read_text(encoding="utf-8")))

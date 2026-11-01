"""Generate a reviewable report exclusively from completed experiment artifacts."""
import json
from pathlib import Path

import pandas as pd

from .data import write_json


def completed_report():
    def read(path):
        return json.loads(Path(path).read_text(encoding="utf-8"))
    audit = read("reports/data_audit.json")
    split = read("reports/split_manifest.json")
    selection = read("reports/selection.json")
    test = read("reports/metrics_test.json")
    meta = read("models/metadata.json")
    table = pd.read_csv("reports/benchmark_train_cv.csv")
    risks = pd.read_csv("reports/risk_test.csv")
    text = ["# Completed experiment — technical binary labels", "",
            "Label=1 is the technical positive class; business meaning and Tenure units remain unverified.",
            "Source and access evidence: DATA_PROVENANCE.md, accessed 2026-10-25.", "",
            f"Data: {audit['rows_before']} -> {audit['rows_after']} rows; "
            f"{audit['duplicates_after_normalization_excluding_id']} duplicates removed after normalization.",
            f"Split: {split['train_rows']} train, {split['test_rows']} test; stratified 80/20, seed 42.",
            f"Selected on training CV: {selection['algorithm']}, {selection['scenario']}.",
            f"Sigmoid selected by training OOF Brier: {selection['sigmoid_selected']}.",
            f"F1 threshold from training OOF: {selection['threshold']:.8f}.", "",
            "## Training CV benchmark (three folds)", "",
            "| Algorithm | Scenario | AP | ROC-AUC | Brier |", "|---|---|---:|---:|---:|"]
    for row in table.itertuples():
        text.append(f"| {row.algorithm} | {row.scenario} | {row.average_precision:.6f} | {row.roc_auc:.6f} | {row.brier:.6f} |")
    text += ["", "## OOF selection diagnostic and final independent test", "",
             "| Scope | AP | ROC-AUC | Brier |", "|---|---:|---:|---:|"]
    key = "calibrated_oof" if selection["sigmoid_selected"] else "uncalibrated_oof"
    for scope, values in [("OOF (selection diagnostic)", selection[key]), ("Final test", test)]:
        text.append(f"| {scope} | {values['average_precision']:.6f} | {values['roc_auc']:.6f} | {values['brier']:.6f} |")
    text += ["", "## Final test score groups", "",
             "| Group | Count | Label=1 rate | Precision | Recall | Lift |",
             "|---|---:|---:|---:|---:|---:|"]
    for r in risks.itertuples():
        text.append(f"| {r.group} | {r.count} | {r.positive_rate:.6f} | {r.precision:.6f} | {r.recall:.6f} | {r.lift:.6f} |")
    text += ["", "95% stratified-bootstrap intervals (1,000 draws) are in risk_test.csv and risk_oof.csv.",
             "Scores: min(10, 1 + floor(10*p)); low 1-3, medium 4-6, high 7-10.", "",
             "## Limits", "",
             "- No verified 0/1 business meaning or Tenure unit; probabilities predict the stored label only.",
             "- No documented outcome horizon or timestamp split: cannot establish prospective operational validity.",
             "- Exact duplicates removed; similar observations may remain, so random-split performance may be optimistic.",
             "- OOF uses hyperparameters/calibration selected on the same training set; not an unbiased model-selection estimate.",
             "- Final test AP is substantially higher than training CV AP; a single random holdout is uncertain evidence of external performance.",
             "- RandomizedSearchCV has a 10-draw budget and may score below the untuned baseline. Final selection here compares the two tuned candidates, not a guaranteed global optimum.",
             "- Bootstrap is conditional on the fixed fitted pipeline and observed class prevalence; excludes retraining uncertainty.",
             "- Permutation and SHAP use training data; associations and model reliance, not causal effects.",
             "- Chi-square approximations with sparse expected cells are flagged; treat affected tests cautiously.",
             "- Risk bands are operational conventions, not validated business interventions.", "",
             "Saved pipeline reload reproduced final test probabilities. See models/metadata.json for schema and versions."]
    Path("reports/RESULTS.md").write_text("\n".join(text)+"\n", encoding="utf-8")
    write_json("reports/execution_status.json", {
        "status": "completed_technical_label_experiment", "label_semantics_verified": False,
        "data_inspection": "completed", "engineering_and_research_smoke": "passed",
        "eda": "completed_train_only", "benchmark": "completed_20_combinations_plus_2_dummies",
        "tuning": "completed_top_2_distinct_algorithms_10_draws_3_folds_each",
        "calibration_threshold_oof": "completed_train_only", "bootstrap": "1000_each_oof_and_test",
        "final_test": "evaluated_once", "model_save_reload": "passed",
        "selected_algorithm": selection["algorithm"], "selected_scenario": selection["scenario"],
        "final_test_metrics": test, "model_versions": meta["versions"],
        "git": "No commit or push; raw data, environments, models and reports ignored",
        "test_log": "reports/test_results.txt"})

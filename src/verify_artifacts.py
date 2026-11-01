"""Validate exported experiment contracts without refitting or using test for selection."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, confusion_matrix

from .data import write_json
from .scoring import score_probability


def verify():
    oof = pd.read_csv("reports/predictions_oof.csv", dtype={"probability": str})
    test = pd.read_csv("reports/predictions_test.csv", dtype={"probability": str})
    for table in (oof, test):
        table["probability"] = table.probability.map(float)
    manifest = json.loads(Path("reports/split_manifest.json").read_text())
    assert len(oof) == manifest["train_rows"] and len(test) == manifest["test_rows"]
    assert oof.row_reference.is_unique and test.row_reference.is_unique
    assert not set(oof.row_reference) & set(test.row_reference)
    assert set(oof.scope) == {"oof"} and set(test.scope) == {"test"}
    benchmark = pd.read_csv("reports/benchmark_train_cv.csv")
    assert len(benchmark) == 22
    assert len(pd.read_csv("reports/benchmark_folds_train_cv.csv")) == 66
    for name in ["random_forest", "extra_trees"]:
        assert len(pd.read_csv(f"reports/tuning_{name}.csv")) == 10
    for scope, table in [("oof", oof), ("test", test)]:
        np.testing.assert_array_equal(score_probability(table.probability), table.score)
        assert not {"CustomerID", "Gender", "MaritalStatus"} & set(table.columns)
        groups = pd.read_csv(f"reports/risk_{scope}.csv")
        assert groups.loc[groups.group.isin(["low", "medium", "high"]), "count"].sum() == len(table)
        write_json(f"reports/threshold_metrics_{scope}.json", {
            "scope": scope, "precision": precision_score(table.observed_label, table.prediction),
            "recall": recall_score(table.observed_label, table.prediction),
            "f1": f1_score(table.observed_label, table.prediction),
            "confusion_matrix_label_order_0_1": confusion_matrix(table.observed_label, table.prediction).tolist(),
            "semantics": "technical labels, not verified business outcomes"})
    write_json("reports/artifact_verification.json", {
        "status": "passed", "train_test_row_references": "disjoint",
        "oof_rows": len(oof), "test_rows": len(test), "benchmark_rows": 22,
        "cv_fold_rows": 66, "tuning_trials_each": 10,
        "scores": "reproduced from exported probabilities", "risk_group_counts": "sum to scope row count",
        "method": "existing outputs only; no refitting or new test-driven selection"})
    print("Artifact contracts passed: disjoint OOF/test, 22 benchmark rows, 66 fold rows, 10 trials each, scores and counts")


if __name__ == "__main__":
    verify()

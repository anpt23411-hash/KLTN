"""Tiny fixtures verify contracts only; never produce research results."""
import tempfile
import unittest
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression

from src.data import clean
from src.preprocessing import Features, build_pipeline
from src.scoring import score_probability, bootstrap_risks


class Contracts(unittest.TestCase):
    def test_xgboost_fold_balanced_weights(self):
        from unittest.mock import patch
        from src.experiment import FoldWeightedXGB
        estimator = FoldWeightedXGB(balanced=True, random_state=42)
        for labels in [np.array([0, 0, 0, 1]), np.array([0, 1, 1, 1, 1])]:
            with patch("xgboost.XGBClassifier.fit", return_value=None) as fit:
                clone(estimator).fit(np.zeros((len(labels), 2)), labels)
                expected = np.array([len(labels)/(2*(labels == v).sum()) for v in labels])
                np.testing.assert_allclose(fit.call_args.kwargs["sample_weight"], expected)
        self.assertNotIn("balanced", estimator.get_xgb_params())

    def test_missing_research_definitions_block_benchmark(self):
        import json
        from src.experiment import validate_config
        c = json.loads(Path("config.json").read_text())
        # Independent of the user's later choices: missing source must always fail.
        c["label_source"] = None
        with self.assertRaisesRegex(ValueError, "label_source"):
            validate_config(c)

    def test_registry_estimators_cv_compatible(self):
        from sklearn.model_selection import cross_val_predict, StratifiedKFold
        from src.experiment import model_and_space
        X = pd.DataFrame({"Tenure": np.arange(48, dtype=float), "cat": ["a", "b"]*24})
        y = np.array([0, 0, 1, 0]*12)
        config = {"categorical_columns": ["cat"], "new_customer_max_tenure": 0}
        for algorithm in ["logistic_regression", "random_forest", "extra_trees", "hist_gradient_boosting", "xgboost"]:
            estimator, _ = model_and_space(algorithm, True, pd.Series(y))
            pipe = build_pipeline(X, estimator, config, {"sampling": "none"})
            p = cross_val_predict(pipe, X, y, cv=StratifiedKFold(3, shuffle=True, random_state=42), method="predict_proba")
            self.assertEqual(p.shape, (48, 2))
            self.assertTrue(np.isfinite(p).all())

    def test_calibration_oof_and_roundtrip(self):
        from sklearn.calibration import CalibratedClassifierCV
        from sklearn.model_selection import cross_val_predict, StratifiedKFold
        X = pd.DataFrame({"Tenure": np.arange(60, dtype=float), "cat": ["a", "b"]*30})
        y = np.array([0, 0, 1]*20)
        pipe = build_pipeline(X, LogisticRegression(random_state=42),
                              {"categorical_columns": ["cat"], "new_customer_max_tenure": 0},
                              {"sampling": "smotenc"})
        cv = StratifiedKFold(3, shuffle=True, random_state=42)
        calibrated = CalibratedClassifierCV(pipe, method="sigmoid", cv=cv)
        p = cross_val_predict(calibrated, X, y, cv=cv, method="predict_proba")
        self.assertEqual(p.shape, (len(X), 2))
        calibrated.fit(X, y)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"calibrated.joblib"
            joblib.dump(calibrated, path)
            np.testing.assert_allclose(calibrated.predict_proba(X.iloc[:3]),
                                       joblib.load(path).predict_proba(X.iloc[:3]))

    def test_eda_fdr_and_no_outlier_deletion(self):
        from src.eda import eda
        X = pd.DataFrame({"num": [1., 2., 3., 4., 5., 1000.],
                          "other": [2., 3., 1., 6., 5., 7.], "cat": ["a", "b"]*3})
        y = pd.Series([0, 1, 0, 1, 0, 1])
        original = X.copy(deep=True)
        with tempfile.TemporaryDirectory() as tmp:
            eda(X, y, Path(tmp))
            table = pd.read_csv(Path(tmp)/"hypothesis_tests_train.csv")
            self.assertTrue(table.q_fdr_bh.between(0, 1).all())
            self.assertEqual(set(table.test), {"chi_square", "mann_whitney", "spearman"})
        pd.testing.assert_frame_equal(X, original)

    def test_deduplicate_after_id_removed_and_alias_normalization(self):
        raw = pd.DataFrame({"CustomerID": [1, 2, 3], "Churn": [1, 1, 0], "Tenure": [2., 2., 4.],
                            "PreferredLoginDevice": ["Phone ", "Mobile Phone", "Computer"]})
        d, audit = clean(raw)
        self.assertEqual(len(d), 2)
        self.assertEqual(audit["duplicates_after_normalization_excluding_id"], 1)
        self.assertEqual(len(raw), 3)

    def test_conflicting_labels_fail(self):
        with self.assertRaisesRegex(ValueError, "conflicting"):
            clean(pd.DataFrame({"CustomerID": [1, 2], "Churn": [0, 1], "Tenure": [1., 1.]}))

    def test_unknown_label_fail(self):
        with self.assertRaises(ValueError):
            clean(pd.DataFrame({"CustomerID": [1, 2], "Churn": [0, 2], "Tenure": [1., 2.]}))

    def test_score_edges(self):
        np.testing.assert_array_equal(score_probability([0, .099, .1, .3, .6, .9, 1]), [1, 1, 2, 4, 7, 10, 10])
        for bad in [[np.nan], [-.01], [1.01]]:
            with self.assertRaises(ValueError):
                score_probability(bad)

    def test_features_train_only_and_unknown_tenure(self):
        train = pd.DataFrame({"Tenure": [0., 1., 2., 3., 100.], "cat": ["a"]*5})
        f = Features(["cat"], 0).fit(train)
        out = f.transform(pd.DataFrame({"Tenure": [np.nan, 0., 1000.], "cat": ["b"]*3}))
        self.assertEqual(out.IsNewCustomer.iloc[0], 0)
        self.assertEqual(out.TenureMissing.iloc[0], 1)
        self.assertEqual(out.IsNewCustomer.iloc[1], 1)
        np.testing.assert_allclose(out.Tenure.iloc[2], np.log1p(1000))

    def test_pipeline_smote_serialization_and_unseen_category(self):
        X = pd.DataFrame({"Tenure": np.arange(30, dtype=float), "cat": ["a", "b"]*15})
        X.loc[2, "Tenure"] = np.nan
        y = np.array([0]*22 + [1]*8)
        config = {"categorical_columns": ["cat"], "new_customer_max_tenure": 0}
        for sampling in ["none", "random_over", "smotenc"]:
            pipe = build_pipeline(X, LogisticRegression(random_state=42), config, {"sampling": sampling})
            pipe = clone(pipe).fit(X, y)
            holdout = pd.DataFrame({"Tenure": [np.nan, 999.], "cat": ["unseen", "a"]})
            before = pipe.named_steps["pre"].named_transformers_["numeric"].named_steps["impute"].statistics_.copy()
            p = pipe.predict_proba(holdout)
            self.assertEqual(p.shape, (2, 2))
            np.testing.assert_array_equal(before, pipe.named_steps["pre"].named_transformers_["numeric"].named_steps["impute"].statistics_)
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp)/"pipeline.joblib"
                joblib.dump(pipe, path)
                np.testing.assert_allclose(p, joblib.load(path).predict_proba(holdout))

    def test_bootstrap_reproducible_and_counts(self):
        y = np.array([0, 0, 0, 1, 1, 1])
        p = np.array([.05, .2, .5, .7, .8, .95])
        a = bootstrap_risks(y, p, .5, 20)
        pd.testing.assert_frame_equal(a, bootstrap_risks(y, p, .5, 20))
        self.assertEqual(a.iloc[:3]["count"].sum(), len(y))


if __name__ == "__main__":
    unittest.main()

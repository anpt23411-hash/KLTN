import tempfile
import unittest
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold
from src.thesis_preprocessing import PrepareFrame, FinishFrame, LogicalSMOTENC, build_thesis_pipeline, ratios
from src.evaluation import positive_probability, choose_threshold, score_groups


def fixture():
    return pd.DataFrame({"Tenure": [np.nan, 0., 1., 2., 5., 10.]*10,
                         "Gender": ["Male", "Female"]*30, "Complain": [0, 1]*30,
                         "OrderCount": [0., 1., 2., 3., np.nan, 8.]*10,
                         "CouponUsed": [0., 1., 0., 2., 3., np.nan]*10,
                         "CashbackAmount": np.arange(60, dtype=float)+1}), pd.Series([0, 0, 1]*20)


class ThesisContracts(unittest.TestCase):
    def test_local_inference_contract(self):
        from src.predict import predict_frame
        X, y = fixture()
        pipe = build_thesis_pipeline(LogisticRegression(random_state=42), "logistic_regression", {"sampling": "none"}, {"flags": "all"}).fit(X, y)
        metadata = {"input_columns": list(X), "input_dtypes": X.dtypes.astype(str).to_dict(),
                    "threshold": .3, "risk_groups": {"low": [1, 2], "medium": [3, 5], "high": [6, 10]}}
        output = predict_frame(X.iloc[:3][X.columns[::-1]], pipe, metadata)
        self.assertEqual(set(output.scope), {"new_data_unlabelled"})
        self.assertEqual(len(output), 3)
        with self.assertRaises(ValueError):
            predict_frame(X.assign(CustomerID=range(len(X))), pipe, metadata)
        with self.assertRaises(ValueError):
            predict_frame(X.assign(Churn=y), pipe, metadata)

    def test_probability_class_guard(self):
        class WrongClassOrder:
            classes_ = [1, 0]
        with self.assertRaisesRegex(ValueError, "class order"):
            positive_probability(WrongClassOrder(), pd.DataFrame())

    def test_oof_repeated_folds_rejected(self):
        from src.thesis import run_cv
        from sklearn.model_selection import RepeatedStratifiedKFold
        X, y = fixture()
        pipe = build_thesis_pipeline(DecisionTreeClassifier(random_state=42), "decision_tree", {"sampling": "none"}, {"flags": "all"})
        with self.assertRaisesRegex(ValueError, "exact partition"):
            run_cv(pipe, X, y, RepeatedStratifiedKFold(n_splits=3, n_repeats=2, random_state=42).split(X, y), oof=True)

    def test_ratios_not_computed_after_imputation(self):
        X, _ = fixture()
        result = ratios(X)
        self.assertTrue(np.isnan(result.CashbackPerOrder.iloc[0]))
        self.assertTrue(np.isnan(result.CouponRate.iloc[4]))
        self.assertEqual(result.CashbackPerOrder.iloc[1], 2.)

    def test_schema_aliases_and_missing_source(self):
        X, y = fixture()
        X["PreferredLoginDevice"] = ["Phone", "Computer"]*30
        pre = PrepareFrame(flags="all", tenure_threshold=1).fit(X, y)
        z = pre.transform(X[X.columns[::-1]])
        self.assertEqual(z.IsNewCustomer.iloc[:4].tolist(), [0., 1., 1., 0.])
        self.assertEqual(z.TenureMissing.iloc[0], 1.)
        self.assertEqual(z.PreferredLoginDevice.iloc[0], 1.)  # Computer wins alphabetical mode tie.
        with self.assertRaises(ValueError):
            pre.transform(X.assign(Churn=y))
        with self.assertRaises(ValueError):
            PrepareFrame().fit(X.assign(CustomerID=range(len(X))), y)

    def test_smote_preserves_binary_flags_and_newcustomer_logic(self):
        X, y = fixture()
        pre = PrepareFrame(flags="all", include_new=True, tenure_threshold=1).fit(X, y)
        z = pre.transform(X)
        for ratio in [1., .5]:
            sampled, labels = LogicalSMOTENC(sampling_strategy=ratio).fit_resample(z, y)
            raw_tenure = np.expm1(sampled.Tenure) if "Tenure" in pre.log_columns_ else sampled.Tenure
            expected = ((raw_tenure <= 1) & sampled["__TenureMissing"].eq(0)).astype(float)
            np.testing.assert_array_equal(sampled.IsNewCustomer, expected)
            for col in sampled:
                if col.endswith("Missing") or col == "Complain":
                    self.assertTrue(set(sampled[col]) <= {0., 1.})
            self.assertAlmostEqual(np.sum(np.asarray(labels) == 1)/np.sum(np.asarray(labels) == 0), ratio)

    def test_modal_reference_not_changed_by_resampling(self):
        X, y = fixture()
        pre = PrepareFrame(flags="all").fit(X, y)
        z = pre.transform(X)
        sampled, _ = LogicalSMOTENC().fit_resample(z, y)
        finish = FinishFrame(scale=True).fit(sampled)
        self.assertEqual(finish.encoder_.drop_idx_.tolist(), [0])
        self.assertNotIn("Complain", finish.scaled_)
        self.assertNotIn("IsNewCustomer", finish.scaled_)

    def test_fold_preprocessing_and_no_validation_resampling(self):
        X, y = fixture()
        p = build_thesis_pipeline(DecisionTreeClassifier(random_state=42), "decision_tree", {"sampling": "smotenc", "ratio": 1.}, {"flags": "all"})
        for a, b in StratifiedKFold(3, shuffle=True, random_state=42).split(X, y):
            fitted = clone(p).fit(X.iloc[a], y.iloc[a])
            self.assertEqual(fitted.named_steps["prepare"].medians_["Tenure"], X.iloc[a].Tenure.median())
            counts = fitted.named_steps["sample"].sampled_class_counts_.copy()
            self.assertEqual(len(positive_probability(fitted, X.iloc[b])), len(b))
            self.assertEqual(fitted.named_steps["sample"].sampled_class_counts_, counts)

    def test_raw_prediction_roundtrip_unseen_category_and_order(self):
        X, y = fixture()
        pipe = build_thesis_pipeline(LogisticRegression(random_state=42), "logistic_regression", {"sampling": "none"}, {"flags": "all"}).fit(X, y)
        new = X.iloc[:3].copy()
        new["Gender"] = "unseen"
        expected = positive_probability(pipe, new)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"model.joblib"
            joblib.dump(pipe, path)
            np.testing.assert_allclose(positive_probability(joblib.load(path), new[new.columns[::-1]]), expected)

    def test_report_risk_boundaries_and_threshold(self):
        groups = {"low": [1, 2], "medium": [3, 5], "high": [6, 10]}
        table = score_groups([0, 0, 1, 1], [0., .2, .5, 1.], groups, .5)
        self.assertEqual(table.iloc[:3]["count"].tolist(), [1, 1, 2])
        threshold, sweep = choose_threshold([0, 0, 1, 1], [.1, .2, .2, .9])
        self.assertEqual(threshold, .2)
        self.assertGreater(sweep.f1.max(), .7)


if __name__ == "__main__":
    unittest.main()

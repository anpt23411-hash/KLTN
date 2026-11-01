import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTENC, RandomOverSampler


def missing_name(c):
    return "TenureMissing" if c == "Tenure" else c + "_missing"


class Features(TransformerMixin, BaseEstimator):
    """Fit log candidates on train only; flags are computed before imputation."""
    def __init__(self, categorical_columns, new_customer_max_tenure, use_log=True):
        self.categorical_columns = categorical_columns
        self.new_customer_max_tenure = new_customer_max_tenure
        self.use_log = use_log

    def fit(self, X, y=None):
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        self.numeric_ = [c for c in X if c not in self.categorical_columns]
        self.log_columns_ = [c for c in self.numeric_ if self.use_log and X[c].min() >= 0 and X[c].skew() > 1]
        return self

    def transform(self, X):
        if list(X.columns) != list(self.feature_names_in_):
            raise ValueError("Input columns/order differ from training schema")
        out = X.copy()
        for c in self.feature_names_in_:
            out[missing_name(c)] = out[c].isna().astype(float)
        out["IsNewCustomer"] = out.Tenure.eq(0).fillna(False).astype(float)
        for c in self.log_columns_:
            if (out[c].dropna() < 0).any():
                raise ValueError(f"Negative value in log1p feature {c}")
            out[c] = np.log1p(out[c])
        for c in self.categorical_columns:
            out[c] = out[c].map(lambda v: str(v) if pd.notna(v) else np.nan).astype(object)
        return out


def build_pipeline(X, estimator, config, scenario):
    cats = config["categorical_columns"]
    if not set(cats).issubset(X.columns):
        raise ValueError("Configured categorical columns absent from data")
    nums = [c for c in X if c not in cats]
    flags = [missing_name(c) for c in X] + ["IsNewCustomer"]
    nums += flags
    numeric = Pipeline([("impute", SimpleImputer(strategy="median", keep_empty_features=True)),
                        ("scale", StandardScaler())])
    categorical = Pipeline([("impute", SimpleImputer(strategy="most_frequent", keep_empty_features=True)),
                            ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1))])
    pre = ColumnTransformer([("numeric", numeric, nums), ("categorical", categorical, cats)],
                            verbose_feature_names_out=False).set_output(transform="pandas")
    post = ColumnTransformer([("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cats)],
                             remainder="passthrough", verbose_feature_names_out=False)
    steps = [("features", Features(cats, config["new_customer_max_tenure"], scenario.get("log1p", True))),
             ("pre", pre)]
    if scenario["sampling"] == "smotenc":
        steps.append(("sample", SMOTENC(categorical_features=cats + flags, random_state=42, k_neighbors=3)))
    elif scenario["sampling"] == "random_over":
        steps.append(("sample", RandomOverSampler(random_state=42)))
    elif scenario["sampling"] != "none":
        raise ValueError("sampling must be none, random_over or smotenc")
    steps += [("onehot", post), ("model", estimator)]
    return ImbPipeline(steps)

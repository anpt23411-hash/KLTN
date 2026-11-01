"""Exploratory tests use train only. FDR covers all reported hypothesis tests."""
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests


def eda(X, y, folder):
    folder.mkdir(parents=True, exist_ok=True)
    X.describe(include="all").to_csv(folder / "descriptive_train.csv")
    numeric = X.select_dtypes(include="number")
    rows, tests = [], []
    for c in numeric:
        v = numeric[c].dropna()
        q1, q3 = v.quantile([.25, .75])
        lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        rows.append(dict(feature=c, skew=v.skew(), q1=q1, q3=q3, lower=lo, upper=hi,
                         outside_iqr=int(((v < lo) | (v > hi)).sum()), missing=int(X[c].isna().sum())))
    pd.DataFrame(rows).to_csv(folder / "iqr_train.csv", index=False)
    for c in X:
        a, b = X.loc[y == 1, c].dropna(), X.loc[y == 0, c].dropna()
        if c in numeric:
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
            tests.append(dict(feature=c, test="mann_whitney", statistic=u, p=p,
                              effect=2*u/(len(a)*len(b))-1, effect_name="rank_biserial_positive_churn"))
        else:
            table = pd.crosstab(X[c].fillna("<MISSING>"), y)
            chi, p, _, expected = stats.chi2_contingency(table, correction=False)
            denom = min(table.shape)-1
            tests.append(dict(feature=c, test="chi_square", statistic=chi, p=p,
                              effect=np.sqrt(chi / (table.values.sum()*denom)) if denom else 0,
                              effect_name="cramers_v", fraction_expected_lt5=float((expected < 5).mean())))
    for i, c in enumerate(numeric):
        for other in numeric.columns[i+1:]:
            pair = numeric[[c, other]].dropna()
            rho, p = stats.spearmanr(pair[c], pair[other])
            tests.append(dict(feature=f"{c} | {other}", test="spearman", statistic=rho, p=p,
                              effect=rho, effect_name="rho"))
    result = pd.DataFrame(tests)
    valid = result.p.notna()
    result.loc[valid, "q_fdr_bh"] = multipletests(result.loc[valid, "p"], method="fdr_bh")[1]
    result.to_csv(folder / "hypothesis_tests_train.csv", index=False)

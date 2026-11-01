import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score, brier_score_loss, precision_score, recall_score

RISK_GROUPS = {"low": [1, 3], "medium": [4, 6], "high": [7, 10]}


def score_probability(p):
    p = np.asarray(p, dtype=float)
    if not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("Probabilities must be finite and in [0, 1]")
    return np.minimum(10, 1 + np.floor(10*p)).astype(int)


def metrics(y, p):
    return {"average_precision": average_precision_score(y, p), "roc_auc": roc_auc_score(y, p),
            "brier": brier_score_loss(y, p)}


def risk_table(y, p, threshold):
    y, p = np.asarray(y), np.asarray(p)
    scores = score_probability(p)
    rows = []
    for name, (lo, hi) in RISK_GROUPS.items():
        selected = (scores >= lo) & (scores <= hi)
        n = int(selected.sum())
        precision = float(y[selected].mean()) if n else np.nan
        rows.append(dict(group=name, count=n, positive_rate=precision, precision=precision,
                         recall=float(y[selected].sum()/y.sum()), lift=precision/y.mean()))
    selected = p >= threshold
    precision = precision_score(y, selected, zero_division=0)
    rows.append(dict(group="above_f1_threshold", count=int(selected.sum()),
                     positive_rate=float(y[selected].mean()) if selected.any() else np.nan,
                     precision=precision, recall=recall_score(y, selected), lift=precision/y.mean()))
    return pd.DataFrame(rows)


def bootstrap_risks(y, p, threshold, iterations=1000):
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(42)
    strata = [np.flatnonzero(y == k) for k in (0, 1)]
    samples = []
    for b in range(iterations):
        idx = np.concatenate([rng.choice(s, len(s), replace=True) for s in strata])
        samples.append(risk_table(y[idx], p[idx], threshold).assign(iteration=b))
    draws = pd.concat(samples, ignore_index=True)
    summary = risk_table(y, p, threshold).set_index("group")
    for c in ["count", "positive_rate", "precision", "recall", "lift"]:
        quant = draws.groupby("group")[c].quantile([.025, .975]).unstack()
        summary[c+"_ci_low"] = quant[.025]
        summary[c+"_ci_high"] = quant[.975]
    return summary.reset_index()

"""Metrics, risk strata, confidence intervals and publication figures."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn import metrics as m
from .scoring import score_probability


def positive_probability(estimator, X):
    classes = list(estimator.classes_)
    if classes != [0, 1]:
        raise ValueError(f"Unexpected class order {classes}")
    return estimator.predict_proba(X)[:, classes.index(1)]


def calibration_bins(y, p):
    frame = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    frame["bin"] = pd.qcut(frame.p, 10, duplicates="drop") if frame.p.nunique() > 1 else "constant"
    return frame.groupby("bin", observed=True).agg(count=("y", "size"), mean_probability=("p", "mean"), positive_rate=("y", "mean")).reset_index()


def evaluate(y, p, threshold=.5):
    y, p = np.asarray(y), np.asarray(p)
    pred = p >= threshold
    bins = calibration_bins(y, p)
    return dict(average_precision=m.average_precision_score(y, p), roc_auc=m.roc_auc_score(y, p),
                brier=m.brier_score_loss(y, p), accuracy=m.accuracy_score(y, pred),
                precision=m.precision_score(y, pred, zero_division=0), recall=m.recall_score(y, pred, zero_division=0),
                f1=m.f1_score(y, pred, zero_division=0), f2=m.fbeta_score(y, pred, beta=2, zero_division=0),
                mcc=m.matthews_corrcoef(y, pred), balanced_accuracy=m.balanced_accuracy_score(y, pred),
                ece=float((bins["count"]*(bins.mean_probability-bins.positive_rate).abs()).sum()/len(y)))


def choose_threshold(y, p):
    precision, recall, thresholds = m.precision_recall_curve(y, p)
    f1 = 2*precision[:-1]*recall[:-1]/np.maximum(precision[:-1]+recall[:-1], 1e-15)
    table = pd.DataFrame({"threshold": thresholds, "precision": precision[:-1], "recall": recall[:-1], "f1": f1})
    winner = table.sort_values(["f1", "recall", "threshold"], ascending=[False, False, True], kind="stable").iloc[0]
    return float(winner.threshold), table


def score_groups(y, p, groups, threshold):
    y, p = np.asarray(y), np.asarray(p)
    score = score_probability(p)
    rows = []
    ranges = {**groups, **{f"score_{i}": [i, i] for i in range(1, 11)}}
    for name, (lo, hi) in ranges.items():
        selected = (score >= lo) & (score <= hi)
        n = int(selected.sum())
        positives = int(y[selected].sum())
        rate = positives/n if n else np.nan
        rows.append(dict(group=name, count=n, positive_count=positives, positive_rate=rate,
                         precision=rate, recall=positives/y.sum(), lift=rate/y.mean()))
    selected = p >= threshold
    n = int(selected.sum())
    rate = float(y[selected].mean()) if n else np.nan
    rows.append(dict(group="above_f1_threshold", count=n, positive_count=int(y[selected].sum()),
                     positive_rate=rate, precision=rate, recall=y[selected].sum()/y.sum(), lift=rate/y.mean()))
    return pd.DataFrame(rows)


def bootstrap(y, p, threshold, groups, iterations=1000, seed=42):
    y, p = np.asarray(y), np.asarray(p)
    rng = np.random.default_rng(seed)
    strata = [np.flatnonzero(y == i) for i in [0, 1]]
    metric_rows, risk_rows = [], []
    for i in range(iterations):
        idx = np.concatenate([rng.choice(s, len(s), replace=True) for s in strata])
        metric_rows.append(evaluate(y[idx], p[idx], threshold))
        risk_rows.append(score_groups(y[idx], p[idx], groups, threshold).assign(iteration=i))
    metrics = pd.DataFrame(metric_rows)
    intervals = metrics.quantile([.025, .975]).T.rename(columns={.025: "ci_low", .975: "ci_high"})
    intervals.insert(0, "estimate", pd.Series(evaluate(y, p, threshold)))
    risk = score_groups(y, p, groups, threshold).set_index("group")
    draws = pd.concat(risk_rows)
    for key in ["count", "positive_rate", "precision", "recall", "lift"]:
        q = draws.groupby("group")[key].quantile([.025, .975]).unstack()
        risk[key+"_ci_low"], risk[key+"_ci_high"] = q[.025], q[.975]
    return intervals.reset_index(names="metric"), risk.reset_index()


def prediction_table(y, p, threshold, groups, scope):
    scores = score_probability(p)
    names = np.full(len(scores), "", dtype=object)
    for name, (lo, hi) in groups.items():
        names[(scores >= lo) & (scores <= hi)] = name
    return pd.DataFrame(dict(row_reference=y.index, scope=scope, observed_label=np.asarray(y), probability=p,
                             prediction=(p >= threshold).astype(int), score=scores, risk_group=names))


def figures(y, p, threshold, folder, scope):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for kind in ["roc", "precision_recall", "calibration", "confusion", "score_distribution"]:
        fig, ax = plt.subplots(figsize=(6, 4))
        if kind == "roc":
            m.RocCurveDisplay.from_predictions(y, p, ax=ax)
            ax.plot([0, 1], [0, 1], "--", color="gray")
        elif kind == "precision_recall":
            m.PrecisionRecallDisplay.from_predictions(y, p, ax=ax)
            ax.axhline(np.mean(y), ls="--", color="gray", label="Label=1 prevalence")
            ax.legend()
        elif kind == "calibration":
            bins = calibration_bins(y, p)
            bins.to_csv(folder/f"calibration_bins_{scope}.csv", index=False)
            ax.plot(bins.mean_probability, bins.positive_rate, "o-")
            ax.plot([0, 1], [0, 1], "--", color="gray")
            ax.set(xlabel="Mean P(label=1)", ylabel="Observed label=1 rate")
        elif kind == "confusion":
            m.ConfusionMatrixDisplay.from_predictions(y, p >= threshold, ax=ax, colorbar=False)
        else:
            scores = score_probability(p)
            ax.hist([scores[np.asarray(y) == 0], scores[np.asarray(y) == 1]], bins=np.arange(.5, 11), stacked=True, label=["Label=0", "Label=1"])
            ax.set(xlabel="Score", ylabel="Count", xticks=range(1, 11))
            ax.legend()
        ax.set_title(f"{scope}: {kind}")
        fig.savefig(folder/f"{kind}_{scope}.png", dpi=160, bbox_inches="tight")
        plt.close(fig)

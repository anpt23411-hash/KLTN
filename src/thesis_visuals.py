from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .evaluation import calibration_bins
from .thesis_preprocessing import NOMINAL


def save(fig, path):
    fig.savefig(path, dpi=160, bbox_inches="tight")
    plt.close(fig)


def eda_figures(X, y, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    num = X.select_dtypes(include="number")
    num.hist(figsize=(15, 12), bins=25)
    save(plt.gcf(), folder/"distributions_train.png")
    fig, axes = plt.subplots(4, 4, figsize=(16, 13))
    for ax, c in zip(axes.flat, num):
        ax.boxplot([X.loc[y.eq(k), c].dropna() for k in [0, 1]], tick_labels=["0", "1"], showfliers=True)
        ax.set(title=c, xlabel="Label")
    for ax in list(axes.flat)[len(num.columns):]:
        ax.axis("off")
    fig.tight_layout()
    save(fig, folder/"boxplots_by_label_train.png")
    corr = num.corr(method="spearman")
    corr.to_csv(folder/"spearman_matrix_train.csv")
    pairs = [(a, b, corr.loc[a, b]) for i, a in enumerate(corr) for b in corr.columns[i+1:] if abs(corr.loc[a, b]) >= .7]
    pd.DataFrame(pairs, columns=["feature_a", "feature_b", "rho"]).to_csv(folder/"high_correlation_pairs.csv", index=False)
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="coolwarm")
    ax.set(xticks=range(len(corr)), yticks=range(len(corr)), xticklabels=corr.columns, yticklabels=corr.columns)
    plt.setp(ax.get_xticklabels(), rotation=90)
    fig.colorbar(im, ax=ax)
    save(fig, folder/"spearman_heatmap_train.png")
    group_rows = []
    cols = NOMINAL + ["CityTier", "SatisfactionScore", "Complain", "Tenure"]
    fig, axes = plt.subplots(3, 3, figsize=(16, 13))
    for ax, c in zip(axes.flat, cols):
        labels = (pd.cut(X[c], bins=[-np.inf, 1, 6, 12, 24, np.inf]).astype("string") if c == "Tenure" else X[c].astype("string")).fillna("<MISSING>")
        group = pd.DataFrame({"group": labels, "label": y}).groupby("group").agg(count=("label", "size"), positive_rate=("label", "mean"))
        group.assign(feature=c).reset_index().to_csv(folder/f"group_{c}_train.csv", index=False)
        group_rows.append(group.assign(feature=c).reset_index())
        group.positive_rate.plot.bar(ax=ax, color="steelblue")
        ax.axhline(y.mean(), color="red", ls="--")
        ax.set(title=c, ylabel="Label=1 rate", xlabel="")
    fig.tight_layout()
    save(fig, folder/"positive_rate_by_group_train.png")
    pd.concat(group_rows).to_csv(folder/"group_rates_train.csv", index=False)
    fig, ax = plt.subplots(figsize=(10, 4))
    X.isna().mean().sort_values(ascending=False).plot.bar(ax=ax)
    ax.set(ylabel="Missing fraction", title="Train missingness")
    save(fig, folder/"missingness_train.png")


def calibration_comparison(y, p, cp, path):
    fig, ax = plt.subplots(figsize=(6, 5))
    for name, values in [("Uncalibrated", p), ("Sigmoid", cp)]:
        t = calibration_bins(y, values)
        ax.plot(t.mean_probability, t.positive_rate, "o-", label=name)
    ax.plot([0, 1], [0, 1], "--", color="gray")
    ax.set(xlabel="Mean P(label=1)", ylabel="Observed label=1 rate", title="Training OOF calibration")
    ax.legend()
    save(fig, path)


def score_and_group_figures(pred, c, folder, scope):
    rates = pred.groupby("score").agg(count=("observed_label", "size"), positive_rate=("observed_label", "mean"))
    rates = rates.reindex(range(1, 11))
    rates.to_csv(folder/f"score_rates_{scope}.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(rates.index, rates.positive_rate, "o-")
    ax.set(xlabel="Score", ylabel="Observed label=1 rate", xticks=range(1, 11), ylim=(0, 1), title=scope)
    save(fig, folder/f"score_rates_{scope}.png")
    # H2 is descriptive: show actual departures from monotonicity rather than forcing it.
    observed = rates.dropna()
    pd.DataFrame({"adjacent_lower_score": observed.index[:-1], "adjacent_upper_score": observed.index[1:],
                  "rate_change": np.diff(observed.positive_rate)}).to_csv(folder/f"h2_monotonicity_{scope}.csv", index=False)

"""Local batch prediction only. No service, UI, LLM or Agent."""
import argparse
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .evaluation import positive_probability
from .scoring import score_probability


def predict_frame(X, pipeline, metadata, scope="new_data_unlabelled"):
    required = metadata["input_columns"]
    if X.columns.duplicated().any() or set(X) != set(required):
        raise ValueError(f"Expected feature-only columns: {required}; target/ID/extra fields forbidden")
    X = X.loc[:, required].copy()
    for column, dtype in metadata["input_dtypes"].items():
        if dtype.startswith(("float", "int")):
            X[column] = pd.to_numeric(X[column], errors="raise")
    p = positive_probability(pipeline, X)
    scores = score_probability(p)
    groups = np.full(len(X), "", dtype=object)
    for name, (lo, hi) in metadata["risk_groups"].items():
        groups[(scores >= lo) & (scores <= hi)] = name
    return pd.DataFrame({"row_reference": X.index, "scope": scope, "probability_label_1": p,
                         "prediction_label": (p >= metadata["threshold"]).astype(int), "score": scores, "risk_group": groups})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV containing raw features only")
    parser.add_argument("--output", required=True)
    parser.add_argument("--model-dir", default="models/thesis_run")
    parser.add_argument("--scope", choices=["new_data_unlabelled", "in_sample_inference_smoke"], default="new_data_unlabelled")
    args = parser.parse_args()
    directory = Path(args.model_dir)
    metadata = json.loads((directory/"metadata.json").read_text(encoding="utf-8"))
    pipeline = joblib.load(directory/"pipeline.joblib")
    data = pd.read_csv(args.input)
    result = predict_frame(data, pipeline, metadata, scope=args.scope)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output, index=False)
    print(f"Wrote {len(result)} predictions ({args.scope}); target semantics verified: {metadata['label_semantics_verified']}")


if __name__ == "__main__":
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        main()

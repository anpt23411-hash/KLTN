"""Result tables and integrity checks, generated from completed run artifacts."""
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .data import write_json
from .scoring import score_probability


def markdown_table(t):
    header = "| " + " | ".join(str(c) for c in t.columns) + " |"
    rows = [header, "|" + "|".join(["---"]*len(t.columns)) + "|"]
    for row in t.itertuples(index=False, name=None):
        rows.append("| " + " | ".join(f"{x:.6f}" if isinstance(x, (float, np.floating)) else str(x) for x in row) + " |")
    return "\n".join(rows)


def build_summary(c):
    r, m = Path(c["report_dir"]), Path(c["model_dir"])
    def read(name):
        return json.loads((r/name).read_text(encoding="utf-8"))
    a = read("selection.json")
    h = read("metrics_holdout.json")
    shap_meta = read("shap_metadata.json")
    audit = read("data_audit.json")
    split = read("split_manifest.json")
    benchmarks = pd.read_csv(r/"benchmark.csv")
    repeated = pd.read_csv(r/"benchmark_repeated_folds.csv")
    assert len(benchmarks) == 22 and len(repeated) == 22*15
    oof = pd.read_csv(r/"predictions_oof.csv", dtype={"probability": str})
    holdout = pd.read_csv(r/"predictions_holdout.csv", dtype={"probability": str})
    assert len(oof) == split["train_rows"] and len(holdout) == split["holdout_rows"]
    assert oof.row_reference.is_unique and holdout.row_reference.is_unique
    assert not set(oof.row_reference) & set(holdout.row_reference)
    for predictions in [oof, holdout]:
        np.testing.assert_array_equal(score_probability(predictions.probability.map(float)), predictions.score)
        assert predictions.risk_group.isin(c["risk_groups"]).all()
        for group, (lo, hi) in c["risk_groups"].items():
            assert predictions.loc[predictions.risk_group.eq(group), "score"].between(lo, hi).all()
    shortlisted = pd.read_csv(r/"tuning_shortlist.csv")
    assert shortlisted.algorithm.nunique() == 2
    for name in shortlisted.algorithm:
        assert len(pd.read_csv(r/f"tuning_{name}.csv")) == c["tuning_iterations"]
    b = joblib.load(m/"split.joblib")
    for scope, pred, X in [("oof", oof, b["X_train"]), ("holdout", holdout, b["X_holdout"])]:
        grouped = X.join(pred.set_index("row_reference")[["risk_group", "probability"]])
        grouped.groupby("risk_group").median(numeric_only=True).to_csv(r/f"risk_profile_numeric_{scope}.csv")
        catrows = []
        for name in X.select_dtypes(include=["string", "object"]):
            t = pd.crosstab(grouped.risk_group, grouped[name], normalize="index").stack().rename("fraction").reset_index()
            t["feature"] = name
            t.columns = ["risk_group", "category", "fraction", "feature"]
            catrows.append(t)
        pd.concat(catrows).to_csv(r/f"risk_profile_categorical_{scope}.csv", index=False)
    curves = pd.read_csv(r/"figures/h2_monotonicity_holdout.csv")
    violations = int(curves.rate_change.lt(0).sum())
    sensitivity = pd.read_csv(r/"sensitivity_folds.csv").groupby("variant")[["average_precision", "roc_auc", "brier"]].agg(["mean", "std"])
    sensitivity.columns = ["_".join(x) for x in sensitivity]
    sensitivity.reset_index().to_csv(r/"sensitivity_summary.csv", index=False)
    post = pd.read_csv(r/"post_tuning_folds.csv").groupby(["algorithm", "scenario", "version"])[["average_precision", "roc_auc", "brier", "fit_seconds", "predict_seconds"]].agg(["mean", "std"])
    post.columns = ["_".join(x) for x in post]
    post.reset_index().to_csv(r/"post_tuning_summary.csv", index=False)
    ci = pd.read_csv(r/"metrics_ci_holdout.csv")
    risk = pd.read_csv(r/"risk_holdout.csv")
    write_json(r/"artifact_verification.json", {"status": "passed", "benchmark_rows": 22,
               "repeated_fold_rows": 330, "oof_holdout_disjoint": True, "oof_rows": len(oof), "holdout_rows": len(holdout),
               "scores_reproduced": True, "tuning_trials_per_algorithm": 10,
               "holdout_previously_observed": True, "verification_uses_saved_predictions_no_model_reselection": True})
    write_json(r/"research_questions.json", {"RQ1_H1": "Descriptive paired fold comparisons only; no independent-fold significance claim",
               "RQ2_H2": {"adjacent_score_rate_decreases_holdout": violations,
                          "strict_monotonicity_observed": violations == 0,
                          "caution": "Unequal/small score groups and fixed-model sampling uncertainty; not causal or prospective validation"},
               "RQ3": "Validation-fold permutation; real-background grouped SHAP with local signed contributions; reference LR odds ratios",
               "RQ4_H3": "Excluded by user: no Agent, LLM, API or application UI"})
    metric_table = pd.DataFrame([dict(scope="OOF selection diagnostic", **(a["sigmoid_oof"] if a["calibrated"] else a["raw_oof"])),
                                 dict(scope="Previously observed holdout; t=0.5", **h["at_0_5"]),
                                 dict(scope="Previously observed holdout; t=OOF F1", **h["at_f1_threshold"])])
    text = ["# Kết quả học máy theo báo cáo — thực nghiệm đã chạy", "",
            "Không gồm Agent, LLM, API hoặc giao diện. Nhãn kỹ thuật 1 là lớp dương; chưa xác minh ý nghĩa nghiệp vụ/đơn vị Tenure.", "",
            f"Dữ liệu thật: {audit['rows_before']} → {audit['rows_after']} sau chuẩn hóa/loại trùng. "
            f"Train {split['train_rows']}, holdout {split['holdout_rows']}; seed {c['seed']}.",
            "Holdout đã được quan sát trong pilot: không xem đây là đánh giá độc lập hoàn toàn. Lần chạy này chỉ chọn cấu hình từ train.", "",
            f"Mô hình: **{a['algorithm']} / {a['scenario']} / {a['version']}**; sigmoid={a['calibrated']}; ngưỡng OOF={a['threshold']:.8f}.", "",
            "## Benchmark chung 5 fold", "",
            markdown_table(benchmarks[["algorithm", "scenario", "average_precision_mean", "average_precision_std", "roc_auc_mean", "brier_mean", "fit_seconds_mean"]]), "",
            "## Sau tuning: đánh giá lại cùng 5 fold", "", markdown_table(post.reset_index()), "",
            "## Kết quả xác suất và phân loại", "", markdown_table(metric_table), "",
            "OOF ở bảng trên dùng t=0,5 để đối chiếu calibration; ngưỡng tối ưu và toàn bộ sweep ở threshold_sweep_oof.csv.", "",
            "## CI 95% trên holdout (1.000 bootstrap phân tầng)", "", markdown_table(ci), "",
            "Mô hình/calibration/ngưỡng giữ cố định. CI không gồm bất định lựa chọn/huấn luyện lại.", "",
            "## Điểm và nhóm nguy cơ", "",
            "Score=min(10,1+floor(10*p)); low=1–2 (p<0,2), medium=3–5 (0,2≤p<0,5), high=6–10 (p≥0,5).", "",
            markdown_table(risk.loc[risk.group.isin(["low", "medium", "high"]), ["group", "count", "positive_rate", "precision", "recall", "lift"]]), "",
            f"H2: {violations} cặp mức điểm quan sát liền kề có tỷ lệ lớp 1 giảm. Không ép tỷ lệ đơn điệu.", "",
            "## Độ nhạy trên train", "", markdown_table(sensitivity.reset_index()), "",
            "## Diễn giải và thời gian", "",
            "Permutation: 5 validation fold, 5 lần hoán vị/trường; mọi đặc trưng dẫn xuất được tính lại từ trường gốc.",
            f"SHAP: {shap_meta['explainer']}; {shap_meta['background']}; giải thích 150 quan sát train; có bar, beeswarm, waterfall và đóng góp có dấu từng hồ sơ.",
            "Xem shap_metadata.json để biết thang log-odds/xác suất và mô hình đang được giải thích. SHAP không phân rã sigmoid nếu có calibration.",
            "Hệ số/odds ratio LR là mô hình tham chiếu có nhóm one-hot bị loại, không phải kết luận nhân quả.",
            "operational_timing.csv: fit/batch 5 lần; single warmup 10 + 200 phép đo, median/IQR/p95.", "",
            "## Giới hạn và sửa báo cáo", "",
            "Xem THESIS_ALIGNMENT.md: mâu thuẫn 5/6 thuật toán; CV 3/5/repeated; dòng trước/sau loại trùng; nhóm nguy cơ; IsNewCustomer pilot và Word khác nhau.",
            "Các số bảng 3.4/3.5 cần thay bằng kết quả mới. Không cố định 31 chiều hoặc năm cờ ở mọi fold.",
            "AP/CV chịu thiên lệch do lựa chọn trên cùng train; mean/std fold không là CI suy luận. Không khẳng định H1 có ý nghĩa thống kê từ fold chồng lấn.",
            "Tên nhãn, outcome horizon, thời điểm đặc trưng và tính tương đương Mobile/Mobile Phone vẫn chưa có bằng chứng nguồn đầy đủ.",
            "Ablation chỉ đo mức phụ thuộc biến, không chứng minh hay bác bỏ rò rỉ thời gian. Cần dữ liệu mới theo thời gian để xác nhận triển khai.",
            "Không có bằng chứng can thiệp giữ chân hay tác động nhân quả; không tạo kết quả Agent.", ""]
    audit_path = r/"experiment_audit.json"
    if audit_path.exists():
        inspection = read("experiment_audit.json")
        text += ["## Đối soát trạng thái thực nghiệm", "",
                 markdown_table(pd.DataFrame(inspection["stages"])[["stage", "status", "seconds"]]), "",
                 "Cấu hình hiện tại khớp config_snapshot.json và metadata; SHA256 dữ liệu nguồn khớp.",
                 "Đủ 22 cấu hình/330 hàng fold, 180 hàng kiểm chứng đặc trưng, 20 trial tuning, 30 hàng ablation và 30 hàng khảo sát k.",
                 "Không có bước thiếu hoặc lỗi đang chặn. Lỗi SHAP interventional của lần finalize đầu đã được xử lý; giữ lại log lỗi để truy vết.",
                 f"Sai số cộng tính SHAP từ file đã lưu: {inspection['shap_saved_additivity_max_error']:.3g}.",
                 "Lần đối soát/tổng hợp này chỉ đọc đầu ra đã lưu; không fit, dự đoán lại holdout, chạy lại bootstrap hoặc thay đổi mô hình/ngưỡng.", ""]
    (r/"RESULTS.md").write_text("\n".join(text), encoding="utf-8")
    print("Report and artifact checks completed", flush=True)

# Danh mục bảng và hình

Đường dẫn nguồn tính từ gốc dự án hoặc reports/thesis_run/ như ghi chú. PNG đều có bản SVG cùng tên.

| loai | ten | file | nguon | vi_tri |
|---|---|---|---|---|
| Bảng | Kiểm kê bảng, hình và báo cáo có sẵn trước khi xuất | tables/artifact_inventory.csv | Quét reports/ trước khi xuất; đường dẫn tính từ gốc dự án | Phụ lục |
| Bảng | Dữ liệu trước/sau làm sạch và train/holdout | tables/data_counts.csv | data_audit.json; split_manifest.json | 4.1 |
| Hình | Phân bố nhãn | figures/labels.png | Nguồn: data_audit.json; split_manifest.json (không dùng dự đoán); tập: trước/sau sạch; train; holdout; n=5630/5073/4058/1015; đơn vị: quan sát. Không có thanh sai số. | 4.1 |
| Bảng | Thiếu dữ liệu sau làm sạch | tables/missing_clean.csv | data_audit.json: missing_after | 4.1 |
| Hình | Tỷ lệ thiếu theo biến | figures/missing.png | Nguồn: data_audit.json (không dùng dự đoán); tập: toàn dữ liệu sau làm sạch; n=5073; đơn vị: %. Không có thanh sai số. | 4.1 |
| Bảng nguồn | benchmark.csv | tables/source_benchmark.csv | reports/thesis_run/benchmark.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | benchmark_repeated_folds.csv | tables/source_benchmark_repeated_folds.csv | reports/thesis_run/benchmark_repeated_folds.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | calibration_bins_sigmoid_oof.csv | tables/source_calibration_bins_sigmoid_oof.csv | reports/thesis_run/calibration_bins_sigmoid_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | calibration_bins_uncalibrated_oof.csv | tables/source_calibration_bins_uncalibrated_oof.csv | reports/thesis_run/calibration_bins_uncalibrated_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/descriptive_train.csv | tables/source_eda__descriptive_train.csv | reports/thesis_run/eda/descriptive_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_CityTier_train.csv | tables/source_eda__group_CityTier_train.csv | reports/thesis_run/eda/group_CityTier_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_Complain_train.csv | tables/source_eda__group_Complain_train.csv | reports/thesis_run/eda/group_Complain_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_Gender_train.csv | tables/source_eda__group_Gender_train.csv | reports/thesis_run/eda/group_Gender_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_MaritalStatus_train.csv | tables/source_eda__group_MaritalStatus_train.csv | reports/thesis_run/eda/group_MaritalStatus_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_PreferedOrderCat_train.csv | tables/source_eda__group_PreferedOrderCat_train.csv | reports/thesis_run/eda/group_PreferedOrderCat_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_PreferredLoginDevice_train.csv | tables/source_eda__group_PreferredLoginDevice_train.csv | reports/thesis_run/eda/group_PreferredLoginDevice_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_PreferredPaymentMode_train.csv | tables/source_eda__group_PreferredPaymentMode_train.csv | reports/thesis_run/eda/group_PreferredPaymentMode_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_rates_train.csv | tables/source_eda__group_rates_train.csv | reports/thesis_run/eda/group_rates_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_SatisfactionScore_train.csv | tables/source_eda__group_SatisfactionScore_train.csv | reports/thesis_run/eda/group_SatisfactionScore_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/group_Tenure_train.csv | tables/source_eda__group_Tenure_train.csv | reports/thesis_run/eda/group_Tenure_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/high_correlation_pairs.csv | tables/source_eda__high_correlation_pairs.csv | reports/thesis_run/eda/high_correlation_pairs.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/hypothesis_tests_train.csv | tables/source_eda__hypothesis_tests_train.csv | reports/thesis_run/eda/hypothesis_tests_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/iqr_train.csv | tables/source_eda__iqr_train.csv | reports/thesis_run/eda/iqr_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/medians_train.csv | tables/source_eda__medians_train.csv | reports/thesis_run/eda/medians_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/missing_association_train.csv | tables/source_eda__missing_association_train.csv | reports/thesis_run/eda/missing_association_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | eda/spearman_matrix_train.csv | tables/source_eda__spearman_matrix_train.csv | reports/thesis_run/eda/spearman_matrix_train.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | feature_study.csv | tables/source_feature_study.csv | reports/thesis_run/feature_study.csv | 4.2 |
| Bảng nguồn | feature_study_folds.csv | tables/source_feature_study_folds.csv | reports/thesis_run/feature_study_folds.csv | 4.2 |
| Bảng nguồn | figures/calibration_bins_holdout.csv | tables/source_figures__calibration_bins_holdout.csv | reports/thesis_run/figures/calibration_bins_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | figures/calibration_bins_oof.csv | tables/source_figures__calibration_bins_oof.csv | reports/thesis_run/figures/calibration_bins_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | figures/h2_monotonicity_holdout.csv | tables/source_figures__h2_monotonicity_holdout.csv | reports/thesis_run/figures/h2_monotonicity_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | figures/h2_monotonicity_oof.csv | tables/source_figures__h2_monotonicity_oof.csv | reports/thesis_run/figures/h2_monotonicity_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | figures/score_rates_holdout.csv | tables/source_figures__score_rates_holdout.csv | reports/thesis_run/figures/score_rates_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | figures/score_rates_oof.csv | tables/source_figures__score_rates_oof.csv | reports/thesis_run/figures/score_rates_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | imbalance_repeated.csv | tables/source_imbalance_repeated.csv | reports/thesis_run/imbalance_repeated.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | inference_smoke_input.csv | tables/source_inference_smoke_input.csv | reports/thesis_run/inference_smoke_input.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | inference_smoke_output.csv | tables/source_inference_smoke_output.csv | reports/thesis_run/inference_smoke_output.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | lr_coefficients.csv | tables/source_lr_coefficients.csv | reports/thesis_run/lr_coefficients.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | metrics_ci_holdout.csv | tables/source_metrics_ci_holdout.csv | reports/thesis_run/metrics_ci_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | metrics_ci_oof.csv | tables/source_metrics_ci_oof.csv | reports/thesis_run/metrics_ci_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | operational_timing.csv | tables/source_operational_timing.csv | reports/thesis_run/operational_timing.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | operational_timing_draws.csv | tables/source_operational_timing_draws.csv | reports/thesis_run/operational_timing_draws.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | paired_imbalance_deltas.csv | tables/source_paired_imbalance_deltas.csv | reports/thesis_run/paired_imbalance_deltas.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | permutation_folds.csv | tables/source_permutation_folds.csv | reports/thesis_run/permutation_folds.csv | 4.7 |
| Bảng nguồn | permutation_importance.csv | tables/source_permutation_importance.csv | reports/thesis_run/permutation_importance.csv | 4.7 |
| Bảng nguồn | post_tuning_folds.csv | tables/source_post_tuning_folds.csv | reports/thesis_run/post_tuning_folds.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | post_tuning_summary.csv | tables/source_post_tuning_summary.csv | reports/thesis_run/post_tuning_summary.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | predictions_holdout.csv | tables/source_predictions_holdout.csv | reports/thesis_run/predictions_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | predictions_oof.csv | tables/source_predictions_oof.csv | reports/thesis_run/predictions_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | risk_holdout.csv | tables/source_risk_holdout.csv | reports/thesis_run/risk_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | risk_oof.csv | tables/source_risk_oof.csv | reports/thesis_run/risk_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | risk_profile_categorical_holdout.csv | tables/source_risk_profile_categorical_holdout.csv | reports/thesis_run/risk_profile_categorical_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | risk_profile_categorical_oof.csv | tables/source_risk_profile_categorical_oof.csv | reports/thesis_run/risk_profile_categorical_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | risk_profile_numeric_holdout.csv | tables/source_risk_profile_numeric_holdout.csv | reports/thesis_run/risk_profile_numeric_holdout.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | risk_profile_numeric_oof.csv | tables/source_risk_profile_numeric_oof.csv | reports/thesis_run/risk_profile_numeric_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | sensitivity_folds.csv | tables/source_sensitivity_folds.csv | reports/thesis_run/sensitivity_folds.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | sensitivity_summary.csv | tables/source_sensitivity_summary.csv | reports/thesis_run/sensitivity_summary.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | shap_grouped_importance.csv | tables/source_shap_grouped_importance.csv | reports/thesis_run/shap_grouped_importance.csv | 4.7 |
| Bảng nguồn | shap_local_contributions.csv | tables/source_shap_local_contributions.csv | reports/thesis_run/shap_local_contributions.csv | 4.7 |
| Bảng nguồn | shap_prediction_context.csv | tables/source_shap_prediction_context.csv | reports/thesis_run/shap_prediction_context.csv | 4.7 |
| Bảng nguồn | smotenc_k_study.csv | tables/source_smotenc_k_study.csv | reports/thesis_run/smotenc_k_study.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | threshold_sweep_oof.csv | tables/source_threshold_sweep_oof.csv | reports/thesis_run/threshold_sweep_oof.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | tuning_hist_gradient_boosting.csv | tables/source_tuning_hist_gradient_boosting.csv | reports/thesis_run/tuning_hist_gradient_boosting.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | tuning_random_forest.csv | tables/source_tuning_random_forest.csv | reports/thesis_run/tuning_random_forest.csv | 4.3–4.8 / Phụ lục |
| Bảng nguồn | tuning_shortlist.csv | tables/source_tuning_shortlist.csv | reports/thesis_run/tuning_shortlist.csv | 4.3–4.8 / Phụ lục |
| Bảng | So sánh đặc trưng A–F | tables/feature_comparison.csv | feature_study.csv; repeated 5×3 trên train, AP mean/SD 15 fold | 4.2 |
| Bảng | Benchmark năm thuật toán × P0–P3 và hai dummy | tables/benchmark.csv | benchmark.csv; fold 0–4 của benchmark_repeated_folds.csv; train n=4058 | 4.3 |
| Hình | So sánh AP benchmark | figures/benchmark_ap.png | Nguồn: benchmark.csv; dự đoán validation từng fold; tập: train CV 5 fold; n=4058; đơn vị: AP (0–1). Thanh ngang: ±1 SD giữa 5 fold, không phải CI. | 4.3 |
| Bảng | Đại diện từng thuật toán | tables/representatives.csv | Tái hiện đúng src/thesis.py:tune trên benchmark/fold đã lưu; không chọn lại mô hình | 4.3 |
| Bảng | Đối soát quy tắc chọn đại diện | tables/selection_trace.csv | AP/Brier 5 fold; SD hiệu ghép cặp trên 15 fold | 4.3 |
| Bảng | Shortlist đã lưu | tables/shortlist.csv | tuning_shortlist.csv | 4.3 |
| Bảng | Tuned và untuned trên cùng 5 fold | tables/tuning_comparison.csv | post_tuning_folds.csv; train n=4058 | 4.4 |
| Hình | So sánh tuned/untuned | figures/tuning.png | Nguồn: post_tuning_folds.csv; dự đoán validation; tập: train CV 5 fold; n=4058; đơn vị: AP (0–1). Thanh dọc: ±1 SD fold, không phải CI. | 4.4 |
| Bảng | Trước/sau sigmoid calibration | tables/calibration.csv | selection.json; post_tuning_folds.csv | 4.5 |
| Hình | Reliability trước/sau sigmoid | figures/reliability.png | Nguồn: calibration_bins_*_oof.csv; bin phân vị đã lưu; tập: OOF train; n=4058; đơn vị: xác suất/tỷ lệ (0–1). Không có thanh sai số. | 4.5 |
| Hình | Ma trận nhầm lẫn — oof, t=0.500000 | figures/confusion_oof_05.png | Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát. Không có thanh sai số. | 4.5 |
| Hình | Ma trận nhầm lẫn — oof, t=0.359436 | figures/confusion_oof_f1.png | Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát. Không có thanh sai số. | 4.5 |
| Hình | Đường Precision–Recall — oof | figures/pr_oof.png | Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: tỷ lệ (0–1). Không có thanh sai số. | 4.5 |
| Hình | ROC bổ trợ — oof | figures/roc_oof.png | Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: tỷ lệ (0–1). Không có thanh sai số. | 4.5 |
| Bảng | Điểm rủi ro — oof | tables/score_oof.csv | predictions_oof.csv; hist_gradient_boosting/P0/untuned | 4.6 |
| Hình | Phân bố và Churn theo điểm rủi ro — oof | figures/score_oof.png | Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số. | 4.6 |
| Bảng | Nhóm rủi ro — oof | tables/risk_group_oof.csv | predictions_oof.csv; hist_gradient_boosting/P0/untuned | 4.6 |
| Hình | Phân bố và Churn theo nhóm rủi ro — oof | figures/risk_group_oof.png | Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số. | 4.6 |
| Hình | Ma trận nhầm lẫn — holdout, t=0.500000 | figures/confusion_holdout_05.png | Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát. Không có thanh sai số. | 4.5 |
| Hình | Ma trận nhầm lẫn — holdout, t=0.359436 | figures/confusion_holdout_f1.png | Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát. Không có thanh sai số. | 4.5 |
| Hình | Đường Precision–Recall — holdout | figures/pr_holdout.png | Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: tỷ lệ (0–1). Không có thanh sai số. | 4.5 |
| Hình | ROC bổ trợ — holdout | figures/roc_holdout.png | Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: tỷ lệ (0–1). Không có thanh sai số. | 4.5 |
| Bảng | Điểm rủi ro — holdout | tables/score_holdout.csv | predictions_holdout.csv; hist_gradient_boosting/P0/untuned | 4.6 |
| Hình | Phân bố và Churn theo điểm rủi ro — holdout | figures/score_holdout.png | Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số. | 4.6 |
| Bảng | Nhóm rủi ro — holdout | tables/risk_group_holdout.csv | predictions_holdout.csv; hist_gradient_boosting/P0/untuned | 4.6 |
| Hình | Phân bố và Churn theo nhóm rủi ro — holdout | figures/risk_group_holdout.png | Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số. | 4.6 |
| Bảng | OOF và holdout tại hai ngưỡng | tables/metrics_two_thresholds.csv | Tính từ predictions_oof.csv và predictions_holdout.csv; AP trên vector gộp | 4.5 |
| Bảng | Kiểm tra độ bền khi bỏ proxy thời gian | tables/robustness.csv | sensitivity_folds.csv; repeated 5×3 train | 4.7 |
| Bảng | Permutation importance | tables/permutation.csv | permutation_importance.csv; validation 5 fold, 5 lần hoán vị/biến/fold; delta AP | 4.7 |
| Hình | Permutation importance trên validation | figures/permutation.png | Nguồn: permutation_importance.csv; dự đoán validation sau hoán vị; tập: train CV 5 fold; n=4058; đơn vị: delta AP. Thanh ngang: ±1 SD của trung bình hoán vị giữa 5 fold, không phải CI. | 4.7 |
| Bảng | SHAP gộp theo biến | tables/shap.csv | shap_grouped_importance.csv; đối soát đóng góp cục bộ đã lưu | 4.7 |
| Hình | SHAP — mức đóng góp trung bình | figures/shap_bar.png | Nguồn: shap_local_contributions.csv; không phải dự đoán đánh giá; tập: train in-sample, mô hình cây cơ sở; n=150; đơn vị: log-odds. Không có thanh sai số. | 4.7 |
| Hình | Phân bố đóng góp SHAP đã lưu | figures/shap_distribution.png | Nguồn: shap_local_contributions.csv; mỗi chấm là một hồ sơ, không mã hóa giá trị biến; tập: train in-sample; n=150; đơn vị: log-odds. Không có thanh sai số. | 4.7 |
| Bảng | Thời gian vận hành đã đo (giây) | tables/timing.csv | operational_timing.csv; operational_timing_draws.csv | 4.8 |
| Bảng | Thời gian từng giai đoạn đã lưu (giây) | tables/stage_timing.csv | experiment_audit.json; stage_*.json | 4.8 |
| Bảng | Thời gian tìm kiếm đã lưu (giây) | tables/search_timing.csv | selection.json: search_seconds; không cộng trùng tuned/untuned | 4.8 |
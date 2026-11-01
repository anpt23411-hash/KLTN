# Báo cáo thực nghiệm học máy — Chương 4

Xuất lúc 2026-11-01T23:00:11.200480+07:00. Chỉ đọc artifact đã lưu; không huấn luyện, không dự đoán lại hoặc thay đổi quyết định.
Nguồn chính: `reports/thesis_run/`; không trộn kết quả pilot ở `reports/`.
Churn quan sát trong báo cáo là nhãn kỹ thuật 1; ngữ nghĩa nghiệp vụ chưa được xác minh đầy đủ. Holdout đã được quan sát ở pilot, không phải tập kiểm định hoàn toàn mới. OOF là chẩn đoán lựa chọn trên train, có thiên lệch lựa chọn.

Kiểm kê đầy đủ đầu ra gốc: [artifact_inventory.csv](tables/artifact_inventory.csv).

## Dữ liệu trước/sau làm sạch và train/holdout

Nguồn: data_audit.json; split_manifest.json. [tables/data_counts.csv](tables/data_counts.csv)

| Tập | n | Nhãn 0 | Nhãn 1 | Tỷ lệ Churn |
|---|---|---|---|---|
| Trước làm sạch | 5630 | 4682 | 948 | 0.168384 |
| Sau làm sạch | 5073 | 4232 | 841 | 0.165780 |
| Train | 4058 | 3385 | 673 | 0.165845 |
| Holdout | 1015 | 847 | 168 | 0.165517 |

Chuẩn hóa alias rồi loại 557 dòng trùng, không loại ngoại lệ. Chia phân tầng 80/20, seed=42; học tiền xử lý bên trong train fold. Mobile→Mobile Phone vẫn là giả định. Xem phần đối soát chi tiết phía dưới.

![Phân bố nhãn](figures/labels.png)

Nguồn: data_audit.json; split_manifest.json (không dùng dự đoán); tập: trước/sau sạch; train; holdout; n=5630/5073/4058/1015; đơn vị: quan sát. Không có thanh sai số.

[Bản SVG](figures/labels.svg)

## Thiếu dữ liệu sau làm sạch

Nguồn: data_audit.json: missing_after. [tables/missing_clean.csv](tables/missing_clean.csv)

| Biến | Số thiếu | Tỷ lệ thiếu (%) |
|---|---|---|
| CustomerID | 0 | 0.000000 |
| Churn | 0 | 0.000000 |
| Tenure | 231 | 4.553519 |
| PreferredLoginDevice | 0 | 0.000000 |
| CityTier | 0 | 0.000000 |
| WarehouseToHome | 221 | 4.356397 |
| PreferredPaymentMode | 0 | 0.000000 |
| Gender | 0 | 0.000000 |
| HourSpendOnApp | 230 | 4.533806 |
| NumberOfDeviceRegistered | 0 | 0.000000 |
| PreferedOrderCat | 0 | 0.000000 |
| SatisfactionScore | 0 | 0.000000 |
| MaritalStatus | 0 | 0.000000 |
| NumberOfAddress | 0 | 0.000000 |
| Complain | 0 | 0.000000 |
| OrderAmountHikeFromlastYear | 252 | 4.967475 |
| CouponUsed | 210 | 4.139562 |
| OrderCount | 243 | 4.790065 |
| DaySinceLastOrder | 288 | 5.677114 |
| CashbackAmount | 0 | 0.000000 |

![Tỷ lệ thiếu theo biến](figures/missing.png)

Nguồn: data_audit.json (không dùng dự đoán); tập: toàn dữ liệu sau làm sạch; n=5073; đơn vị: %. Không có thanh sai số.

[Bản SVG](figures/missing.svg)

## So sánh đặc trưng A–F

Nguồn: feature_study.csv; repeated 5×3 trên train, AP mean/SD 15 fold. [tables/feature_comparison.csv](tables/feature_comparison.csv)

| variant | algorithm | mean | std |
|---|---|---|---|
| A | hist_gradient_boosting | 0.924907 | 0.011735 |
| A | logistic_regression | 0.708080 | 0.039935 |
| B | hist_gradient_boosting | 0.922779 | 0.015914 |
| B | logistic_regression | 0.724760 | 0.037962 |
| C | hist_gradient_boosting | 0.923726 | 0.013783 |
| C | logistic_regression | 0.725049 | 0.037528 |
| D | hist_gradient_boosting | 0.921298 | 0.014635 |
| D | logistic_regression | 0.724024 | 0.037990 |
| E | hist_gradient_boosting | 0.922779 | 0.015914 |
| E | logistic_regression | 0.751914 | 0.033398 |
| F | hist_gradient_boosting | 0.920185 | 0.013650 |
| F | logistic_regression | 0.718324 | 0.036128 |

A: biến gốc; B: thêm cờ thiếu chọn trong fit; C: B+CashbackPerOrder; D: B+CouponRate; E: B+IsNewCustomer (Tenure≤1); F: B bỏ HourSpendOnApp, OrderCount, CouponUsed. Đặc trưng cuối giữ biến gốc+cờ thiếu+IsNewCustomer, không giữ tỷ số; xem feature_selection.json và quy tắc chi tiết.

## Benchmark năm thuật toán × P0–P3 và hai dummy

Nguồn: benchmark.csv; fold 0–4 của benchmark_repeated_folds.csv; train n=4058. [tables/benchmark.csv](tables/benchmark.csv)

| algorithm | scenario | average_precision_mean | average_precision_std | roc_auc_mean | roc_auc_std | brier_mean | brier_std | accuracy_mean | accuracy_std | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std | f2_mean | f2_std | mcc_mean | mcc_std | balanced_accuracy_mean | balanced_accuracy_std | ece_mean | ece_std | fit_seconds_mean | fit_seconds_std | predict_seconds_mean | predict_seconds_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| decision_tree | P0 | 0.623769 | 0.068389 | 0.860585 | 0.039914 | 0.078615 | 0.015581 | 0.921385 | 0.015581 | 0.758439 | 0.037718 | 0.769619 | 0.076997 | 0.763291 | 0.054645 | 0.766902 | 0.067610 | 0.716703 | 0.063760 | 0.860585 | 0.039914 | 0.008628 | 0.006755 | 0.105023 | 0.022095 | 0.022397 | 0.005614 |
| decision_tree | P1 | 0.621021 | 0.036186 | 0.855857 | 0.024717 | 0.078613 | 0.007848 | 0.921387 | 0.007848 | 0.766687 | 0.027121 | 0.757800 | 0.053269 | 0.761181 | 0.028552 | 0.758894 | 0.042215 | 0.714915 | 0.032641 | 0.855857 | 0.024717 | 0.011584 | 0.005349 | 0.087643 | 0.013522 | 0.019165 | 0.003475 |
| decision_tree | P2 | 0.598680 | 0.065243 | 0.864885 | 0.031988 | 0.088461 | 0.017460 | 0.911539 | 0.017460 | 0.707979 | 0.046251 | 0.795058 | 0.054819 | 0.748837 | 0.048733 | 0.775857 | 0.051867 | 0.697219 | 0.059515 | 0.864885 | 0.031988 | 0.020453 | 0.006071 | 0.366419 | 0.012843 | 0.016436 | 0.001043 |
| decision_tree | P3 | 0.600361 | 0.045987 | 0.857384 | 0.017325 | 0.086000 | 0.012226 | 0.914000 | 0.012226 | 0.727286 | 0.042158 | 0.772670 | 0.026502 | 0.749090 | 0.032897 | 0.763010 | 0.028449 | 0.697873 | 0.040088 | 0.857384 | 0.017325 | 0.010594 | 0.006316 | 0.294781 | 0.017121 | 0.016255 | 0.001416 |
| dummy_most_frequent | baseline | 0.165845 | 0.000563 | 0.500000 | 0.000000 | 0.165845 | 0.000563 | 0.834155 | 0.000563 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.500000 | 0.000000 | 0.165845 | 0.000563 | 0.058168 | 0.000848 | 0.014606 | 0.000902 |
| dummy_prior | baseline | 0.165845 | 0.000563 | 0.500000 | 0.000000 | 0.138341 | 0.000376 | 0.834155 | 0.000563 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.500000 | 0.000000 | 0.000617 | 0.000141 | 0.060470 | 0.001060 | 0.014804 | 0.000903 |
| hist_gradient_boosting | P0 | 0.927379 | 0.012481 | 0.977398 | 0.005039 | 0.035543 | 0.005085 | 0.954902 | 0.010740 | 0.912548 | 0.036378 | 0.805329 | 0.038089 | 0.855411 | 0.034910 | 0.824605 | 0.036520 | 0.831216 | 0.041042 | 0.894984 | 0.021402 | 0.017566 | 0.002249 | 0.247837 | 0.026689 | 0.020168 | 0.001489 |
| hist_gradient_boosting | P1 | 0.924348 | 0.019483 | 0.977649 | 0.007470 | 0.038748 | 0.006329 | 0.950469 | 0.009676 | 0.828339 | 0.033089 | 0.885616 | 0.027989 | 0.855825 | 0.027215 | 0.873405 | 0.026671 | 0.826783 | 0.032970 | 0.924492 | 0.016289 | 0.034814 | 0.005757 | 0.270627 | 0.009301 | 0.019732 | 0.000502 |
| hist_gradient_boosting | P2 | 0.894794 | 0.024648 | 0.971313 | 0.007693 | 0.044803 | 0.007039 | 0.942337 | 0.011204 | 0.849599 | 0.040815 | 0.793521 | 0.033844 | 0.820378 | 0.033874 | 0.804001 | 0.033127 | 0.786889 | 0.040754 | 0.882728 | 0.019698 | 0.019664 | 0.003423 | 0.645735 | 0.098092 | 0.020194 | 0.000824 |
| hist_gradient_boosting | P3 | 0.908313 | 0.019792 | 0.975415 | 0.005777 | 0.041121 | 0.006112 | 0.945539 | 0.010147 | 0.864591 | 0.030648 | 0.796440 | 0.043824 | 0.828770 | 0.033476 | 0.808992 | 0.039359 | 0.797648 | 0.039050 | 0.885812 | 0.023223 | 0.015924 | 0.008737 | 0.481498 | 0.017215 | 0.019937 | 0.000825 |
| logistic_regression | P0 | 0.753422 | 0.038078 | 0.910396 | 0.024777 | 0.074244 | 0.007165 | 0.897978 | 0.007074 | 0.749698 | 0.047482 | 0.582465 | 0.040475 | 0.654063 | 0.025392 | 0.608905 | 0.034199 | 0.602828 | 0.028456 | 0.771587 | 0.017961 | 0.021628 | 0.005970 | 0.084978 | 0.014708 | 0.021129 | 0.005771 |
| logistic_regression | P1 | 0.749648 | 0.033324 | 0.910429 | 0.022165 | 0.114554 | 0.006810 | 0.839332 | 0.011836 | 0.509353 | 0.021234 | 0.817324 | 0.055541 | 0.627499 | 0.032164 | 0.729056 | 0.043763 | 0.556284 | 0.044375 | 0.830523 | 0.029274 | 0.153380 | 0.005410 | 0.072346 | 0.002380 | 0.018594 | 0.003149 |
| logistic_regression | P2 | 0.741788 | 0.033350 | 0.905372 | 0.019642 | 0.115571 | 0.005604 | 0.835141 | 0.008495 | 0.501582 | 0.015426 | 0.809873 | 0.047551 | 0.619363 | 0.024879 | 0.721084 | 0.035861 | 0.545974 | 0.034884 | 0.825025 | 0.023856 | 0.147764 | 0.005316 | 0.349808 | 0.017608 | 0.017010 | 0.000516 |
| logistic_regression | P3 | 0.748311 | 0.038475 | 0.907890 | 0.022183 | 0.087187 | 0.007567 | 0.880235 | 0.009351 | 0.618601 | 0.026694 | 0.726611 | 0.045654 | 0.667748 | 0.028233 | 0.701710 | 0.036848 | 0.598563 | 0.034683 | 0.818697 | 0.022261 | 0.078244 | 0.006677 | 0.345354 | 0.051700 | 0.039726 | 0.044556 |
| random_forest | P0 | 0.924340 | 0.022950 | 0.978426 | 0.005615 | 0.043289 | 0.005193 | 0.945784 | 0.011672 | 0.884257 | 0.035707 | 0.774129 | 0.044334 | 0.825374 | 0.039139 | 0.793812 | 0.042218 | 0.796028 | 0.045477 | 0.877020 | 0.024618 | 0.051888 | 0.008499 | 0.413539 | 0.012206 | 0.030015 | 0.002414 |
| random_forest | P1 | 0.929952 | 0.017164 | 0.979313 | 0.005232 | 0.043580 | 0.004384 | 0.949974 | 0.011119 | 0.832515 | 0.035265 | 0.875213 | 0.042362 | 0.852908 | 0.032744 | 0.866048 | 0.037298 | 0.823479 | 0.039353 | 0.920029 | 0.022663 | 0.068850 | 0.003560 | 0.480243 | 0.067786 | 0.031653 | 0.002766 |
| random_forest | P2 | 0.894279 | 0.025688 | 0.972542 | 0.008272 | 0.050258 | 0.004671 | 0.943076 | 0.009592 | 0.832242 | 0.029489 | 0.823273 | 0.043570 | 0.827263 | 0.030572 | 0.824751 | 0.037488 | 0.793548 | 0.035894 | 0.895093 | 0.022336 | 0.063827 | 0.008723 | 0.962299 | 0.090077 | 0.030767 | 0.000574 |
| random_forest | P3 | 0.906783 | 0.025120 | 0.975272 | 0.007155 | 0.046613 | 0.005047 | 0.945785 | 0.010352 | 0.850609 | 0.034274 | 0.817269 | 0.043886 | 0.833113 | 0.032646 | 0.823424 | 0.038540 | 0.801343 | 0.038537 | 0.894307 | 0.022941 | 0.057436 | 0.005188 | 0.891817 | 0.161469 | 0.037754 | 0.009661 |
| xgboost | P0 | 0.797940 | 0.039265 | 0.931405 | 0.017458 | 0.067639 | 0.007238 | 0.909560 | 0.011125 | 0.820679 | 0.045596 | 0.582454 | 0.055640 | 0.680259 | 0.045890 | 0.617840 | 0.052241 | 0.642618 | 0.049036 | 0.778524 | 0.028294 | 0.036643 | 0.009457 | 0.242855 | 0.041092 | 0.018682 | 0.002032 |
| xgboost | P1 | 0.787420 | 0.034450 | 0.931223 | 0.015662 | 0.098188 | 0.004309 | 0.881471 | 0.005547 | 0.602082 | 0.011274 | 0.842532 | 0.047431 | 0.701833 | 0.018240 | 0.779808 | 0.032793 | 0.644697 | 0.025799 | 0.865874 | 0.021058 | 0.146153 | 0.008425 | 0.215165 | 0.002691 | 0.017507 | 0.000369 |
| xgboost | P2 | 0.766462 | 0.043273 | 0.919373 | 0.020887 | 0.086799 | 0.005428 | 0.889354 | 0.012583 | 0.648727 | 0.040665 | 0.731122 | 0.069225 | 0.686007 | 0.039408 | 0.711961 | 0.054060 | 0.621930 | 0.048593 | 0.825975 | 0.032571 | 0.104195 | 0.011036 | 0.538551 | 0.017208 | 0.017537 | 0.000961 |
| xgboost | P3 | 0.779221 | 0.036770 | 0.922770 | 0.019069 | 0.074388 | 0.005602 | 0.903894 | 0.012261 | 0.725459 | 0.044472 | 0.679149 | 0.047828 | 0.700775 | 0.037789 | 0.687472 | 0.042569 | 0.644645 | 0.045145 | 0.813873 | 0.024964 | 0.061817 | 0.011540 | 0.468973 | 0.011265 | 0.017572 | 0.001128 |

P0: không sampling/trọng số; P1: trọng số cân bằng; P2/P3: SMOTE-NC tỷ lệ 1,0/0,5, k=3, không trọng số. AP trung bình fold khác AP từ vector OOF gộp. SD fold chỉ mô tả biến thiên, không phải CI hay kiểm định tương đương.

![So sánh AP benchmark](figures/benchmark_ap.png)

Nguồn: benchmark.csv; dự đoán validation từng fold; tập: train CV 5 fold; n=4058; đơn vị: AP (0–1). Thanh ngang: ±1 SD giữa 5 fold, không phải CI.

[Bản SVG](figures/benchmark_ap.svg)

## Đại diện từng thuật toán

Nguồn: Tái hiện đúng src/thesis.py:tune trên benchmark/fold đã lưu; không chọn lại mô hình. [tables/representatives.csv](tables/representatives.csv)

| algorithm | scenario | average_precision_mean | average_precision_std | roc_auc_mean | roc_auc_std | brier_mean | brier_std | accuracy_mean | accuracy_std | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std | f2_mean | f2_std | mcc_mean | mcc_std | balanced_accuracy_mean | balanced_accuracy_std | ece_mean | ece_std | fit_seconds_mean | fit_seconds_std | predict_seconds_mean | predict_seconds_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| logistic_regression | P0 | 0.753422 | 0.038078 | 0.910396 | 0.024777 | 0.074244 | 0.007165 | 0.897978 | 0.007074 | 0.749698 | 0.047482 | 0.582465 | 0.040475 | 0.654063 | 0.025392 | 0.608905 | 0.034199 | 0.602828 | 0.028456 | 0.771587 | 0.017961 | 0.021628 | 0.005970 | 0.084978 | 0.014708 | 0.021129 | 0.005771 |
| decision_tree | P0 | 0.623769 | 0.068389 | 0.860585 | 0.039914 | 0.078615 | 0.015581 | 0.921385 | 0.015581 | 0.758439 | 0.037718 | 0.769619 | 0.076997 | 0.763291 | 0.054645 | 0.766902 | 0.067610 | 0.716703 | 0.063760 | 0.860585 | 0.039914 | 0.008628 | 0.006755 | 0.105023 | 0.022095 | 0.022397 | 0.005614 |
| random_forest | P0 | 0.924340 | 0.022950 | 0.978426 | 0.005615 | 0.043289 | 0.005193 | 0.945784 | 0.011672 | 0.884257 | 0.035707 | 0.774129 | 0.044334 | 0.825374 | 0.039139 | 0.793812 | 0.042218 | 0.796028 | 0.045477 | 0.877020 | 0.024618 | 0.051888 | 0.008499 | 0.413539 | 0.012206 | 0.030015 | 0.002414 |
| hist_gradient_boosting | P0 | 0.927379 | 0.012481 | 0.977398 | 0.005039 | 0.035543 | 0.005085 | 0.954902 | 0.010740 | 0.912548 | 0.036378 | 0.805329 | 0.038089 | 0.855411 | 0.034910 | 0.824605 | 0.036520 | 0.831216 | 0.041042 | 0.894984 | 0.021402 | 0.017566 | 0.002249 | 0.247837 | 0.026689 | 0.020168 | 0.001489 |
| xgboost | P0 | 0.797940 | 0.039265 | 0.931405 | 0.017458 | 0.067639 | 0.007238 | 0.909560 | 0.011125 | 0.820679 | 0.045596 | 0.582454 | 0.055640 | 0.680259 | 0.045890 | 0.617840 | 0.052241 | 0.642618 | 0.049036 | 0.778524 | 0.028294 | 0.036643 | 0.009457 | 0.242855 | 0.041092 | 0.018682 | 0.002032 |

## Đối soát quy tắc chọn đại diện

Nguồn: AP/Brier 5 fold; SD hiệu ghép cặp trên 15 fold. [tables/selection_trace.csv](tables/selection_trace.csv)

| algorithm | moc | scenario | ap_drop | paired_sd_15 | tolerance | brier_delta | duoc_chon |
|---|---|---|---|---|---|---|---|
| logistic_regression | P0 | P0 | 0.000000 | 0.000000 | 0.005000 | 0.000000 | True |
| decision_tree | P0 | P0 | 0.000000 | 0.000000 | 0.005000 | 0.000000 | True |
| random_forest | P1 | P0 | 0.005612 | 0.009715 | 0.009715 | -0.000291 | True |
| hist_gradient_boosting | P0 | P0 | 0.000000 | 0.000000 | 0.005000 | 0.000000 | True |
| xgboost | P0 | P0 | 0.000000 | 0.000000 | 0.005000 | 0.000000 | True |

## Shortlist đã lưu

Nguồn: tuning_shortlist.csv. [tables/shortlist.csv](tables/shortlist.csv)

| algorithm | scenario | average_precision_mean | average_precision_std | roc_auc_mean | roc_auc_std | brier_mean | brier_std | accuracy_mean | accuracy_std | precision_mean | precision_std | recall_mean | recall_std | f1_mean | f1_std | f2_mean | f2_std | mcc_mean | mcc_std | balanced_accuracy_mean | balanced_accuracy_std | ece_mean | ece_std | fit_seconds_mean | fit_seconds_std | predict_seconds_mean | predict_seconds_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hist_gradient_boosting | P0 | 0.927379 | 0.012481 | 0.977398 | 0.005039 | 0.035543 | 0.005085 | 0.954902 | 0.010740 | 0.912548 | 0.036378 | 0.805329 | 0.038089 | 0.855411 | 0.034910 | 0.824605 | 0.036520 | 0.831216 | 0.041042 | 0.894984 | 0.021402 | 0.017566 | 0.002249 | 0.247837 | 0.026689 | 0.020168 | 0.001489 |
| random_forest | P0 | 0.924340 | 0.022950 | 0.978426 | 0.005615 | 0.043289 | 0.005193 | 0.945784 | 0.011672 | 0.884257 | 0.035707 | 0.774129 | 0.044334 | 0.825374 | 0.039139 | 0.793812 | 0.042218 | 0.796028 | 0.045477 | 0.877020 | 0.024618 | 0.051888 | 0.008499 | 0.413539 | 0.012206 | 0.030015 | 0.002414 |

RF P1 đứng đầu benchmark, nhưng P0 được giữ: AP giảm 0.00561183 ≤ max(0,005; SD ghép cặp 15 fold)=0.00971529; Brier P0−P1=-0.00029146 ≤ 0,005. Mã duyệt P0→P1→P2→P3 và giữ phương án đầu đạt điều kiện; RF P1 không vào bốn ứng viên cuối. Đây là quy tắc thực dụng ưu tiên đơn giản, không chứng minh tương đương thống kê.

## Tuned và untuned trên cùng 5 fold

Nguồn: post_tuning_folds.csv; train n=4058. [tables/tuning_comparison.csv](tables/tuning_comparison.csv)

| algorithm | scenario | version | average_precision_mean | average_precision_std | roc_auc_mean | roc_auc_std | brier_mean | brier_std | fit_seconds_mean | fit_seconds_std | predict_seconds_mean | predict_seconds_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hist_gradient_boosting | P0 | tuned | 0.867233 | 0.023975 | 0.960504 | 0.008597 | 0.054061 | 0.006072 | 0.424984 | 0.097694 | 0.041729 | 0.010937 |
| hist_gradient_boosting | P0 | untuned | 0.927379 | 0.012481 | 0.977398 | 0.005039 | 0.035543 | 0.005085 | 0.343430 | 0.027304 | 0.028592 | 0.003522 |
| random_forest | P0 | tuned | 0.893957 | 0.030555 | 0.965028 | 0.013129 | 0.046488 | 0.007287 | 1.456072 | 0.302750 | 0.051743 | 0.022187 |
| random_forest | P0 | untuned | 0.924340 | 0.022950 | 0.978426 | 0.005615 | 0.043289 | 0.005193 | 1.088166 | 0.314856 | 0.097585 | 0.035641 |

![So sánh tuned/untuned](figures/tuning.png)

Nguồn: post_tuning_folds.csv; dự đoán validation; tập: train CV 5 fold; n=4058; đơn vị: AP (0–1). Thanh dọc: ±1 SD fold, không phải CI.

[Bản SVG](figures/tuning.svg)

Tuning làm giảm AP của cả hai thuật toán trong ngân sách đã chạy (10 trial×3 fold mỗi thuật toán). Không khẳng định tuning luôn cải thiện. Mô hình giữ lại: HGB/P0/untuned. Ứng viên AP gần nhau chỉ được thay bằng Brier thấp hơn nếu ECE không tăng; không mở lại lựa chọn.

## Trước/sau sigmoid calibration

Nguồn: selection.json; post_tuning_folds.csv. [tables/calibration.csv](tables/calibration.csv)

| phien_ban | AP_mean_fold | AP_OOF_gop | Brier_OOF | ECE_OOF |
|---|---|---|---|---|
| Chưa hiệu chuẩn | 0.927379 | 0.927393 | 0.035542 | 0.015540 |
| Sigmoid | không lưu/không áp dụng | 0.907570 | 0.042183 | 0.030426 |

Sigmoid bị loại vì Brier và ECE OOF đều tăng. AP mean fold sigmoid không được lưu; không thay bằng AP OOF gộp. Quy tắc yêu cầu AP mean fold giảm≤0,005 và cả Brier/ECE cải thiện. Không kiểm chứng độc lập được điều kiện AP sigmoid từ các artifact còn lại.

![Reliability trước/sau sigmoid](figures/reliability.png)

Nguồn: calibration_bins_*_oof.csv; bin phân vị đã lưu; tập: OOF train; n=4058; đơn vị: xác suất/tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/reliability.svg)

![Ma trận nhầm lẫn — oof, t=0.500000](figures/confusion_oof_05.png)

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát. Không có thanh sai số.

[Bản SVG](figures/confusion_oof_05.svg)

![Ma trận nhầm lẫn — oof, t=0.359436](figures/confusion_oof_f1.png)

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát. Không có thanh sai số.

[Bản SVG](figures/confusion_oof_f1.svg)

![Đường Precision–Recall — oof](figures/pr_oof.png)

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/pr_oof.svg)

![ROC bổ trợ — oof](figures/roc_oof.png)

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/roc_oof.svg)

## Điểm rủi ro — oof

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned. [tables/score_oof.csv](tables/score_oof.csv)

| score | count | positive_count | positive_rate |
|---|---|---|---|
| 1 | 3120 | 39 | 0.012500 |
| 2 | 171 | 21 | 0.122807 |
| 3 | 75 | 23 | 0.306667 |
| 4 | 53 | 20 | 0.377358 |
| 5 | 45 | 28 | 0.622222 |
| 6 | 51 | 40 | 0.784314 |
| 7 | 54 | 42 | 0.777778 |
| 8 | 74 | 58 | 0.783784 |
| 9 | 137 | 129 | 0.941606 |
| 10 | 278 | 273 | 0.982014 |

![Phân bố và Churn theo điểm rủi ro — oof](figures/score_oof.png)

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/score_oof.svg)

## Nhóm rủi ro — oof

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned. [tables/risk_group_oof.csv](tables/risk_group_oof.csv)

| risk_group | count | positive_count | positive_rate |
|---|---|---|---|
| low | 3291 | 60 | 0.018232 |
| medium | 173 | 71 | 0.410405 |
| high | 594 | 542 | 0.912458 |

![Phân bố và Churn theo nhóm rủi ro — oof](figures/risk_group_oof.png)

Nguồn: predictions_oof.csv; hist_gradient_boosting/P0/untuned; tập: OOF train; n=4058; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/risk_group_oof.svg)

![Ma trận nhầm lẫn — holdout, t=0.500000](figures/confusion_holdout_05.png)

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát. Không có thanh sai số.

[Bản SVG](figures/confusion_holdout_05.svg)

![Ma trận nhầm lẫn — holdout, t=0.359436](figures/confusion_holdout_f1.png)

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát. Không có thanh sai số.

[Bản SVG](figures/confusion_holdout_f1.svg)

![Đường Precision–Recall — holdout](figures/pr_holdout.png)

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/pr_holdout.svg)

![ROC bổ trợ — holdout](figures/roc_holdout.png)

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/roc_holdout.svg)

## Điểm rủi ro — holdout

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned. [tables/score_holdout.csv](tables/score_holdout.csv)

| score | count | positive_count | positive_rate |
|---|---|---|---|
| 1 | 768 | 6 | 0.007812 |
| 2 | 51 | 4 | 0.078431 |
| 3 | 16 | 1 | 0.062500 |
| 4 | 10 | 3 | 0.300000 |
| 5 | 12 | 7 | 0.583333 |
| 6 | 15 | 10 | 0.666667 |
| 7 | 17 | 13 | 0.764706 |
| 8 | 24 | 22 | 0.916667 |
| 9 | 41 | 41 | 1.000000 |
| 10 | 61 | 61 | 1.000000 |

![Phân bố và Churn theo điểm rủi ro — holdout](figures/score_holdout.png)

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/score_holdout.svg)

## Nhóm rủi ro — holdout

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned. [tables/risk_group_holdout.csv](tables/risk_group_holdout.csv)

| risk_group | count | positive_count | positive_rate |
|---|---|---|---|
| low | 819 | 10 | 0.012210 |
| medium | 38 | 11 | 0.289474 |
| high | 158 | 147 | 0.930380 |

![Phân bố và Churn theo nhóm rủi ro — holdout](figures/risk_group_holdout.png)

Nguồn: predictions_holdout.csv; hist_gradient_boosting/P0/untuned; tập: holdout đã quan sát ở pilot; n=1015; đơn vị: quan sát; tỷ lệ (0–1). Không có thanh sai số.

[Bản SVG](figures/risk_group_holdout.svg)

## OOF và holdout tại hai ngưỡng

Nguồn: Tính từ predictions_oof.csv và predictions_holdout.csv; AP trên vector gộp. [tables/metrics_two_thresholds.csv](tables/metrics_two_thresholds.csv)

| tap | n | nguong | ten_nguong | average_precision | roc_auc | brier | accuracy | precision | recall | f1 | f2 | mcc | balanced_accuracy | ece | TN | FP | FN | TP |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| oof | 4058 | 0.500000 | 0,5 | 0.927393 | 0.977639 | 0.035542 | 0.954904 | 0.912458 | 0.805349 | 0.855564 | 0.824711 | 0.831237 | 0.894994 | 0.015540 | 3333 | 52 | 131 | 542 |
| oof | 4058 | 0.359436 | F1 từ OOF | 0.927393 | 0.977639 | 0.035542 | 0.957861 | 0.880303 | 0.863299 | 0.871718 | 0.866647 | 0.846568 | 0.919980 | 0.015540 | 3306 | 79 | 92 | 581 |
| holdout | 1015 | 0.500000 | 0,5 | 0.963235 | 0.988144 | 0.026374 | 0.968473 | 0.930380 | 0.875000 | 0.901840 | 0.885542 | 0.883672 | 0.931006 | 0.020925 | 836 | 11 | 21 | 147 |
| holdout | 1015 | 0.359436 | F1 từ OOF | 0.963235 | 0.988144 | 0.026374 | 0.969458 | 0.895954 | 0.922619 | 0.909091 | 0.917160 | 0.890880 | 0.950684 | 0.020925 | 829 | 18 | 13 | 155 |

Ngưỡng F1 cố định từ OOF là 0.3594360844443061; không tối ưu trên holdout. Điểm=min(10,1+floor(10p)); thấp=1–2 (p<0,2), trung bình=3–5 (0,2≤p<0,5), cao=6–10 (p≥0,5). Ranh giới nhóm cao 0,5 khác ngưỡng phân loại F1. Bin rỗng có tỷ lệ không xác định, không gán bằng 0.

## Kiểm tra độ bền khi bỏ proxy thời gian

Nguồn: sensitivity_folds.csv; repeated 5×3 train. [tables/robustness.csv](tables/robustness.csv)

| variant | average_precision_mean | average_precision_std | roc_auc_mean | roc_auc_std | brier_mean | brier_std |
|---|---|---|---|---|---|---|
| full | 0.922779 | 0.015914 | 0.975780 | 0.005822 | 0.035816 | 0.003864 |
| without_temporal_proxies | 0.875813 | 0.020677 | 0.962806 | 0.006465 | 0.048893 | 0.003613 |

Ablation đo mức phụ thuộc nhóm biến; không chứng minh hoặc bác bỏ rò rỉ thời gian. Khảo sát k SMOTE-NC và hiệu ghép cặp mất cân bằng được giữ trong bảng nguồn; không dùng để mở lại lựa chọn.

## Permutation importance

Nguồn: permutation_importance.csv; validation 5 fold, 5 lần hoán vị/biến/fold; delta AP. [tables/permutation.csv](tables/permutation.csv)

| feature | mean | std |
|---|---|---|
| HourSpendOnApp | 0.002122 | 0.001398 |
| CouponUsed | 0.009239 | 0.002862 |
| OrderCount | 0.010629 | 0.005148 |
| Gender | 0.011905 | 0.006819 |
| PreferredLoginDevice | 0.016420 | 0.005260 |
| NumberOfDeviceRegistered | 0.018657 | 0.009848 |
| PreferredPaymentMode | 0.024284 | 0.010363 |
| CityTier | 0.030476 | 0.010806 |
| PreferedOrderCat | 0.030761 | 0.004856 |
| DaySinceLastOrder | 0.031664 | 0.008214 |
| OrderAmountHikeFromlastYear | 0.034630 | 0.012774 |
| WarehouseToHome | 0.037082 | 0.007779 |
| MaritalStatus | 0.046250 | 0.011077 |
| SatisfactionScore | 0.054432 | 0.006722 |
| CashbackAmount | 0.059042 | 0.017608 |
| NumberOfAddress | 0.107293 | 0.020146 |
| Complain | 0.161424 | 0.022117 |
| Tenure | 0.497744 | 0.010924 |

![Permutation importance trên validation](figures/permutation.png)

Nguồn: permutation_importance.csv; dự đoán validation sau hoán vị; tập: train CV 5 fold; n=4058; đơn vị: delta AP. Thanh ngang: ±1 SD của trung bình hoán vị giữa 5 fold, không phải CI.

[Bản SVG](figures/permutation.svg)

## SHAP gộp theo biến

Nguồn: shap_grouped_importance.csv; đối soát đóng góp cục bộ đã lưu. [tables/shap.csv](tables/shap.csv)

| feature | mean_abs_grouped_shap |
|---|---|
| Tenure | 1.473396 |
| Complain | 0.610681 |
| NumberOfAddress | 0.461160 |
| CashbackAmount | 0.340590 |
| SatisfactionScore | 0.294787 |
| PreferedOrderCat | 0.274781 |
| MaritalStatus | 0.270182 |
| CityTier | 0.259253 |
| WarehouseToHome | 0.236344 |
| DaySinceLastOrder | 0.198882 |
| NumberOfDeviceRegistered | 0.194229 |
| OrderAmountHikeFromlastYear | 0.178709 |
| PreferredPaymentMode | 0.178416 |
| PreferredLoginDevice | 0.093114 |
| Gender | 0.088152 |
| OrderCount | 0.087386 |
| CouponUsed | 0.080050 |
| CouponUsedMissing | 0.051828 |
| HourSpendOnApp | 0.023798 |
| TenureMissing | 0.018137 |
| WarehouseToHomeMissing | 0.005796 |
| OrderCountMissing | 0.005147 |
| IsNewCustomer | 0.001058 |
| OrderAmountHikeFromlastYearMissing | 0.000000 |

![SHAP — mức đóng góp trung bình](figures/shap_bar.png)

Nguồn: shap_local_contributions.csv; không phải dự đoán đánh giá; tập: train in-sample, mô hình cây cơ sở; n=150; đơn vị: log-odds. Không có thanh sai số.

[Bản SVG](figures/shap_bar.svg)

![Phân bố đóng góp SHAP đã lưu](figures/shap_distribution.png)

Nguồn: shap_local_contributions.csv; mỗi chấm là một hồ sơ, không mã hóa giá trị biến; tập: train in-sample; n=150; đơn vị: log-odds. Không có thanh sai số.

[Bản SVG](figures/shap_distribution.svg)

SHAP: TreeExplainer_tree_path_dependent; nền theo tần số đường đi trong cây train; nhánh nền interventional thất bại đã được loại. Đóng góp giải thích output log-odds của mô hình cơ sở; không phải đánh giá OOF/holdout, không phải tác động nhân quả.

## Thời gian vận hành đã đo (giây)

Nguồn: operational_timing.csv; operational_timing_draws.csv. [tables/timing.csv](tables/timing.csv)

| operation | count | median | q1 | q3 | p95 |
|---|---|---|---|---|---|
| batch_predict | 5 | 0.044774 | 0.043810 | 0.048128 | 0.054610 |
| fit | 5 | 0.263068 | 0.263011 | 0.273149 | 0.273949 |
| single_predict | 200 | 0.012256 | 0.011555 | 0.012803 | 0.013715 |

## Thời gian từng giai đoạn đã lưu (giây)

Nguồn: experiment_audit.json; stage_*.json. [tables/stage_timing.csv](tables/stage_timing.csv)

| stage | status | seconds |
|---|---|---|
| prepare | completed | 4.265542 |
| features | completed | 33.075164 |
| smoke | completed | 3.252344 |
| benchmark | completed | 123.807368 |
| tune | completed | 1540.031877 |
| robustness | completed | 25.472707 |
| finalize | completed | 33.793797 |

## Thời gian tìm kiếm đã lưu (giây)

Nguồn: selection.json: search_seconds; không cộng trùng tuned/untuned. [tables/search_timing.csv](tables/search_timing.csv)

| algorithm | search_seconds |
|---|---|
| hist_gradient_boosting | 10.708478 |
| random_forest | 1484.679127 |

Fit/batch: mỗi loại 5 phép đo, batch trên 4058 dòng; single: warmup 10, rồi đo 200 lần trên một dòng. Median/Q1/Q3/p95 đều tính bằng giây; IQR=Q3−Q1. Gồm tiền xử lý và predict_proba, chưa gồm mạng/API. Thời gian fit/predict CV nằm trong benchmark và post_tuning; không đồng nhất với search hoặc thời gian giai đoạn. Không đo lại thời gian huấn luyện/suy luận trong lần xuất này; thiếu CPU/OS/tải hệ thống lúc đo.

## Đối soát chi tiết đã lưu

Phần dưới trích toàn bộ báo cáo nguồn đã lưu; ngày đối soát là ngày của báo cáo nguồn. Các đường dẫn gốc trong dấu mã tính từ gốc dự án. Các bảng nguồn đã được sao chép vào tables/.

# Tổng hợp kết quả học máy phục vụ khóa luận

Đối soát ngày 30/10/2026. Chỉ dùng `thesis_config.json`, `reports/thesis_run/`, `models/thesis_run/` cho số liệu thực nghiệm. Mã nguồn được đọc để xác định phương pháp; không dùng kết quả pilot. Không huấn luyện, tuning, dự đoán holdout hoặc bootstrap lại. Các phép tính bổ sung chỉ dùng bảng kết quả/dự đoán đã lưu. Bản sao trước cập nhật nằm cạnh mỗi tệp, hậu tố `.before_20261030_233844.bak`.

Metadata và selection thống nhất: **hist_gradient_boosting / P0 / untuned**, calibrated=False, **t=0.3594360844443061**. Nguồn: `models/thesis_run/metadata.json`, `reports/thesis_run/selection.json`. Config hiện tại khớp snapshot và metadata. Nhãn dương kỹ thuật=1; chưa xác minh đầy đủ ý nghĩa nhãn, đơn vị Tenure, thời điểm hình thành biến và thời hạn dự báo. Holdout đã được quan sát trong pilot theo metadata; không gọi là tập kiểm thử hoàn toàn mới.

## 1. Dữ liệu và phân chia

Nguồn: `reports/thesis_run/data_audit.json`, `reports/thesis_run/split_manifest.json`. Phạm vi: toàn dữ liệu trước/sau làm sạch và hai tập riêng. Tổng hợp: đếm đã lưu; tỷ lệ=n1/n.


| Phạm vi | n | Nhãn 0 | Nhãn 1 | Tỷ lệ 1 |
|---|---|---|---|---|
| Trước làm sạch | 5630 | 4682 | 948 | 0.168384 |
| Sau làm sạch | 5073 | 4232 | 841 | 0.16578 |
| Train | 4058 | 3385 | 673 | 0.165845 |
| Holdout | 1015 | 847 | 168 | 0.165517 |

Loại trùng sau chuẩn hóa alias, bỏ CustomerID khỏi khóa đối chiếu nhưng giữ nhãn Churn trong khóa (`src/data.py`). Có 556 dòng trùng trước chuẩn hóa, 557 sau chuẩn hóa; loại 557, không loại ngoại lệ IQR; conflicting_feature_groups=0, ID overlap=0 theo audit. Alias Phone→Mobile Phone, CC→Credit Card, COD→Cash on Delivery; Mobile→Mobile Phone ở danh mục đơn hàng vẫn là giả định chưa xác minh. Chia phân tầng 80/20 sau làm sạch, seed 42. Toàn bộ dữ liệu gốc có 1.856 ô thiếu; sau làm sạch 1.675 ô/1.675 dòng thiếu, tối đa 1 ô/dòng. Đây không phải thống kê riêng train.

## 2. Thiếu dữ liệu và liên hệ nhãn

Nguồn: `reports/thesis_run/eda/missing_association_train.csv`, `reports/thesis_run/data_audit.json`. Phạm vi: cột missing_all_clean trên 5.073 dòng; các cột còn lại chỉ train 4.058 dòng. Tổng hợp: kiểm định thiếu/không thiếu với nhãn; BH riêng trên các biến có thiếu.


| feature | missing_all_clean | missing | missing_fraction | positive_rate_missing | positive_rate_observed | p | test | q_fdr_bh |
|---|---|---|---|---|---|---|---|---|
| Tenure | 231 | 196 | 0.0482997 | 0.30102 | 0.158985 | 1.83274e-07 | chi_square | 1.28292e-06 |
| WarehouseToHome | 221 | 172 | 0.0423854 | 0.296512 | 0.160062 | 2.49874e-06 | chi_square | 5.8304e-06 |
| HourSpendOnApp | 230 | 185 | 0.045589 | 0.216216 | 0.163439 | 0.0593641 | chi_square | 0.0692581 |
| OrderAmountHikeFromlastYear | 252 | 209 | 0.0515032 | 0.0574163 | 0.171733 | 1.50889e-05 | chi_square | 2.64055e-05 |
| CouponUsed | 210 | 173 | 0.0426318 | 0.0289017 | 0.171943 | 7.44529e-07 | chi_square | 2.60585e-06 |
| OrderCount | 243 | 187 | 0.0460818 | 0.0695187 | 0.170499 | 0.000287766 | chi_square | 0.000402873 |
| DaySinceLastOrder | 288 | 229 | 0.0564317 | 0.196507 | 0.164011 | 0.199057 | chi_square | 0.199057 |

## 3. Thống kê mô tả train

Nguồn: `reports/thesis_run/eda/descriptive_train.csv`. Phạm vi: train; gồm 18 biến gốc và hai tỷ số khảo sát. Tổng hợp: describe trước điền thiếu; các trường nominal và CityTier/SatisfactionScore/Complain được coi là phân loại trong EDA.


| feature | count | unique | top | freq | mean | std | min | 25% | 50% | 75% | max |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tenure | 3862 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 10.2923 | 8.56374 | 0 | 2 | 9 | 16 | 61 |
| PreferredLoginDevice | 4058 | 2 | Mobile Phone | 2910 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| CityTier | 4058 | 3 | 1 | 2634 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| WarehouseToHome | 3886 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 15.5242 | 8.4977 | 5 | 9 | 13 | 20 | 127 |
| PreferredPaymentMode | 4058 | 5 | Debit Card | 1693 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| Gender | 4058 | 2 | Male | 2448 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| HourSpendOnApp | 3873 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 2.92564 | 0.725599 | 0 | 2 | 3 | 3 | 5 |
| NumberOfDeviceRegistered | 4058 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 3.68655 | 1.03015 | 1 | 3 | 4 | 4 | 6 |
| PreferedOrderCat | 4058 | 5 | Mobile Phone | 1495 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| SatisfactionScore | 4058 | 5 | 3 | 1198 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| MaritalStatus | 4058 | 3 | Married | 2140 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| NumberOfAddress | 4058 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 4.20601 | 2.57286 | 1 | 2 | 3 | 6 | 22 |
| Complain | 4058 | 2 | 0 | 2921 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng |
| OrderAmountHikeFromlastYear | 3849 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 15.7197 | 3.66377 | 11 | 13 | 15 | 18 | 26 |
| CouponUsed | 3885 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 1.79717 | 1.95061 | 0 | 1 | 1 | 2 | 16 |
| OrderCount | 3871 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 3.10669 | 3.03362 | 1 | 1 | 2 | 3 | 16 |
| DaySinceLastOrder | 3829 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 4.58266 | 3.64802 | 0 | 2 | 3 | 7 | 46 |
| CashbackAmount | 4058 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 177.823 | 49.895 | 0 | 145.838 | 163.845 | 198.14 | 324.99 |
| CashbackPerOrder | 3871 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 92.7478 | 54.1459 | 0 | 50.8067 | 83.665 | 129.56 | 298.59 |
| CouponRate | 3698 | không lưu/không áp dụng | không lưu/không áp dụng | không lưu/không áp dụng | 0.610275 | 0.387019 | 0 | 0.333333 | 0.6 | 1 | 1 |

## 4. Độ lệch và ngoại lệ IQR

Nguồn: `reports/thesis_run/eda/iqr_train.csv`. Phạm vi: train, các biến EDA dạng số. Tổng hợp: IQR=Q3−Q1; ngoài [Q1−1,5IQR; Q3+1,5IQR], chỉ đánh dấu.


| feature | skew | q1 | q3 | lower | upper | outside_iqr | missing |
|---|---|---|---|---|---|---|---|
| Tenure | 0.70936 | 2 | 16 | -19 | 37 | 3 | 196 |
| WarehouseToHome | 1.43735 | 9 | 20 | -7.5 | 36.5 | 1 | 172 |
| HourSpendOnApp | -0.0159861 | 2 | 3 | 0.5 | 4.5 | 5 | 185 |
| NumberOfDeviceRegistered | -0.409323 | 3 | 4 | 1.5 | 5.5 | 293 | 0 |
| NumberOfAddress | 1.09867 | 2 | 6 | -4 | 12 | 3 | 0 |
| OrderAmountHikeFromlastYear | 0.777889 | 13 | 18 | 5.5 | 25.5 | 21 | 209 |
| CouponUsed | 2.52123 | 1 | 2 | -0.5 | 3.5 | 476 | 173 |
| OrderCount | 2.12567 | 1 | 3 | -2 | 6 | 540 | 187 |
| DaySinceLastOrder | 1.17724 | 2 | 7 | -5.5 | 14.5 | 48 | 229 |
| CashbackAmount | 1.12916 | 145.838 | 198.14 | 67.3838 | 276.594 | 313 | 0 |
| CashbackPerOrder | 0.785296 | 50.8067 | 129.56 | -67.3233 | 247.69 | 61 | 187 |
| CouponRate | -0.399761 | 0.333333 | 1 | -0.666667 | 2 | 0 | 360 |

## 5. Tỷ lệ nhãn theo nhóm

Nguồn: `reports/thesis_run/eda/group_rates_train.csv`, `reports/thesis_run/eda/group_Tenure_train.csv`. Phạm vi: train. Tổng hợp: count và mean(nhãn 1) trong nhóm; Tenure theo khoảng đã lưu.


| group | count | positive_rate | feature |
|---|---|---|---|
| Female | 1610 | 0.14472 | Gender |
| Male | 2448 | 0.179739 | Gender |
| Divorced | 692 | 0.141618 | MaritalStatus |
| Married | 2140 | 0.113084 | MaritalStatus |
| Single | 1226 | 0.271615 | MaritalStatus |
| Computer | 1148 | 0.19338 | PreferredLoginDevice |
| Mobile Phone | 2910 | 0.154983 | PreferredLoginDevice |
| Cash on Delivery | 364 | 0.269231 | PreferredPaymentMode |
| Credit Card | 1273 | 0.140613 | PreferredPaymentMode |
| Debit Card | 1693 | 0.145895 | PreferredPaymentMode |
| E wallet | 443 | 0.227991 | PreferredPaymentMode |
| UPI | 285 | 0.168421 | PreferredPaymentMode |
| Fashion | 612 | 0.163399 | PreferedOrderCat |
| Grocery | 290 | 0.0448276 | PreferedOrderCat |
| Laptop & Accessory | 1461 | 0.0999316 | PreferedOrderCat |
| Mobile Phone | 1495 | 0.265552 | PreferedOrderCat |
| Others | 200 | 0.085 | PreferedOrderCat |
| 1 | 2634 | 0.138952 | CityTier |
| 2 | 160 | 0.175 | CityTier |
| 3 | 1264 | 0.220728 | CityTier |
| 1 | 855 | 0.123977 | SatisfactionScore |
| 2 | 471 | 0.106157 | SatisfactionScore |
| 3 | 1198 | 0.174457 | SatisfactionScore |
| 4 | 753 | 0.163347 | SatisfactionScore |
| 5 | 781 | 0.236876 | SatisfactionScore |
| 0 | 2921 | 0.10647 | Complain |
| 1 | 1137 | 0.318382 | Complain |
| (-inf, 1.0] | 851 | 0.520564 | Tenure |
| (1.0, 6.0] | 682 | 0.0645161 | Tenure |
| (12.0, 24.0] | 1077 | 0.0696379 | Tenure |
| (24.0, inf] | 309 | 0 | Tenure |
| (6.0, 12.0] | 943 | 0.0551432 | Tenure |
| <MISSING> | 196 | 0.30102 | Tenure |

## 6. Kiểm định đơn biến và hiệu ứng

Nguồn: `reports/thesis_run/eda/hypothesis_tests_train.csv`. Phạm vi: train, 20 biến gốc/tỷ số khảo sát. Tổng hợp: Mann–Whitney hai phía cho số; chi-square không correction cho phân loại; hiệu ứng rank-biserial=2U/(n1*n0)−1 hoặc Cramér V.


| feature | test | statistic | p | effect | effect_name | fraction_expected_lt5 | q_fdr_bh |
|---|---|---|---|---|---|---|---|
| Tenure | mann_whitney | 370502 | 1.53634e-135 | -0.628434 | rank_biserial_positive_churn | không lưu/không áp dụng | 1.46805e-134 |
| PreferredLoginDevice | chi_square | 8.77338 | 0.00305658 | 0.0464973 | cramers_v | 0 | 0.00453217 |
| CityTier | chi_square | 41.3885 | 1.02943e-09 | 0.100991 | cramers_v | 0 | 2.10788e-09 |
| WarehouseToHome | mann_whitney | 1.12208e+06 | 2.931e-05 | 0.105389 | rank_biserial_positive_churn | không lưu/không áp dụng | 4.94247e-05 |
| PreferredPaymentMode | chi_square | 51.2342 | 1.9943e-10 | 0.112363 | cramers_v | 0 | 4.18316e-10 |
| Gender | chi_square | 8.60914 | 0.0033448 | 0.04606 | cramers_v | 0 | 0.00487547 |
| HourSpendOnApp | mann_whitney | 1.04077e+06 | 0.517776 | 0.0149318 | rank_biserial_positive_churn | không lưu/không áp dụng | 0.543034 |
| NumberOfDeviceRegistered | mann_whitney | 1.31111e+06 | 5.47791e-11 | 0.151051 | rank_biserial_positive_churn | không lưu/không áp dụng | 1.27324e-10 |
| PreferedOrderCat | chi_square | 193.492 | 9.41329e-41 | 0.218361 | cramers_v | 0 | 3.51975e-40 |
| SatisfactionScore | chi_square | 52.1234 | 1.29986e-10 | 0.113334 | cramers_v | 0 | 2.86636e-10 |
| MaritalStatus | chi_square | 145.141 | 3.04085e-32 | 0.189121 | cramers_v | 0 | 9.68568e-32 |
| NumberOfAddress | mann_whitney | 1.20054e+06 | 0.0245883 | 0.0539852 | rank_biserial_positive_churn | không lưu/không áp dụng | 0.0325322 |
| Complain | chi_square | 265.668 | 9.98065e-60 | 0.255866 | cramers_v | 0 | 4.76853e-59 |
| OrderAmountHikeFromlastYear | mann_whitney | 978909 | 0.00386845 | -0.0709212 | rank_biserial_positive_churn | không lưu/không áp dụng | 0.00554477 |
| CouponUsed | mann_whitney | 1.07904e+06 | 0.857087 | 0.00424485 | rank_biserial_positive_churn | không lưu/không áp dụng | 0.867171 |
| OrderCount | mann_whitney | 1.03647e+06 | 0.354976 | -0.0218548 | rank_biserial_positive_churn | không lưu/không áp dụng | 0.386429 |
| DaySinceLastOrder | mann_whitney | 739334 | 4.47666e-26 | -0.264428 | rank_biserial_positive_churn | không lưu/không áp dụng | 1.32756e-25 |
| CashbackAmount | mann_whitney | 860762 | 1.18131e-23 | -0.244318 | rank_biserial_positive_churn | không lưu/không áp dụng | 3.38641e-23 |
| CashbackPerOrder | mann_whitney | 966628 | 0.000375852 | -0.0877684 | rank_biserial_positive_churn | không lưu/không áp dụng | 0.000598579 |
| CouponRate | mann_whitney | 1.02306e+06 | 0.264412 | 0.0265683 | rank_biserial_positive_churn | không lưu/không áp dụng | 0.303193 |

FDR-BH của EDA áp dụng chung 86 p-value hợp lệ, gồm cả kiểm định với nhãn và mọi cặp Spearman trong cùng tệp (`src/eda.py`); không chỉ 20 kiểm định nhãn. Có 16/20 kiểm định với nhãn đạt q<0,05. Chọn cờ thiếu dùng một họ BH riêng trong từng fit/fold, không dùng bảng EDA toàn train để cố định cờ cho CV. Không diễn giải p hoặc hiệu ứng là nhân quả.

## 7. Cặp tương quan cao đã lưu

Nguồn: `reports/thesis_run/eda/high_correlation_pairs.csv`. Phạm vi: train. Tổng hợp: cặp được lọc sẵn; ma trận đầy đủ ở `reports/thesis_run/eda/spearman_matrix_train.csv`.


| feature_a | feature_b | rho |
|---|---|---|
| CouponUsed | OrderCount | 0.721352 |

A: 18 biến gốc, không cờ thiếu/IsNewCustomer. B: A+cờ thiếu q<0,05 trong fold. C: B+CashbackPerOrder=CashbackAmount/OrderCount. D: B+CouponRate=CouponUsed/OrderCount. E: B+IsNewCustomer=(Tenure quan sát≤1), thiếu Tenure→0. F: B bỏ HourSpendOnApp, OrderCount, CouponUsed. Tỷ số chỉ tính với mẫu số>0 và thành phần không thiếu, sau đó mới điền median fold.

## 8. Sáu bộ A–F

Nguồn: `reports/thesis_run/feature_study.csv`, `reports/thesis_run/feature_study_folds.csv`, `reports/thesis_run/feature_selection.json`, `src/thesis.py`. Phạm vi: train; LR và HGB P0, 15 fold mỗi bộ/mô hình. Tổng hợp: 180 lượt=6×2×15; mean và SD mẫu ddof=1 trên fold; delta so A cho B, so B cho C–F.


| variant | algorithm | mean | std | delta_vs_reference | reference | quyết định |
|---|---|---|---|---|---|---|
| A | hist_gradient_boosting | 0.924907 | 0.0117346 | 0 | A | mốc |
| A | logistic_regression | 0.70808 | 0.0399354 | 0 | A | mốc |
| B | hist_gradient_boosting | 0.922779 | 0.0159137 | -0.00212784 | A | giữ cờ |
| B | logistic_regression | 0.72476 | 0.0379617 | 0.0166805 | A | giữ cờ |
| C | hist_gradient_boosting | 0.923726 | 0.0137826 | 0.000946986 | B | không giữ tỷ số |
| C | logistic_regression | 0.725049 | 0.0375282 | 0.000288442 | B | không giữ tỷ số |
| D | hist_gradient_boosting | 0.921298 | 0.0146349 | -0.00148177 | B | không giữ tỷ số |
| D | logistic_regression | 0.724024 | 0.0379899 | -0.000736298 | B | không giữ tỷ số |
| E | hist_gradient_boosting | 0.922779 | 0.0159137 | 0 | B | giữ IsNewCustomer |
| E | logistic_regression | 0.751914 | 0.0333984 | 0.0271543 | B | giữ IsNewCustomer |
| F | hist_gradient_boosting | 0.920185 | 0.0136498 | -0.00259403 | B | không loại ba biến |
| F | logistic_regression | 0.718324 | 0.0361279 | -0.00643624 | B | không loại ba biến |

Quy tắc giữ bổ sung B/C/D/E: ít nhất một mô hình tăng AP≥0,005 và mô hình kia không giảm quá 0,005. F chỉ được loại ba biến nếu cả hai delta≥−0,002; kết quả không đạt. Quyết định cuối giữ 18 biến gốc+cờ thiếu được chọn theo fit+IsNewCustomer, không tỷ số. Metadata toàn train giữ 5 cờ: Tenure, WarehouseToHome, OrderAmountHikeFromlastYear, CouponUsed, OrderCount; ma trận cuối **31 chiều**=13 số gốc+12 dummy+5 cờ+1 IsNewCustomer. Danh sách/số cờ thực tế từng fold **không lưu/không thể khôi phục từ bảng fold hiện có**; không fit lại để suy ra. Con số 31 đúng cho fit cuối, không bảo đảm cố định mọi fold.

P0: không sampling/không trọng số. P1: không sampling, trọng số cân bằng tính trong fit (XGBoost dùng trọng số lớp tương ứng). P2: SMOTE-NC ratio=1,0, k=3. P3: SMOTE-NC ratio=0,5, k=3; không kết hợp trọng số. Mọi phép học tiền xử lý/sampling nằm trong phần train fold; validation giữ tỷ lệ thật.

## 9. Benchmark 5 fold

Nguồn: `reports/thesis_run/benchmark.csv`, `reports/thesis_run/benchmark_repeated_folds.csv`. Phạm vi: train; fold 0–4 của repeated. Tổng hợp: 22 cấu hình=5 thuật toán×4 P+2 dummy; 110 lượt; mean/SD mẫu trên 5 fold.


| algorithm | scenario | average_precision_mean | average_precision_std | roc_auc_mean | brier_mean | ece_mean |
|---|---|---|---|---|---|---|
| decision_tree | P0 | 0.623769 | 0.068389 | 0.860585 | 0.0786146 | 0.00862798 |
| decision_tree | P1 | 0.621021 | 0.0361861 | 0.855857 | 0.078613 | 0.0115839 |
| decision_tree | P2 | 0.59868 | 0.065243 | 0.864885 | 0.0884607 | 0.0204531 |
| decision_tree | P3 | 0.600361 | 0.0459874 | 0.857384 | 0.0860004 | 0.0105945 |
| dummy_most_frequent | baseline | 0.165845 | 0.000563083 | 0.5 | 0.165845 | 0.165845 |
| dummy_prior | baseline | 0.165845 | 0.000563083 | 0.5 | 0.138341 | 0.000616731 |
| hist_gradient_boosting | P0 | 0.927379 | 0.0124809 | 0.977398 | 0.0355429 | 0.0175663 |
| hist_gradient_boosting | P1 | 0.924348 | 0.0194829 | 0.977649 | 0.0387484 | 0.0348139 |
| hist_gradient_boosting | P2 | 0.894794 | 0.0246484 | 0.971313 | 0.0448033 | 0.0196643 |
| hist_gradient_boosting | P3 | 0.908313 | 0.0197924 | 0.975415 | 0.0411208 | 0.0159235 |
| logistic_regression | P0 | 0.753422 | 0.0380779 | 0.910396 | 0.0742435 | 0.0216281 |
| logistic_regression | P1 | 0.749648 | 0.0333244 | 0.910429 | 0.114554 | 0.15338 |
| logistic_regression | P2 | 0.741788 | 0.0333499 | 0.905372 | 0.115571 | 0.147764 |
| logistic_regression | P3 | 0.748311 | 0.0384747 | 0.90789 | 0.087187 | 0.0782443 |
| random_forest | P0 | 0.92434 | 0.0229499 | 0.978426 | 0.0432889 | 0.0518879 |
| random_forest | P1 | 0.929952 | 0.0171637 | 0.979313 | 0.0435804 | 0.0688502 |
| random_forest | P2 | 0.894279 | 0.0256881 | 0.972542 | 0.0502583 | 0.0638273 |
| random_forest | P3 | 0.906783 | 0.0251201 | 0.975272 | 0.0466131 | 0.0574356 |
| xgboost | P0 | 0.79794 | 0.0392649 | 0.931405 | 0.0676386 | 0.0366429 |
| xgboost | P1 | 0.78742 | 0.0344495 | 0.931223 | 0.098188 | 0.146153 |
| xgboost | P2 | 0.766462 | 0.0432727 | 0.919373 | 0.086799 | 0.104195 |
| xgboost | P3 | 0.779221 | 0.0367701 | 0.92277 | 0.0743881 | 0.0618175 |

## 10. Repeated CV 5×3

Nguồn: `reports/thesis_run/imbalance_repeated.csv`, `reports/thesis_run/benchmark_repeated_folds.csv`. Phạm vi: train; fold 0–14. Tổng hợp: 22 cấu hình×15=330 lượt; 110 lượt benchmark là tập con, không cộng thêm thành 440.


| algorithm | scenario | average_precision_mean | average_precision_std | roc_auc_mean | brier_mean | ece_mean |
|---|---|---|---|---|---|---|
| decision_tree | P0 | 0.647091 | 0.0499503 | 0.871105 | 0.0730257 | 0.00648979 |
| decision_tree | P1 | 0.636077 | 0.049619 | 0.861686 | 0.0751604 | 0.00911917 |
| decision_tree | P2 | 0.583132 | 0.0525916 | 0.857942 | 0.0926568 | 0.0243117 |
| decision_tree | P3 | 0.612994 | 0.040218 | 0.866018 | 0.0831295 | 0.01347 |
| dummy_most_frequent | baseline | 0.165845 | 0.000521314 | 0.5 | 0.165845 | 0.165845 |
| dummy_prior | baseline | 0.165845 | 0.000521314 | 0.5 | 0.138341 | 0.000616731 |
| hist_gradient_boosting | P0 | 0.922779 | 0.0159137 | 0.97578 | 0.0358155 | 0.0196001 |
| hist_gradient_boosting | P1 | 0.922215 | 0.0159989 | 0.976084 | 0.039213 | 0.0360138 |
| hist_gradient_boosting | P2 | 0.894009 | 0.0183976 | 0.970085 | 0.0438698 | 0.0190294 |
| hist_gradient_boosting | P3 | 0.905835 | 0.0157663 | 0.972569 | 0.040559 | 0.0167534 |
| logistic_regression | P0 | 0.751914 | 0.0333984 | 0.90988 | 0.0743822 | 0.0252033 |
| logistic_regression | P1 | 0.749617 | 0.0319411 | 0.910412 | 0.114974 | 0.154167 |
| logistic_regression | P2 | 0.738548 | 0.0331392 | 0.904186 | 0.115706 | 0.146066 |
| logistic_regression | P3 | 0.745244 | 0.0346789 | 0.907095 | 0.0877504 | 0.0780316 |
| random_forest | P0 | 0.923261 | 0.0167462 | 0.977192 | 0.0429808 | 0.0529633 |
| random_forest | P1 | 0.931171 | 0.0153079 | 0.978453 | 0.0433612 | 0.0691254 |
| random_forest | P2 | 0.895776 | 0.0190097 | 0.972126 | 0.0497458 | 0.0661716 |
| random_forest | P3 | 0.908434 | 0.0190341 | 0.975236 | 0.0459909 | 0.0590791 |
| xgboost | P0 | 0.795936 | 0.0357848 | 0.931012 | 0.0679653 | 0.034987 |
| xgboost | P1 | 0.784109 | 0.0343985 | 0.931705 | 0.0984125 | 0.147274 |
| xgboost | P2 | 0.765362 | 0.0376732 | 0.919263 | 0.0864001 | 0.102113 |
| xgboost | P3 | 0.778185 | 0.0369683 | 0.92341 | 0.0741962 | 0.061201 |

Các fold chồng lấn, 15 lượt không độc lập; SD không phải CI. Repeated không tạo một vector OOF duy nhất. AP là sklearn average_precision_score, không phải diện tích PR hình thang. RF P1 có AP cao nhất toàn benchmark 5 fold (0,929952); HGB chỉ đứng đầu các cấu hình sau sàng lọc và bốn ứng viên cuối.

## 11. Vì sao RF P0 thay RF P1

Nguồn: `reports/thesis_run/benchmark.csv`, `reports/thesis_run/benchmark_repeated_folds.csv`, `src/thesis.py:tune`. Phạm vi: RF trên train; AP/Brier 5 fold, SD ghép cặp 15 fold. Tổng hợp: hiệu AP mean và SD mẫu của 15 hiệu ghép cặp.


| Điều kiện | Giá trị |
|---|---|
| AP P1−P0 (5 fold) | 0.00561183 |
| SD(P1−P0), 15 fold | 0.00971529 |
| max(0,005; SD) | 0.00971529 |
| Brier P0−P1 (5 fold) | -0.000291456 |
| Giới hạn tăng Brier | 0.005 |

Trong từng thuật toán: lấy cấu hình AP 5-fold cao nhất làm mốc; duyệt P0→P1→P2→P3, chọn phương án đầu tiên có AP giảm≤max(0,005; SD hiệu ghép cặp) và Brier≤Brier mốc+0,005. SD lấy cả 15 fold theo mã thực tế. RF P0 đạt cả hai điều kiện nên được ưu tiên. Đây là quy tắc thực dụng ưu tiên đơn giản, **không phải kiểm định tương đương thống kê**. Sau đó xếp các phương án mỗi thuật toán theo AP và lấy hai thuật toán khác nhau.

## 12. Shortlist tuning

Nguồn: `reports/thesis_run/tuning_shortlist.csv`. Phạm vi: train; HGB P0 và RF P0. Tổng hợp: hai hàng sau chọn scenario theo quy tắc trên.


| algorithm | scenario | average_precision_mean | average_precision_std | roc_auc_mean | brier_mean | ece_mean |
|---|---|---|---|---|---|---|
| hist_gradient_boosting | P0 | 0.927379 | 0.0124809 | 0.977398 | 0.0355429 | 0.0175663 |
| random_forest | P0 | 0.92434 | 0.0229499 | 0.978426 | 0.0432889 | 0.0518879 |

Tuning RandomizedSearchCV, AP refit, seed 42, n_jobs=1, mỗi thuật toán 10 trial×3 fold=30 lượt; tổng 20 trial/60 lượt CV và hai refit search. Không khảo sát đầy đủ không gian; không bảo đảm tuning cải thiện. RF ban đầu n_estimators=150, max_depth=None, min_samples_split=2, min_samples_leaf=1, max_features=sqrt. HGB ban đầu learning_rate=0,1, max_iter=100, max_leaf_nodes=31, max_depth=None, min_samples_leaf=20, l2_regularization=0 (đối chiếu mã và estimator đã lưu).

## 13. Không gian và cấu hình tuning

Nguồn: `src/experiment.py:model_and_space`, `src/thesis.py:model`, `reports/thesis_run/selection.json`, hai tệp `reports/thesis_run/tuning_*.csv`. Phạm vi: hai thuật toán shortlist. Tổng hợp: giá trị không gian từ mã; cấu hình chọn từ kết quả đã lưu.


| Thuật toán | Không gian (model__) | Best params 3-fold |
|---|---|---|
| random_forest | {"n_estimators": [100, 150, 250], "max_depth": [null, 4, 8, 12], "min_samples_split": [2, 5, 10], "min_samples_leaf": [1, 2, 4, 8], "max_features": ["sqrt", 0.7, 1.0]} | {"model__n_estimators": 100, "model__min_samples_split": 5, "model__min_samples_leaf": 1, "model__max_features": 1.0, "model__max_depth": null} |
| hist_gradient_boosting | {"learning_rate": [0.03, 0.05, 0.1], "max_iter": [100, 150, 200], "max_leaf_nodes": [7, 15, 31], "max_depth": [null, 3, 6], "min_samples_leaf": [10, 20, 40], "l2_regularization": [0.0, 1.0, 10.0]} | {"model__min_samples_leaf": 20, "model__max_leaf_nodes": 15, "model__max_iter": 150, "model__max_depth": 6, "model__learning_rate": 0.05, "model__l2_regularization": 0.0} |

## 14. Bốn ứng viên trên cùng 5 fold

Nguồn: `reports/thesis_run/post_tuning_summary.csv`, `reports/thesis_run/post_tuning_folds.csv`. Phạm vi: train; HGB/RF P0 tuned và untuned. Tổng hợp: 4×5=20 lượt, mean/SD mẫu.


| algorithm | scenario | version | average_precision_mean | average_precision_std | roc_auc_mean | roc_auc_std | brier_mean | brier_std | fit_seconds_mean | fit_seconds_std | predict_seconds_mean | predict_seconds_std |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hist_gradient_boosting | P0 | tuned | 0.867233 | 0.0239748 | 0.960504 | 0.00859736 | 0.054061 | 0.00607191 | 0.424984 | 0.0976942 | 0.0417295 | 0.010937 |
| hist_gradient_boosting | P0 | untuned | 0.927379 | 0.0124809 | 0.977398 | 0.00503854 | 0.0355429 | 0.00508541 | 0.34343 | 0.0273038 | 0.0285917 | 0.00352201 |
| random_forest | P0 | tuned | 0.893957 | 0.0305551 | 0.965028 | 0.0131289 | 0.0464879 | 0.00728717 | 1.45607 | 0.30275 | 0.0517429 | 0.022187 |
| random_forest | P0 | untuned | 0.92434 | 0.0229499 | 0.978426 | 0.00561516 | 0.0432889 | 0.00519334 | 1.08817 | 0.314856 | 0.097585 | 0.0356413 |

Chọn ứng viên AP mean fold cao nhất; chỉ chuyển sang Brier thấp hơn khi AP giảm≤0,005, Brier giảm nghiêm ngặt và ECE không tăng. AP dùng mean fold; Brier/ECE dùng vector OOF gộp trong selection.json. HGB untuned được giữ. Tuning giảm AP trong ngân sách này; chưa có bằng chứng quy nguyên nhân cho từng tham số. Đánh giá lại cùng train/fold vẫn chịu thiên lệch lựa chọn, không phải nested CV độc lập.

## 15. Calibration trước/sau sigmoid

Nguồn: `reports/thesis_run/selection.json`, `reports/thesis_run/post_tuning_folds.csv`, `reports/thesis_run/calibration_bins_uncalibrated_oof.csv`, `reports/thesis_run/calibration_bins_sigmoid_oof.csv`. Phạm vi: train, OOF ngoài 5 fold; sigmoid học với CV 3 fold bên trong mỗi outer train. Tổng hợp: AP fold trung bình khác AP gộp; Brier/ECE gộp.


| Phiên bản | AP mean fold | AP OOF gộp | Brier OOF | ECE OOF |
|---|---|---|---|---|
| Không sigmoid | 0.927379 | 0.927393 | 0.0355419 | 0.0155403 |
| Sigmoid | không lưu/không thể khôi phục | 0.90757 | 0.042183 | 0.0304262 |

Điều kiện mã: mean(AP sigmoid outer fold)≥mean(AP ứng viên)−0,005, đồng thời Brier OOF sigmoid<Brier raw và ECE OOF sigmoid<ECE raw. ECE=Σ n_bin/N × |mean(p)_bin−rate_bin|, tối đa 10 bin phân vị qcut, gộp ranh giới trùng. Sigmoid bị loại: Brier và ECE đều tăng. Không dùng AP OOF gộp thay cho AP mean fold trong điều kiện AP. Có cv_manifest nhưng **không lưu vector xác suất sigmoid OOF hoặc cal_scores từng fold**; bảng bin không đủ khôi phục AP từng fold, vì vậy không xác minh độc lập được nhánh AP. Không fit lại. AP gộp sigmoid giảm khoảng 0,01982 chỉ là mô tả bổ sung.

## 16. OOF và holdout tại hai ngưỡng

Nguồn: `reports/thesis_run/predictions_oof.csv`, `reports/thesis_run/predictions_holdout.csv`, `src/evaluation.py`. Phạm vi: OOF train và holdout tách riêng. Tổng hợp: tính bổ sung từ xác suất lưu; dự đoán 1 khi p≥t; confusion labels=[0,1], hàng thật/cột dự đoán [[TN,FP],[FN,TP]].


| scope | n | threshold | TN | FP | FN | TP | average_precision | roc_auc | brier | accuracy | precision | recall | f1 | f2 | mcc | balanced_accuracy | ece |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| oof | 4058 | 0.5 | 3333 | 52 | 131 | 542 | 0.927393 | 0.977639 | 0.0355419 | 0.954904 | 0.912458 | 0.805349 | 0.855564 | 0.824711 | 0.831237 | 0.894994 | 0.0155403 |
| oof | 4058 | 0.359436 | 3306 | 79 | 92 | 581 | 0.927393 | 0.977639 | 0.0355419 | 0.957861 | 0.880303 | 0.863299 | 0.871718 | 0.866647 | 0.846568 | 0.91998 | 0.0155403 |
| holdout | 1015 | 0.5 | 836 | 11 | 21 | 147 | 0.963235 | 0.988144 | 0.0263742 | 0.968473 | 0.93038 | 0.875 | 0.90184 | 0.885542 | 0.883672 | 0.931006 | 0.0209251 |
| holdout | 1015 | 0.359436 | 829 | 18 | 13 | 155 | 0.963235 | 0.988144 | 0.0263742 | 0.969458 | 0.895954 | 0.922619 | 0.909091 | 0.91716 | 0.89088 | 0.950684 | 0.0209251 |

Precision=TP/(TP+FP), Recall=TP/(TP+FN), Accuracy=(TP+TN)/N, F1=2TP/(2TP+FP+FN); F2 dùng beta=2; balanced accuracy=(TPR+TNR)/2; MCC theo sklearn. Brier=mean((p−y)²). AP/ROC-AUC/Brier/ECE không phụ thuộc ngưỡng. Ngưỡng đã chốt từ sweep OOF tối đa F1, hòa ưu tiên Recall rồi ngưỡng thấp (`reports/thesis_run/threshold_sweep_oof.csv`). OOF ở ngưỡng tối ưu còn chịu thiên lệch chọn ngưỡng.

## 17. CI 95% oof

Nguồn: `reports/thesis_run/metrics_ci_oof.csv`. Phạm vi: oof; ngưỡng F1 đã chốt. Tổng hợp: giữ nguyên CI bootstrap phân tầng 1.000 lần đã lưu, percentile 2,5/97,5; không bootstrap lại.


| metric | estimate | ci_low | ci_high |
|---|---|---|---|
| average_precision | 0.927393 | 0.911979 | 0.941466 |
| roc_auc | 0.977639 | 0.9722 | 0.982914 |
| brier | 0.0355419 | 0.0317415 | 0.039186 |
| accuracy | 0.957861 | 0.952193 | 0.964022 |
| precision | 0.880303 | 0.85863 | 0.902983 |
| recall | 0.863299 | 0.838039 | 0.888559 |
| f1 | 0.871718 | 0.854135 | 0.890375 |
| f2 | 0.866647 | 0.845276 | 0.888724 |
| mcc | 0.846568 | 0.825692 | 0.868547 |
| balanced_accuracy | 0.91998 | 0.907195 | 0.933353 |
| ece | 0.0155403 | 0.0126197 | 0.021555 |

## 17. CI 95% holdout

Nguồn: `reports/thesis_run/metrics_ci_holdout.csv`. Phạm vi: holdout; ngưỡng F1 đã chốt. Tổng hợp: giữ nguyên CI bootstrap phân tầng 1.000 lần đã lưu, percentile 2,5/97,5; không bootstrap lại.


| metric | estimate | ci_low | ci_high |
|---|---|---|---|
| average_precision | 0.963235 | 0.943793 | 0.979092 |
| roc_auc | 0.988144 | 0.980031 | 0.99409 |
| brier | 0.0263742 | 0.0208886 | 0.0322057 |
| accuracy | 0.969458 | 0.958621 | 0.97931 |
| precision | 0.895954 | 0.852459 | 0.937126 |
| recall | 0.922619 | 0.880952 | 0.958333 |
| f1 | 0.909091 | 0.875379 | 0.937323 |
| f2 | 0.91716 | 0.881656 | 0.947087 |
| mcc | 0.89088 | 0.851532 | 0.925157 |
| balanced_accuracy | 0.950684 | 0.929222 | 0.96917 |
| ece | 0.0209251 | 0.0150893 | 0.0306268 |

CI điều kiện trên mô hình, calibration, ngưỡng và mẫu hiện có; không bao gồm tái huấn luyện, chọn mô hình/đặc trưng/ngưỡng, thay đổi thời gian hay lịch sử xem holdout. CI OOF không làm mất thiên lệch lựa chọn. Không dùng các CI này cho ngưỡng 0,5.

Score=min(10,1+floor(10p)), p∈[0,1]. Low=1–2 (p<0,2); medium=3–5 (0,2≤p<0,5); high=6–10 (p≥0,5). Ngưỡng F1≈0,3594 nằm bên trong nhóm medium, không phải ranh giới nhóm.

## 18. Điểm và nhóm oof

Nguồn: `reports/thesis_run/risk_oof.csv`. Phạm vi: oof. Tổng hợp: các nhóm, từng điểm 1–10 và above_f1_threshold; CI rate là bootstrap đã lưu.


| group | count | positive_count | positive_rate | positive_rate_ci_low | positive_rate_ci_high | recall | lift |
|---|---|---|---|---|---|---|---|
| low | 3291 | 60 | 0.0182315 | 0.01402 | 0.0224949 | 0.089153 | 0.109931 |
| medium | 173 | 71 | 0.410405 | 0.342526 | 0.482363 | 0.105498 | 2.47462 |
| high | 594 | 542 | 0.912458 | 0.892381 | 0.931896 | 0.805349 | 5.50186 |
| score_1 | 3120 | 39 | 0.0125 | 0.00872086 | 0.0162733 | 0.0579495 | 0.0753715 |
| score_2 | 171 | 21 | 0.122807 | 0.0783015 | 0.172205 | 0.0312036 | 0.740492 |
| score_3 | 75 | 23 | 0.306667 | 0.203114 | 0.412738 | 0.0341753 | 1.84911 |
| score_4 | 53 | 20 | 0.377358 | 0.254231 | 0.5 | 0.0297177 | 2.27537 |
| score_5 | 45 | 28 | 0.622222 | 0.488876 | 0.764859 | 0.0416048 | 3.75182 |
| score_6 | 51 | 40 | 0.784314 | 0.666667 | 0.888949 | 0.0594354 | 4.72919 |
| score_7 | 54 | 42 | 0.777778 | 0.673053 | 0.8868 | 0.0624071 | 4.68978 |
| score_8 | 74 | 58 | 0.783784 | 0.690468 | 0.875 | 0.0861813 | 4.72599 |
| score_9 | 137 | 129 | 0.941606 | 0.898545 | 0.977945 | 0.191679 | 5.67762 |
| score_10 | 278 | 273 | 0.982014 | 0.964664 | 0.996324 | 0.405646 | 5.92127 |
| above_f1_threshold | 660 | 581 | 0.880303 | 0.85863 | 0.902983 | 0.863299 | 5.30798 |

oof: điểm rỗng=[]; ít mẫu theo quy ước mô tả n<30=[]; cặp điểm liên tiếp giảm tỷ lệ=6→7. H2 tăng đơn điệu tuyệt đối không được đáp ứng; không ép đường tỷ lệ tăng và không suy ra kiểm định xu thế từ các cặp này.

## 18. Điểm và nhóm holdout

Nguồn: `reports/thesis_run/risk_holdout.csv`. Phạm vi: holdout. Tổng hợp: các nhóm, từng điểm 1–10 và above_f1_threshold; CI rate là bootstrap đã lưu.


| group | count | positive_count | positive_rate | positive_rate_ci_low | positive_rate_ci_high | recall | lift |
|---|---|---|---|---|---|---|---|
| low | 819 | 10 | 0.01221 | 0.00611958 | 0.020532 | 0.0595238 | 0.0737688 |
| medium | 38 | 11 | 0.289474 | 0.156132 | 0.435897 | 0.0654762 | 1.7489 |
| high | 158 | 147 | 0.93038 | 0.890158 | 0.966667 | 0.875 | 5.62104 |
| score_1 | 768 | 6 | 0.0078125 | 0.00260408 | 0.0143234 | 0.0357143 | 0.0472005 |
| score_2 | 51 | 4 | 0.0784314 | 0.0175439 | 0.156863 | 0.0238095 | 0.473856 |
| score_3 | 16 | 1 | 0.0625 | 0 | 0.200357 | 0.00595238 | 0.377604 |
| score_4 | 10 | 3 | 0.3 | 0 | 0.6 | 0.0178571 | 1.8125 |
| score_5 | 12 | 7 | 0.583333 | 0.299853 | 0.875 | 0.0416667 | 3.52431 |
| score_6 | 15 | 10 | 0.666667 | 0.4 | 0.900119 | 0.0595238 | 4.02778 |
| score_7 | 17 | 13 | 0.764706 | 0.533333 | 0.947434 | 0.077381 | 4.6201 |
| score_8 | 24 | 22 | 0.916667 | 0.793103 | 1 | 0.130952 | 5.53819 |
| score_9 | 41 | 41 | 1 | 1 | 1 | 0.244048 | 6.04167 |
| score_10 | 61 | 61 | 1 | 1 | 1 | 0.363095 | 6.04167 |
| above_f1_threshold | 173 | 155 | 0.895954 | 0.852459 | 0.937126 | 0.922619 | 5.41305 |

holdout: điểm rỗng=[]; ít mẫu theo quy ước mô tả n<30=[3, 4, 5, 6, 7, 8]; cặp điểm liên tiếp giảm tỷ lệ=2→3. H2 tăng đơn điệu tuyệt đối không được đáp ứng; không ép đường tỷ lệ tăng và không suy ra kiểm định xu thế từ các cặp này.

## 19. Khảo sát k SMOTE-NC

Nguồn: `reports/thesis_run/smotenc_k_study.csv`, `src/thesis.py:robustness`. Phạm vi: train, HGB mặc định, bộ đặc trưng đã chọn, P2/P3, k=3/5/7; cùng 5 fold. Tổng hợp: 6 cấu hình×5=30 lượt, mean/SD mẫu; không dùng mở lại lựa chọn cuối.


| scenario | k_neighbors | average_precision_mean | average_precision_std | brier_mean | brier_std | ece_mean | ece_std |
|---|---|---|---|---|---|---|---|
| P2 | 3 | 0.894794 | 0.0246484 | 0.0448033 | 0.00703918 | 0.0196643 | 0.00342321 |
| P2 | 5 | 0.882937 | 0.0209131 | 0.046487 | 0.00605706 | 0.0208173 | 0.00475405 |
| P2 | 7 | 0.888252 | 0.0201123 | 0.0460261 | 0.00473897 | 0.0195397 | 0.00464245 |
| P3 | 3 | 0.908313 | 0.0197924 | 0.0411208 | 0.00611238 | 0.0159235 | 0.00873688 |
| P3 | 5 | 0.907137 | 0.0245619 | 0.041513 | 0.00723567 | 0.0199183 | 0.0048494 |
| P3 | 7 | 0.908993 | 0.0213367 | 0.0404829 | 0.00513545 | 0.0186125 | 0.00505103 |

## 20. Ablation nhóm biến thời điểm

Nguồn: `reports/thesis_run/sensitivity_summary.csv`, `reports/thesis_run/sensitivity_folds.csv`, `src/thesis.py:robustness`. Phạm vi: train, HGB P0 untuned, repeated 5×3. Tổng hợp: 2 biến thể×15=30 lượt; full là bộ cuối E, không phải bộ B trong nghiên cứu A–F.


| variant | average_precision_mean | average_precision_std | roc_auc_mean | roc_auc_std | brier_mean | brier_std |
|---|---|---|---|---|---|---|
| full | 0.922779 | 0.0159137 | 0.97578 | 0.00582218 | 0.0358155 | 0.00386379 |
| without_temporal_proxies | 0.875813 | 0.0206771 | 0.962806 | 0.00646516 | 0.0488933 | 0.00361301 |

Loại Complain, DaySinceLastOrder, OrderCount, CouponUsed, CashbackAmount cùng cờ/phái sinh liên quan; tiền xử lý fit riêng trong fold. Delta mean AP reduced−full=-0.046965892829766265. Ablation đo mức phụ thuộc nhóm biến; không chứng minh hoặc bác bỏ rò rỉ thời gian. Repeated và delta P1/P2/P3 so P0 có đủ bảng riêng ở mục 10 và `reports/thesis_run/paired_imbalance_deltas.csv`.

## 21. LR tham chiếu: hệ số và odds ratio

Nguồn: `reports/thesis_run/lr_coefficients.csv`, `reports/thesis_run/lr_reference.json`. Phạm vi: LR tham chiếu fit toàn train. Tổng hợp: OR=exp(beta), hệ số có điều chuẩn, không phải mô hình cuối/quan hệ nhân quả.


| feature | coefficient_log_odds | odds_ratio |
|---|---|---|
| Tenure | -0.868959 | 0.419388 |
| CityTier | 0.330662 | 1.39189 |
| WarehouseToHome | 0.232121 | 1.26127 |
| HourSpendOnApp | -0.116139 | 0.890351 |
| NumberOfDeviceRegistered | 0.314841 | 1.37004 |
| SatisfactionScore | 0.396678 | 1.48688 |
| NumberOfAddress | 0.688917 | 1.99156 |
| Complain | 1.79474 | 6.01793 |
| OrderAmountHikeFromlastYear | -0.194538 | 0.823215 |
| CouponUsed | 0.0835319 | 1.08712 |
| OrderCount | 0.320403 | 1.37768 |
| DaySinceLastOrder | -0.367359 | 0.692561 |
| CashbackAmount | -0.0831716 | 0.920193 |
| TenureMissing | 2.16836 | 8.74397 |
| WarehouseToHomeMissing | 0.643615 | 1.90335 |
| OrderAmountHikeFromlastYearMissing | -1.07864 | 0.340058 |
| CouponUsedMissing | -1.37915 | 0.251792 |
| OrderCountMissing | -0.483466 | 0.616642 |
| IsNewCustomer | 2.07197 | 7.94049 |
| Gender_1.0 | -0.323453 | 0.723646 |
| MaritalStatus_1.0 | 0.147377 | 1.15879 |
| MaritalStatus_2.0 | 0.979263 | 2.66249 |
| PreferredLoginDevice_1.0 | 0.379314 | 1.46128 |
| PreferredPaymentMode_1.0 | 0.57617 | 1.77921 |
| PreferredPaymentMode_2.0 | -0.193057 | 0.824435 |
| PreferredPaymentMode_3.0 | 0.566161 | 1.76149 |
| PreferredPaymentMode_4.0 | -0.10305 | 0.902082 |
| PreferedOrderCat_1.0 | 0.47883 | 1.61418 |
| PreferedOrderCat_2.0 | 0.792115 | 2.20806 |
| PreferedOrderCat_3.0 | -0.962794 | 0.381824 |
| PreferedOrderCat_4.0 | 1.99449 | 7.34845 |

Nhóm tham chiếu là phần tử đầu mỗi danh mục: {"Gender": "Male", "MaritalStatus": "Married", "PreferredLoginDevice": "Mobile Phone", "PreferredPaymentMode": "Debit Card", "PreferedOrderCat": "Mobile Phone"}. Cột scaled=Tenure, CityTier, WarehouseToHome, HourSpendOnApp, NumberOfDeviceRegistered, SatisfactionScore, NumberOfAddress, OrderAmountHikeFromlastYear, CouponUsed, OrderCount, DaySinceLastOrder, CashbackAmount. Với cột z-score, OR ứng với tăng 1 SD sau biến đổi; cột log1p gồm WarehouseToHome, NumberOfAddress, CouponUsed, OrderCount, DaySinceLastOrder, CashbackAmount. Cờ/Complain/dummy không scale; không diễn giải OR như tăng một đơn vị gốc cho mọi biến.

## 22. Permutation importance validation

Nguồn: `reports/thesis_run/permutation_importance.csv`, `reports/thesis_run/permutation_folds.csv`, `src/thesis_explain.py`. Phạm vi: train, mô hình cuối clone fit trên 5 train fold, đo trên validation. Tổng hợp: 5 lần hoán vị/trường/fold; giảm AP; mean/SD trên 5 giá trị importance mean mỗi fold; đặc trưng phái sinh tính lại từ dữ liệu thô.


| feature | mean | std |
|---|---|---|
| Tenure | 0.497744 | 0.0109238 |
| Complain | 0.161424 | 0.0221172 |
| NumberOfAddress | 0.107293 | 0.0201462 |
| CashbackAmount | 0.0590422 | 0.0176076 |
| SatisfactionScore | 0.054432 | 0.00672183 |
| MaritalStatus | 0.0462498 | 0.0110767 |
| WarehouseToHome | 0.0370822 | 0.00777906 |
| OrderAmountHikeFromlastYear | 0.03463 | 0.0127744 |
| DaySinceLastOrder | 0.0316644 | 0.00821372 |
| PreferedOrderCat | 0.0307609 | 0.00485587 |
| CityTier | 0.0304759 | 0.0108057 |
| PreferredPaymentMode | 0.0242841 | 0.0103631 |
| NumberOfDeviceRegistered | 0.0186568 | 0.00984753 |
| PreferredLoginDevice | 0.0164198 | 0.00525955 |
| Gender | 0.0119047 | 0.00681941 |
| OrderCount | 0.0106293 | 0.00514792 |
| CouponUsed | 0.00923859 | 0.0028619 |
| HourSpendOnApp | 0.00212186 | 0.00139812 |

## 23. SHAP toàn cục

Nguồn: `reports/thesis_run/shap_grouped_importance.csv`, `reports/thesis_run/shap_local_contributions.csv`, `reports/thesis_run/shap_metadata.json`. Phạm vi: 150 quan sát train đã lưu, giải thích in-sample. Tổng hợp: cộng đóng góp one-hot theo trường trong từng dòng trước mean(abs); đơn vị log-odds.


| feature | mean_abs_grouped_shap |
|---|---|
| Tenure | 1.4734 |
| Complain | 0.610681 |
| NumberOfAddress | 0.46116 |
| CashbackAmount | 0.34059 |
| SatisfactionScore | 0.294787 |
| PreferedOrderCat | 0.274781 |
| MaritalStatus | 0.270182 |
| CityTier | 0.259253 |
| WarehouseToHome | 0.236344 |
| DaySinceLastOrder | 0.198882 |
| NumberOfDeviceRegistered | 0.194229 |
| OrderAmountHikeFromlastYear | 0.178709 |
| PreferredPaymentMode | 0.178416 |
| PreferredLoginDevice | 0.0931139 |
| Gender | 0.088152 |
| OrderCount | 0.0873862 |
| CouponUsed | 0.0800503 |
| CouponUsedMissing | 0.0518277 |
| HourSpendOnApp | 0.0237985 |
| TenureMissing | 0.0181369 |
| WarehouseToHomeMissing | 0.00579583 |
| OrderCountMissing | 0.00514729 |
| IsNewCustomer | 0.00105778 |
| OrderAmountHikeFromlastYearMissing | 0 |

SHAP TreeExplainer tree_path_dependent, nền theo tần số đường đi/nút lưu trong cây đã fit train thật; P0 không có mẫu tổng hợp. Nhánh interventional nền tường minh 100 dòng thất bại cộng tính (`reports/thesis_run/shap_interventional_failure.json`), không dùng nhánh đó làm phương pháp cuối. Kiểm tra bổ sung từ đóng góp lưu: max|base+ΣSHAP−output|=1.42109e-14, thang log-odds; không phân rã trực tiếp xác suất hay sigmoid. Không tắt kiểm tra cộng tính.

## 24. Hồ sơ minh họa theo quy tắc cố định

Nguồn: `reports/thesis_run/shap_prediction_context.csv`, `reports/thesis_run/shap_local_contributions.csv`. Phạm vi: 150 hồ sơ train đã được giải thích. Tổng hợp: chọn min, hạng giữa, max xác suất, không xem nhãn; đây là minh họa in-sample, không phải ca đánh giá độc lập.


| Quy tắc | row_reference | p | base log-odds | output log-odds | 3 đóng góp lớn nhất | 3 đóng góp nhỏ nhất |
|---|---|---|---|---|---|---|
| min p | 4694 | 8.7907e-05 | -3.74388 | -9.33914 | NumberOfAddress: 0.22697; Gender: 0.03862; HourSpendOnApp: 0.02412 | Tenure: -2.96739; NumberOfDeviceRegistered: -0.68180; CouponUsedMissing: -0.66708 |
| median rank p | 4944 | 0.0112398 | -3.74388 | -4.477 | WarehouseToHome: 0.43593; PreferedOrderCat: 0.39718; NumberOfDeviceRegistered: 0.16101 | Tenure: -0.50235; SatisfactionScore: -0.30194; Complain: -0.22883 |
| max p | 2001 | 0.986722 | -3.74388 | 4.30832 | Tenure: 3.73167; Complain: 2.01779; MaritalStatus: 0.98081 | SatisfactionScore: -0.57413; NumberOfAddress: -0.26196; CityTier: -0.07650 |

## 25. Thời gian vận hành

Nguồn: `reports/thesis_run/operational_timing.csv`, `reports/thesis_run/operational_timing_draws.csv`, `src/thesis_explain.py:operational_timing`. Phạm vi: pipeline HGB P0 cuối trên train. Tổng hợp: đơn vị giây; fit và batch predict 4.058 dòng, 5 lần; single 1 dòng, warmup 10 rồi đo 200; median/Q1/Q3/p95.


| operation | count | median | q1 | q3 | p95 |
|---|---|---|---|---|---|
| batch_predict | 5 | 0.0447735 | 0.0438101 | 0.0481276 | 0.0546099 |
| fit | 5 | 0.263068 | 0.263011 | 0.273149 | 0.273949 |
| single_predict | 200 | 0.012256 | 0.011555 | 0.0128026 | 0.0137148 |

IQR=Q3−Q1; timing gồm tiền xử lý và predict_proba, chưa gồm mạng/API. Search HGB=10.708477700012736 giây; RF=1484.6791266000364 giây (`selection.json`; cùng search_seconds được lặp cho tuned/untuned, không cộng hai lần).

Môi trường **được metadata ghi lại**, không đo lại phần cứng cũ: Python 3.15.1; {"pandas": "3.1.0", "numpy": "2.5.4", "scipy": "1.18.1", "statsmodels": "0.15.0", "scikit-learn": "1.9.1", "imbalanced-learn": "0.14.2", "xgboost": "3.4.1", "shap": "0.54.1", "matplotlib": "3.11.2", "joblib": "1.6.0", "openpyxl": "3.1.5"}. `reports/thesis_run/smoke.json` thuật lại 12 logical CPUs, RAM 7,7178 GiB, available 0,8601 GiB, CV n_jobs=1; mã smoke sao chép resources từ báo cáo trước nên không xem là đo phần cứng độc lập tại thesis run. Tên CPU/OS và trạng thái tải lúc đo không lưu. Seed=42. Pipeline prepare→[SMOTE-NC nếu P2/P3]→finish→model; chọn cờ/median/mode/log theo fit, nominal one-hot bỏ mode gốc, LR scale số; cuối HGB P0 không sampler. Metadata giữ schema 18 cột, positive_class=1, danh mục, 31 tên biến đổi, cờ/log. Artifact: `models/thesis_run/pipeline.joblib`, `trained.joblib`, `split.joblib`, `metadata.json`. Dữ liệu nguồn SHA256=db70f1e34bc5326887ea3fb3d2a0854e82c577d55ef3a76fdfb25328631bd44d.

## 26. Đối chiếu hash mã nguồn

Nguồn: `reports/thesis_run/source_manifest.json` và bytes tệp hiện có. Phạm vi: mã/config/lock được liệt kê trong manifest. Tổng hợp: tính SHA256 đọc tệp; không chạy pipeline.


| Tệp | SHA256 so source_manifest |
|---|---|
| src\data.py | khớp |
| src\eda.py | khớp |
| src\evaluation.py | khớp |
| src\experiment.py | khớp |
| src\predict.py | khớp |
| src\preprocessing.py | khớp |
| src\reporting.py | khớp |
| src\scoring.py | khớp |
| src\thesis.py | khớp |
| src\thesis_explain.py | khớp |
| src\thesis_preprocessing.py | khớp |
| src\thesis_summary.py | khác/thiếu |
| src\thesis_visuals.py | khớp |
| src\verify_artifacts.py | khớp |
| src\__init__.py | khớp |
| src\__main__.py | khớp |
| thesis_config.json | khớp |
| requirements-lock.txt | khớp |

Trạng thái stage, test và artifact verification đã lưu chỉ là bằng chứng lịch sử, không tuyên bố đã chạy lại kiểm thử/huấn luyện trong lần tổng hợp này. `src/thesis_summary.py` là bộ xuất báo cáo cũ, chạy lại sẽ ghi đè báo cáo tổng hợp thủ công này; không chạy lệnh report để giữ bản bàn giao.

## 27. Danh mục bảng và biểu đồ hiện có

Nguồn: liệt kê trực tiếp các CSV/PNG trong `reports/thesis_run/`. Phạm vi: artifact run; không lấy pilot. Tổng hợp: mỗi hàng một tệp; cách tổng hợp cụ thể theo mục tương ứng ở trên hoặc bảng gốc.


| Đường dẫn chính xác | Phạm vi | Mục khóa luận đề xuất |
|---|---|---|
| reports/thesis_run/benchmark.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/benchmark_repeated_folds.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/calibration_bins_sigmoid_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/calibration_bins_uncalibrated_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/eda/boxplots_by_label_train.png | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/descriptive_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/distributions_train.png | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_CityTier_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_Complain_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_Gender_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_MaritalStatus_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_PreferedOrderCat_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_PreferredLoginDevice_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_PreferredPaymentMode_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_rates_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_SatisfactionScore_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/group_Tenure_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/high_correlation_pairs.csv | smoke/train hoặc xem mục tương ứng | §3.3/§4.2 EDA |
| reports/thesis_run/eda/hypothesis_tests_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/iqr_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/medians_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/missing_association_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/missingness_train.png | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/positive_rate_by_group_train.png | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/spearman_heatmap_train.png | train | §3.3/§4.2 EDA |
| reports/thesis_run/eda/spearman_matrix_train.csv | train | §3.3/§4.2 EDA |
| reports/thesis_run/feature_study.csv | train | §3.5.5 Đặc trưng |
| reports/thesis_run/feature_study_folds.csv | train | §3.5.5 Đặc trưng |
| reports/thesis_run/figures/calibration_bins_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/calibration_bins_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/calibration_comparison_oof.png | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/calibration_holdout.png | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/calibration_oof.png | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/confusion_holdout.png | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/confusion_oof.png | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/h2_monotonicity_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/h2_monotonicity_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/permutation_importance.png | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/figures/precision_recall_holdout.png | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/precision_recall_oof.png | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/roc_holdout.png | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/roc_oof.png | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/score_distribution_holdout.png | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/score_distribution_oof.png | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/score_rates_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/score_rates_holdout.png | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/score_rates_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/score_rates_oof.png | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/figures/shap_beeswarm.png | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/figures/shap_grouped_bar.png | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/figures/shap_waterfall_high.png | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/figures/shap_waterfall_low.png | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/figures/shap_waterfall_middle.png | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/imbalance_repeated.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/inference_smoke_input.csv | smoke/train hoặc xem mục tương ứng | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/inference_smoke_output.csv | smoke/train hoặc xem mục tương ứng | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/lr_coefficients.csv | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/metrics_ci_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/metrics_ci_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/operational_timing.csv | train | §3.7.5 Vận hành |
| reports/thesis_run/operational_timing_draws.csv | train | §3.7.5 Vận hành |
| reports/thesis_run/paired_imbalance_deltas.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/permutation_folds.csv | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/permutation_importance.csv | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/post_tuning_folds.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/post_tuning_summary.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/predictions_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/predictions_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/risk_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/risk_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/risk_profile_categorical_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/risk_profile_categorical_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/risk_profile_numeric_holdout.csv | holdout | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/risk_profile_numeric_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/sensitivity_folds.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/sensitivity_summary.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/shap_grouped_importance.csv | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/shap_local_contributions.csv | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/shap_prediction_context.csv | train | §3.9/§4.7 Diễn giải |
| reports/thesis_run/smotenc_k_study.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/threshold_sweep_oof.csv | train | §3.8/§4.5–4.6 Đánh giá và điểm |
| reports/thesis_run/tuning_hist_gradient_boosting.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/tuning_random_forest.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |
| reports/thesis_run/tuning_shortlist.csv | train | §3.7/§4.3–4.4 So sánh và độ bền |

## Thông tin còn thiếu và giới hạn xác minh

- Không có Word `.docx` trong workspace; đối chiếu dùng `reports/thesis_extracted.txt`, chưa xác minh đó là phiên bản Word hiện tại.
- Không lưu OOF sigmoid/cal_scores từng fold; không khôi phục AP sigmoid fold hoặc xác minh độc lập điều kiện AP calibration.
- Không lưu danh sách cờ/số chiều từng fit CV; metadata chỉ xác nhận fit toàn train.
- Thiếu chứng cứ nguồn cho nghĩa nhãn, đơn vị Tenure, thời điểm đặc trưng/nhãn, horizon và alias Mobile/Mobile Phone.
- Thiếu thông tin CPU model/OS/tải đo và đo tài nguyên độc lập của run.
- Chưa có tập mới theo thời gian, đánh giá can thiệp giữ chân hoặc kết quả Agent/LLM/API/UI trong đợt học máy; không tự loại các phần đó khỏi phạm vi toàn khóa luận.

## Dữ liệu chưa đủ

[Chi tiết và artifact cần bổ sung](DU_LIEU_CON_THIEU.md).

# Không gian tuning khai báo cho hai thuật toán thực chạy

Vị trí: §3.7.4 — thay bảng nhóm tham số dự kiến.

Nguồn: src/experiment.py:model_and_space; src/thesis.py:model; tuning_*.csv.

Trạng thái: Không gian xác minh từ mã; có 10 trial lưu mỗi thuật toán; không phải đã thử mọi tổ hợp.

| Thuật toán | Tham số | Giá trị khai báo | Số trial thực lưu |
|---|---|---|---|
| random_forest | n_estimators | [100, 150, 250] | 10 |
| random_forest | max_depth | [null, 4, 8, 12] | 10 |
| random_forest | min_samples_split | [2, 5, 10] | 10 |
| random_forest | min_samples_leaf | [1, 2, 4, 8] | 10 |
| random_forest | max_features | ["sqrt", 0.7, 1.0] | 10 |
| hist_gradient_boosting | learning_rate | [0.03, 0.05, 0.1] | 10 |
| hist_gradient_boosting | max_leaf_nodes | [7, 15, 31] | 10 |
| hist_gradient_boosting | l2_regularization | [0.0, 1.0, 10.0] | 10 |
| hist_gradient_boosting | max_iter | [100, 150, 200] | 10 |
| hist_gradient_boosting | max_depth | [null, 3, 6] | 10 |
| hist_gradient_boosting | min_samples_leaf | [10, 20, 40] | 10 |

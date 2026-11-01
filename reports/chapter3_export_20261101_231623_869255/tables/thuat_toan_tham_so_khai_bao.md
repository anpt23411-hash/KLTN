# Thuật toán và tham số được khai báo tường minh

Vị trí: §3.7.1–3.7.2.

Nguồn: Mã constructor hiện có; các tham số không ghi ở đây không được suy ra từ default thư viện.

Trạng thái: Đã xác minh từ mã/config/artifact.

| Thuật toán | Tham số tường minh | Nguồn |
|---|---|---|
| Logistic Regression | max_iter=3000; class_weight theo P; random_state=42 | src/experiment.py:model_and_space |
| Decision Tree | class_weight theo P; random_state=42 | src/thesis.py:model |
| Random Forest | n_estimators=150; class_weight theo P; random_state=42; n_jobs=1 | src/experiment.py:model_and_space |
| HistGradientBoosting | class_weight theo P; random_state=42 | src/experiment.py:model_and_space |
| XGBoost | n_estimators=150; max_depth=3; learning_rate=0.05; balanced theo P; random_state=42; n_jobs=1; eval_metric=logloss; tree_method=hist | src/experiment.py:model_and_space; FoldWeightedXGB |
| Hai dummy | strategy=prior / most_frequent; random_state=42; scenario=baseline | src/thesis.py:benchmark |

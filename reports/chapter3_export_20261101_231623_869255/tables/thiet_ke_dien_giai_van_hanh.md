# Thiết kế kiểm tra độ bền, diễn giải và đo thời gian

Vị trí: §3.7.5; §3.8.8; §3.9.

Nguồn: src/thesis.py:robustness; src/thesis_explain.py; shap_metadata.json.

Trạng thái: Đã xác minh từ mã/config/artifact.

| Thành phần | Thiết kế | Giới hạn |
|---|---|---|
| Ablation | Bỏ Complain, DaySinceLastOrder, OrderCount, CouponUsed, CashbackAmount và dẫn xuất; full/reduced repeated5×3 | Không chứng minh/bác bỏ rò rỉ thời gian |
| Khảo sát sampler | P2/P3 × k=3,5,7 × 5 fold trên train | Không mở lại quyết định cuối |
| Permutation | 5 validation fold; 5 permutation/biến/fold; scoring=AP | SD fold không là CI; không phải importance in-sample |
| SHAP đã dùng | TreeExplainer tree_path_dependent; nền tần số nút train; 150 hồ sơ; log-odds; gộp one-hot trước abs | In-sample explanation; nhánh interventional thất bại; không phân rã sigmoid |
| Timing | Fit 5; batch 5 trên 4058 dòng; single warmup10 + 200 phép đo; giây; median/Q1/Q3/p95 | Gồm preprocessing/predict_proba; không gồm mạng/API; thiếu CPU/OS/tải lúc đo |

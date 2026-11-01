# Phương án xử lý mất cân bằng P0–P3

Vị trí: §3.6.3 — cập nhật Bảng 3.7.

Nguồn: thesis_config.json; src/thesis_preprocessing.py; src/experiment.py.

Trạng thái: Đã xác minh từ mã/config/artifact.

| Phương án | Sampling | Trọng số | Tỷ lệ minority/majority mục tiêu | k | Áp dụng |
|---|---|---|---|---|---|
| P0 | none | Không | Không áp dụng | Không áp dụng | Chỉ train fold; validation/holdout không resample |
| P1 | none | balanced trong fit; XGB dùng sample_weight | Không áp dụng | Không áp dụng | Chỉ train fold; validation/holdout không resample |
| P2 | smotenc | Không | 1.0 | 3 | Chỉ train fold; validation/holdout không resample |
| P3 | smotenc | Không | 0.5 | 3 | Chỉ train fold; validation/holdout không resample |

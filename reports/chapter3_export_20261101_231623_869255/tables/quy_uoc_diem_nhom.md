# Quy ước thang điểm và ba nhóm nguy cơ

Vị trí: §3.8.6 — cập nhật bảng nhóm chưa đánh số.

Nguồn: thesis_config.json:risk_groups; src/scoring.py:score_probability; src/predict.py.

Trạng thái: Đã xác minh từ mã/config/artifact.

| Nhóm | Khoảng xác suất | Điểm | Giới hạn |
|---|---|---|---|
| Thấp | 0 ≤ p < 0,2 | 1–2 | Quy ước trình bày, chưa xác nhận ngưỡng hành động doanh nghiệp; khác ngưỡng F1 |
| Trung bình | 0,2 ≤ p < 0,5 | 3–5 | Quy ước trình bày, chưa xác nhận ngưỡng hành động doanh nghiệp; khác ngưỡng F1 |
| Cao | 0,5 ≤ p ≤ 1 | 6–10 | Quy ước trình bày, chưa xác nhận ngưỡng hành động doanh nghiệp; khác ngưỡng F1 |

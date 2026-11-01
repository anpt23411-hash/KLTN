# Thiết kế nhóm đặc trưng A–F

Vị trí: §3.5.5 — phần thiết kế thay Bảng 3.5; AP thực nghiệm sang Chương 4.

Nguồn: src/thesis.py:feature_study.

Trạng thái: Đã xác minh từ mã/config/artifact.

| Nhóm | Thiết kế | Phép so sánh | Quy tắc |
|---|---|---|---|
| A | 18 biến gốc; không cờ thiếu; không IsNewCustomer | Mốc | Đánh giá LR và HGB, repeated 5×3 |
| B | A + cờ thiếu chọn trong từng fit | B−A | Giữ nếu max(delta AP)≥0,005 và min(delta AP)≥−0,005 |
| C | B + CashbackPerOrder=CashbackAmount/OrderCount | C−B | Cùng quy tắc giữ; mẫu số≤0→thiếu trước impute |
| D | B + CouponRate=CouponUsed/OrderCount | D−B | Cùng quy tắc giữ; mẫu số≤0→thiếu trước impute |
| E | B + IsNewCustomer: Tenure≤1 và không thiếu | E−B | Cùng quy tắc giữ; không cố định số cờ từng fold |
| F | B bỏ HourSpendOnApp, OrderCount, CouponUsed | F−B | Chỉ bỏ nếu cả hai delta≥−0,002; không bỏ nguồn của tỷ số được giữ |

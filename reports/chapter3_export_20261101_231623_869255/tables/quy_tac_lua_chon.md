# Quy tắc benchmark, chọn mô hình, calibration và ngưỡng

Vị trí: §3.7.3–3.8.7.

Nguồn: src/thesis.py:tune; src/evaluation.py; thesis_config.json.

Trạng thái: Đã xác minh từ mã/config/artifact.

| Giai đoạn | Quy tắc trong mã | Giới hạn |
|---|---|---|
| Đại diện từng thuật toán | Mốc=max mean AP 5 fold; duyệt P0→P1→P2→P3; giữ đầu tiên có AP giảm≤max(0,005, SD hiệu ghép cặp 15 fold) và Brier tăng≤0,005 | SD là quy tắc ưu tiên; không kiểm định tương đương |
| Shortlist | Xếp 5 đại diện theo mean AP; lấy 2 thuật toán khác nhau | Không lấy thẳng 2 hàng đầu toàn benchmark |
| Tuning/untuned | 10 trial×3 fold mỗi thuật toán; giữ scenario; đánh giá cả tuned và untuned trên cùng 5 fold | Không bảo đảm tuning cải thiện |
| Ứng viên cuối | Mốc mean AP cao nhất; chỉ đổi sang Brier thấp hơn nếu AP giảm≤0,005 và ECE OOF không tăng | AP mean fold; Brier/ECE vector OOF gộp |
| Sigmoid | Outer 5 fold; inner 3 fold; nhận nếu mean AP sigmoid≥mean AP mốc−0,005 và cả Brier/ECE OOF giảm | Không lưu cal_scores hay vector sigmoid OOF: chưa kiểm chứng độc lập nhánh AP |
| Ngưỡng | Tối đa F1 từ vector OOF; hòa: recall cao hơn, sau đó ngưỡng thấp hơn; dự đoán 1 khi p≥t | Giữ nguyên trên holdout; t số thực nghiệm trình bày Chương 4 |
| Điểm/nhóm | score=min(10,1+floor(10p)); thấp 1–2; trung bình 3–5; cao 6–10 | Ranh giới p=0,2/0,5; nhóm cao khác ngưỡng F1 |
| Đánh giá | AP sklearn average_precision_score; ECE qcut tối đa 10 bin, duplicate edges drop; bootstrap phân tầng 1000, seed42 | AP mean fold khác AP OOF; CI mô hình/ngưỡng cố định, không bao gồm bất định lựa chọn |

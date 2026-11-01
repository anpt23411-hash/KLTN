# Dữ liệu còn thiếu và khả năng tái lập

## Đã lưu và đã xuất

Benchmark/fold, A–F, shortlist, tuning, sensitivity/k, permutation, SHAP, timing, CI bootstrap cũ và hồ sơ rủi ro: xem tables/source_* và artifact_inventory.csv. CI cũ có mô hình/ngưỡng cố định, không gồm bất định lựa chọn; lần xuất này không chạy bootstrap mới.

## Tính lại được từ dự đoán đã lưu — đã thực hiện

AP OOF gộp, ROC, PR, các chỉ số và confusion matrix hai ngưỡng, điểm/nhóm và tỷ lệ Churn theo điểm/nhóm, kiểm tra OOF/holdout không chồng lấn. Reliability trước/sau lấy trực tiếp từ bin đã lưu. Không trộn dự đoán in-sample SHAP vào đánh giá.

## Chưa xuất được / chưa kiểm chứng đầy đủ

| Nội dung | Nguyên nhân | Artifact cần bổ sung / cách khôi phục |
|---|---|---|
| AP mean fold sigmoid và kiểm chứng nhánh AP calibration | Không lưu cal_scores hoặc vector sigmoid OOF; bin không đủ tái tạo thứ hạng | Cần cal_scores outer fold hoặc xác suất sigmoid theo row_reference và fold. Nếu không có bản sao, cần chạy lại huấn luyện calibration CV khi được cho phép; chưa thực hiện |
| PR/ROC/confusion của sigmoid bị loại, và calibration raw/sigmoid trên holdout | Chỉ có dự đoán mô hình cuối; không có xác suất sigmoid trên holdout | Cần dự đoán ứng viên theo từng hồ sơ và nguồn mô hình. Không suy ra từ các chỉ số tổng hợp; không huấn luyện/dự đoán thêm |
| OOF gộp cho mọi cấu hình benchmark/tuning | Chỉ lưu metric từng fold, không lưu xác suất mọi ứng viên | Cần prediction OOF theo cấu hình/fold; nếu mất phải chạy lại CV, chưa thực hiện |
| Danh sách cờ thiếu và số chiều từng fit CV | Metadata chỉ xác nhận mô hình fit toàn train | Cần metadata từng fold; nếu mất cần fit lại CV, chưa thực hiện |
| Beeswarm có màu theo giá trị đặc trưng biến đổi | Đóng góp gộp có sẵn nhưng ma trận đặc trưng biến đổi tương ứng không lưu | Đã xuất phân bố SHAP có dấu không mã hóa màu giá trị biến; cần ma trận biến đổi và tên biến để tái tạo chính xác beeswarm gốc |
| CPU model, OS, tải hệ thống khi đo | Không lưu trong artifact timing | Cần nhật ký môi trường lúc chạy, không dùng phần cứng hiện tại thay thế |
| Xác minh ngữ nghĩa Churn, đơn vị Tenure, horizon, thời điểm biến và alias Mobile/Mobile Phone | Thiếu tài liệu nguồn | Cần data dictionary và bằng chứng thời gian/nguồn dữ liệu; không thể giải quyết bằng huấn luyện lại |
| Kiểm định hoàn toàn mới theo thời gian, can thiệp giữ chân | Holdout từng được quan sát ở pilot | Cần cohort mới hoặc thử nghiệm can thiệp riêng |
| Kết quả AI Agent | Chưa có kiểm thử | Không đưa kết quả Agent vào báo cáo; cần bộ kiểm thử và kết quả thực tế |

Không bịa CI, p-value hoặc số liệu thiếu. SD fold không phải CI hoặc bằng chứng tương đương thống kê. Không phát sinh huấn luyện lại, thay đổi mô hình, ngưỡng, split hoặc quy tắc lựa chọn.

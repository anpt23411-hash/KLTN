# Kiểm tra nguồn dữ liệu

File tại workspace: `data/raw/E Commerce Dataset (1).xlsx`.
SHA256 và số dòng thực tế nằm trong `reports/inspection.json`.
Workbook có hai sheet `Data Dict` và `E Comm`, không có sheet
`E Commerce Dataset(1)  ` theo yêu cầu ban đầu.

Sheet Data Dict mô tả CustomerID là Unique customer ID, Churn là Churn Flag.
Không có định nghĩa mã 0/1 hoặc cửa sổ thời gian của nhãn trong sheet này.
Không thể xác nhận ý nghĩa nhãn chỉ từ tỷ lệ lớp hoặc tên biến.

Nguồn dữ liệu được tham chiếu, đã thử truy cập ngày **2026-10-25**:
[Ecommerce Customer Churn Analysis and Prediction — Ankit Verma](https://www.kaggle.com/datasets/ankitverma2010/ecommerce-customer-churn-analysis-and-prediction).
Lần đối soát ngày 25/10/2026 chưa thu được nội dung mô tả đọc được từ trang nguồn.
Đã thử cả trang chính, `/data` và `/discussion`; không đọc được định nghĩa
mã nhãn từ các trang này. Không coi mô tả từ dự án bên thứ ba là bằng chứng
xác minh cách mã hóa của file nguồn.
URL tham chiếu chưa đủ căn cứ xác nhận mã nhãn. Thực nghiệm sử dụng 0/1 kỹ thuật và 1 là lớp dương, chưa xác minh đầy đủ ý nghĩa nghiệp vụ.
`config.json` ghi `label_semantics_verified=false`.

Data Dict ghi Tenure là "Tenure of customer in organization", không có đơn vị.
Đã kiểm tra mô tả trong workbook và tìm tại nguồn Kaggle nhưng chưa xác minh
được đơn vị. Trong pilot (`config.json`), IsNewCustomer dùng Tenure==0,
thiếu Tenure thì cờ bằng 0 và TenureMissing=1. Tên cờ là quy ước thiết kế,
không chứng minh mọi giá trị 0 thật sự là khách hàng mới trong nghiệp vụ.

Trong thesis run (`thesis_config.json`), IsNewCustomer=1 khi Tenure≤1 và không thiếu;
Tenure thiếu có cờ IsNewCustomer=0. Hai định nghĩa thuộc hai thiết kế thực nghiệm
khác nhau và không được dùng thay thế cho nhau.

Sheet E Comm được sử dụng trong thực nghiệm ngày 2026-10-25; khác biệt tên sheet
không còn là điều kiện chặn nghiên cứu. Kết quả được hiểu là dự báo nhãn kỹ thuật.

Kiểm tra kỹ thuật trên mẫu dữ liệu thật chỉ xác minh thư viện/pipeline/SHAP
hoạt động; không phải đánh giá nghiên cứu hay kết quả holdout.

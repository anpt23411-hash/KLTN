# Danh sách và kiểu xử lý 18 biến đầu vào

Vị trí: §3.2.3 — thay/cập nhật Bảng 3.1.

Nguồn: models/thesis_run/metadata.json; src/thesis_preprocessing.py; đoạn 0628–0665.

Trạng thái: Xác minh kỹ thuật; không xác nhận các mô tả nghiệp vụ trong bản trích.

| Biến | Kiểu đã lưu | Xử lý | Mô tả theo bản trích (chưa xác minh nghiệp vụ) | Trạng thái |
|---|---|---|---|---|
| Tenure | float64 | Số: median; log1p nếu đủ điều kiện trong fit | 196 (4,83%) | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| PreferredLoginDevice | string | Nominal: mode, mã hóa số rồi one-hot | Thiết bị khách hàng ưu tiên sử dụng để đăng nhập. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| CityTier | int64 | Số: median; log1p nếu đủ điều kiện trong fit | Phân hạng thành phố của khách hàng; tiêu chí phân hạng chưa được giải thích. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| WarehouseToHome | float64 | Số: median; log1p nếu đủ điều kiện trong fit | 172 (4,24%) | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| PreferredPaymentMode | string | Nominal: mode, mã hóa số rồi one-hot | Phương thức thanh toán ưu tiên của khách hàng. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| Gender | string | Nominal: mode, mã hóa số rồi one-hot | Giới tính của khách hàng. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| HourSpendOnApp | float64 | Số: median; log1p nếu đủ điều kiện trong fit | 185 (4,56%) | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| NumberOfDeviceRegistered | int64 | Số: median; log1p nếu đủ điều kiện trong fit | Số lượng thiết bị được đăng ký với tài khoản khách hàng. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| PreferedOrderCat | string | Nominal: mode, mã hóa số rồi one-hot | Nhóm sản phẩm khách hàng ưu tiên đặt mua trong tháng gần nhất. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| SatisfactionScore | int64 | Số: median; log1p nếu đủ điều kiện trong fit | Điểm hài lòng của khách hàng đối với dịch vụ; các giá trị quan sát nằm trong khoảng từ 1 đến 5. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| MaritalStatus | string | Nominal: mode, mã hóa số rồi one-hot | Tình trạng hôn nhân của khách hàng. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| NumberOfAddress | int64 | Số: median; log1p nếu đủ điều kiện trong fit | Số lượng địa chỉ được thêm vào tài khoản khách hàng. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| Complain | int64 | Số: median; log1p nếu đủ điều kiện trong fit | Thông tin về việc khách hàng có phát sinh khiếu nại trong tháng gần nhất; biến nhận giá trị 0 hoặc 1. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| OrderAmountHikeFromlastYear | float64 | Số: median; log1p nếu đủ điều kiện trong fit | 209 (5,15%) | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| CouponUsed | float64 | Số: median; log1p nếu đủ điều kiện trong fit | 173 (4,26%) | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| OrderCount | float64 | Số: median; log1p nếu đủ điều kiện trong fit | 187 (4,61%) | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| DaySinceLastOrder | float64 | Số: median; log1p nếu đủ điều kiện trong fit | 229 (5,64%) | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |
| CashbackAmount | float64 | Số: median; log1p nếu đủ điều kiện trong fit | Tiền hoàn trung bình trong tháng gần nhất; tài liệu chưa xác định đơn vị tiền tệ. | Tên/kiểu: xác minh metadata; ý nghĩa/đơn vị/horizon: chưa xác minh nguồn |

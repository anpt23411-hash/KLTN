# Dự báo khách hàng rời bỏ — phần 1

## Tài liệu và kết quả nghiên cứu

| Nội dung | Tài liệu |
|---|---|
| Chương 3: danh mục, sơ đồ và bảng phương pháp | [Danh mục hình và bảng](reports/chapter3_export_20261101_231623_869255/DANH_MUC_HINH_BANG_CHUONG_3.md) |
| Chương 4: báo cáo thực nghiệm | [Báo cáo Markdown](reports/chapter4_export_20261101_230011_200480/BAO_CAO_THUC_NGHIEM.md) |
| Chương 4: báo cáo HTML tự chứa | [Tệp HTML](reports/chapter4_export_20261101_230011_200480/BAO_CAO_THUC_NGHIEM.html) |
| Kết quả tổng hợp và căn cứ thực nghiệm | [Thesis run](reports/thesis_run/RESULTS.md) |
| Đối chiếu phương pháp với bản trích luận văn | [Bảng đối chiếu](THESIS_ALIGNMENT.md) |

Mã nguồn nằm trong `src/`, kiểm thử trong `tests/`, cấu hình thực nghiệm chính
là `thesis_config.json`. Repository không chứa workbook dữ liệu gốc, artifact
mô hình `.joblib` hoặc môi trường ảo; các đường dẫn tương ứng trong manifest
mô tả môi trường thực nghiệm cục bộ. Bảng, hình và dự đoán đã lưu được cung cấp
để đối chiếu kết quả, không thay thế dữ liệu nguồn và mô hình khi tái lập toàn bộ.

## Lần thực nghiệm theo báo cáo khóa luận (thesis run)

Đã đối chiếu mục tiêu/RQ/giả thuyết và phương pháp của bản trích luận văn hiện có. [THESIS_ALIGNMENT.md](THESIS_ALIGNMENT.md) ghi bảng đối chiếu và
các mâu thuẫn cần sửa. Lần thực nghiệm mới dùng **thesis_config.json** và
module `src.thesis`, tách riêng pilot bên dưới; không ghi đè kết quả pilot.
Không xây Agent, LLM, API hay giao diện.

Đầu ra mới: `reports/thesis_run/RESULTS.md`, `THESIS_ALIGNMENT.md`,
`reports/thesis_run/eda/`, `figures/`, các CSV/JSON chi tiết;
`models/thesis_run/pipeline.joblib`, `metadata.json`.
`stage_*.json` ghi các bước thực sự hoàn tất và thời gian thực đo.
Run hoàn tất được bảo vệ khỏi fit/đánh giá holdout lặp lại. Các lần thực nghiệm
độc lập sử dụng report_dir/model_dir riêng, giữ nguyên kết quả đã lưu.
Tái lập kết quả dự đoán trong cùng phiên bản/seed, không kỳ vọng số đo thời gian giống hệt.

Thiết kế chi tiết: LR, Decision Tree, RF, HistGradientBoosting, XGBoost × P0/P1/
SMOTE-NC 1,0/SMOTE-NC 0,5. Benchmark 5 fold chung; 5×3 repeated dùng cho độ bền;
10 trial × 3 fold cho 2 thuật toán; đánh giá lại trên 5 fold trước calibration.
Tham số mô hình chưa tuning vẫn là ứng viên để tránh loại bỏ cấu hình tốt hơn
chỉ vì random search chưa thử được cấu hình đó. AP là average_precision_score;
CI/SD và ECE được phân biệt rõ trong tài liệu đối chiếu.

Cờ thiếu được chọn bằng FDR trong từng fold. Năm nominal được one-hot bỏ mode
của fold gốc, không dùng mode sau sampling; ordinal giữ số. LR scale các biến số,
không scale dummy/cờ/Complain; cây không z-score. Riêng khoảng cách SMOTE-NC
được chuẩn hóa nội bộ rồi đảo lại thang đầu vào, để biến có thang lớn không
chi phối khoảng cách. IsNewCustomer (Tenure<=1 theo Word) và các tỷ số nếu dùng
được tính lại sau sampling. Tất cả bước học chỉ trong train/fold fit.
Quy tắc thiếu Tenure: IsNewCustomer=0, có cờ nội bộ bảo toàn trạng thái thiếu;
cờ thiếu xuất ra mô hình chỉ khi đạt tiêu chí FDR trong fold.

Chọn sigmoid khi Brier và ECE 10 bin phân vị cùng cải thiện và AP giảm không
quá 0,005; nếu có đánh đổi, giữ nguyên phương án AP và công bố bảng/curve.
Fold calibration giữ nguyên tỷ lệ lớp thực; không truyền trọng số cân bằng
hoặc dữ liệu SMOTE vào bước học sigmoid. Khi F1 bằng nhau, ưu tiên Recall cao
hơn, rồi ngưỡng thấp hơn. Nhóm nguy cơ theo Word: low 1–2, medium 3–5, high 6–10.
Đây là quy ước mô tả, không là ngưỡng can thiệp đã được xác thực.

SHAP trên HistGradientBoosting đầy đủ: cấu hình interventional với 100 dòng nền
tường minh không vượt qua kiểm tra cộng tính trong môi trường này. Mã chuyển
sang tree_path_dependent, vẫn bật và kiểm chứng cộng tính độc lập; nền là tần số
đường đi của mô hình fit trên train P0 thật, không phải 100 dòng nền tường minh.
Chi tiết và lỗi gốc được lưu, không dùng check_additivity=False để bỏ qua lỗi.

**Giới hạn:** holdout đã được quan sát trong pilot; kết quả mới không là kiểm
thử độc lập hoàn toàn. Các quyết định mới chỉ dựa trên train, không dựa vào
việc kết quả holdout có tốt hơn pilot hay không. Chưa xác minh ý nghĩa nhãn
0/1, đơn vị Tenure, outcome horizon hoặc thời điểm các biến hành vi. Diễn giải
chỉ là P(label=1); không khẳng định dự báo tương lai hay tác động nhân quả.

Dự đoán lô dữ liệu mới, bằng Python cục bộ:

CSV đầu vào chứa đúng các trường trong metadata, có thể đảo thứ tự; không có
CustomerID/Churn/trường thừa. Pipeline tự chuẩn hóa các alias cố định, median,
mode, one-hot, biến đổi đã học. Category mới được đưa về biểu diễn one-hot bằng
0; tỷ lệ category mới là một nội dung kiểm tra chất lượng đầu vào. Output có scope
new_data_unlabelled, P(label=1), nhãn tại ngưỡng OOF, điểm và nhóm nguy cơ.
Joblib là định dạng tuần tự hóa thực thi được mã, phụ thuộc nguồn artifact tin cậy.
File dữ liệu mới/đầu ra, .env, models và môi trường ảo nằm trong vùng Git ignore.
Đã chạy CLI inference smoke trên năm dòng train thật đã bỏ nhãn/ID; đầu ra
được đánh dấu `in_sample_inference_smoke`, không dùng để đánh giá hiệu năng.
Log kiểm thử mới nằm ở `reports/thesis_run/test_results.txt`.

## Pilot trước khi có báo cáo Word (giữ để truy vết)

Mã nguồn thực hiện kiểm tra dữ liệu, EDA trên train, benchmark và tuning trên train,
hiệu chuẩn sigmoid theo Brier OOF, chọn ngưỡng F1, đánh giá test một lần và xuất pipeline.
Không có số liệu nghiên cứu giả lập. Fixtures trong tests chỉ kiểm tra hợp đồng phần mềm.

## Môi trường và tính tái lập

Metadata ghi nhận Python 3.15.1; môi trường cục bộ nằm trong `venv/`.
`requirements.txt` gốc giữ nguyên; `requirements-lock.txt` khóa toàn bộ phiên bản môi trường đã kiểm tra.

Dữ liệu nguồn được lưu trong `data/raw/`.
Sheet được xác định tường minh trong cấu hình nghiên cứu.

## Thiết kế pilot ngày 2026-10-25

Dùng sheet `E Comm` để phân tích, `Data Dict` để tra biến. Năm thuật toán:
Logistic Regression, Random Forest, Extra Trees, HistGradientBoosting và XGBoost.
Hai DummyClassifier (`most_frequent`, `prior`) là baseline riêng.
Đây là thiết kế thực nghiệm, chưa được chứng minh tốt nhất.

| Phương án | Mất cân bằng |
|---|---|
| P0 | Không lấy mẫu, không trọng số |
| P1 | Trọng số cân bằng trong từng fold fit |
| P2 | RandomOverSampler, không trọng số |
| P3 | SMOTE-NC, không trọng số |

Mọi phương án dùng cùng split, fold và tiền xử lý cơ bản (cùng quy tắc chọn log1p).
P1: w_c = n/(2*n_c), tính lại trong mỗi fit: class_weight="balanced" cho LR,
RF, Extra Trees và HistGradientBoosting; sample_weight cho XGBoost.
P1 sử dụng công thức trọng số đã nêu, không dùng scale_pos_weight. P2/P3 chỉ resample trong fold fit.
Calibration sigmoid được fit trên validation giữ nguyên phân bố lớp; trọng số/
lấy mẫu của estimator không truyền sang bước fit sigmoid.

Nhãn kỹ thuật: 1 là lớp dương, 0 là lớp âm; **chưa xác minh ý nghĩa nghiệp vụ**.
Không gọi các tỷ lệ/kết quả dự báo là rời bỏ/ở lại cho tới khi có bằng chứng.
URL, ngày truy cập, nội dung Data Dict và giới hạn xác minh ở DATA_PROVENANCE.md.

Các giai đoạn thực nghiệm được tổ chức theo thứ tự xác định trong mã.

Quy trình không mở lại lựa chọn mô hình dựa trên kết quả test đã quan sát.
Mã chặn finalize lặp lại khi đã có metrics_test.json. Giữ kết quả mỗi nghiên cứu
trong bản sao workspace riêng nếu đổi đề cương; không xóa dấu vết đánh giá.
Artifact joblib phụ thuộc nguồn lưu trữ tin cậy.

## Quy trình và diễn giải

- Chuẩn hóa khoảng trắng và tên đồng nghĩa Phone/Mobile Phone, CC/Credit Card,
  COD/Cash on Delivery, Mobile/Mobile Phone. Ghi số trùng trước/sau chuẩn hóa,
  bỏ CustomerID khi kiểm tra trùng, giữ bản đầu tiên; phát hiện feature giống nhau
  mà nhãn mâu thuẫn thì dừng để xử lý. Không ép về một số dòng định trước.
- Chia phân tầng 80/20 với seed 42 sau làm sạch xác định. EDA chỉ trên train:
  mô tả, skew, IQR, chi-square (kèm tỷ lệ ô có kỳ vọng <5), Cramér's V,
  Mann–Whitney U, rank-biserial hướng lớp Churn=1 và Spearman cặp số.
  FDR-BH chung cho toàn bộ các phép kiểm định được xuất. Không xóa outlier IQR.
- Numeric: cờ thiếu cố định, median, scale. IsNewCustomer = 1 khi Tenure == 0,
  ngược lại 0; Tenure thiếu thì IsNewCustomer=0 và TenureMissing=1.
  Tạo hai cờ từ dữ liệu gốc trước impute. Đơn vị Tenure chưa xác minh:
  Data Dict chỉ ghi "Tenure of customer in organization"; không tự coi là tháng.
  Chọn log1p cho biến số không âm và skew >1 trên train của từng fold.
  Categorical: mode và ordinal tạm thời. SMOTE-NC chạy sau impute/scale/ordinal,
  trước one-hot, chỉ trong imblearn Pipeline.fit; không lấy mẫu test/validation.
  Các cờ nhị phân cũng được đánh dấu categorical cho SMOTE-NC để không nội suy
  thành cờ phân số. RandomOverSampler dùng cùng vị trí pipeline.
  Category lạ lúc dự đoán được one-hot bỏ qua. CityTier, SatisfactionScore,
  Complain mặc định được xử lý categorical, cấu hình ghi rõ.
- 20 tổ hợp cùng hai Dummy; CV phân tầng 3 fold, AP chính, ROC-AUC và Brier.
  Chọn hai thuật toán khác nhau, lấy phương án tốt nhất mỗi thuật toán;
  RandomizedSearchCV n_iter=10, cv=3. Seed 42 tại nơi hỗ trợ.
- So Brier OOF sigmoid với chưa hiệu chuẩn; sigmoid dùng CV bên trong fold.
  Chọn ngưỡng F1 từ dự đoán StratifiedKFold OOF. Không dùng repeated CV với
  cross_val_predict. OOF chịu thiên lệch lựa chọn siêu tham số/hiệu chuẩn trên
  cùng train, là chẩn đoán lựa chọn; test mới là đánh giá cuối. Không dùng nested
  CV mặc định. Test không tham gia tiền xử lý, tuning, calibration hay ngưỡng.
  Đây là CV bên trong calibration, không phải nested CV để ước lượng kết quả
  của toàn bộ quy trình chọn thuật toán. Nhóm calibration giữ tỷ lệ lớp thực tế.
- Điểm `min(10, 1 + floor(10*p))`: low 1–3 (p<0.3), medium 4–6
  (0.3<=p<0.6), high 7–10 (p>=0.6). Đây là nhóm vận hành cố định,
  chưa được khẳng định là ngưỡng nghiệp vụ tối ưu. Mỗi nhóm được coi là tập
  chọn để tính Precision, Recall và Lift; xuất thêm tập p>=ngưỡng F1.
  Tỷ lệ trong nhóm xuất tên `positive_rate` (nhãn kỹ thuật 1).
  Bootstrap phân tầng 1.000 lần, percentile CI 95%, giữ tỷ lệ lớp và pipeline
  cố định; không bao gồm bất định tái huấn luyện. Nhóm rỗng có rate/CI trống.
- LR tham chiếu cho hệ số log-odds/odds ratio (numeric theo một SD sau biến đổi).
  Permutation importance gọi pipeline với DataFrame thô của train, AP, 5 lần lặp.
  SHAP trên mẫu train tối đa 150: RF/ExtraTrees theo xác suất, XGBoost theo
  log-odds. Nếu winner không được giải thích bởi nhánh cây hiện tại, huấn luyện
  RF tham chiếu và ghi rõ; không coi đó là SHAP của winner hoặc sigmoid.
  Hệ số và importance là liên hệ, không phải quan hệ nhân quả.

## Đầu ra và bảo mật

`reports/inspection.json`, `data_audit.json`, `split_manifest.json`, `eda/`,
`benchmark_train_cv.csv`, `tuning_*.csv`, `selection.json`, `metrics_test.json`,
`calibration_*.png`, `risk_oof.csv`, `risk_test.csv`, `lr_coefficients_train.csv`,
`permutation_train.csv`, `shap_train.csv` và các JSON mô tả thang đo.
Chỉ những giai đoạn đã chạy mới có đầu ra tương ứng.

Agent sau này dùng `predictions_oof.csv`/`predictions_test.csv`: row_reference
là chỉ số dòng nội bộ, scope, observed_label, probability=P(label=1), prediction, score,
risk_group. Không xuất CustomerID. OOF và test nằm trong file riêng;
không xuất dự đoán trong mẫu làm kết quả đánh giá.

`models/churn_pipeline.joblib` nhận DataFrame feature đã chuẩn hóa alias,
đúng tên/thứ tự cột trong `models/metadata.json`. Metadata gồm phiên bản,
schema, SHA256 dữ liệu, ngưỡng, điểm, nhóm rủi ro và cấu hình.
Pipeline huấn luyện, split có dữ liệu và các báo cáo đều bị Git ignore.
Dữ liệu cá nhân, .env, venv và secrets thuộc phạm vi loại trừ của cấu hình Git. Chưa push GitHub.

## Trạng thái chạy thực tế

Xem `reports/inspection.json`, `reports/smoke.json` và `reports/test_results.txt`.
`reports/execution_status.json` ghi các bước đã/chưa chạy cùng lý do.
Sau khi finalize thành công, `reports/RESULTS.md` tổng hợp kết quả thực tế,
benchmark 22 hàng, OOF/test và các hạn chế. Chi tiết từng fold ở
`benchmark_folds_train_cv.csv`, chỉ số dòng/fold ở `cv_manifest.json`.
`python -m src.verify_artifacts` kiểm tra các file đã xuất mà không fit lại:
OOF/test không giao nhau, đủ 22 benchmark/66 hàng fold, 10 trial mỗi thuật toán,
điểm và tổng nhóm đúng. Xuất thêm threshold_metrics_oof/test.json từ các dự đoán
đã lưu; không chọn lại mô hình hoặc ngưỡng trên test.
Smoke hiện tại chỉ dùng phần train của đúng split cố định; các estimator smoke
được bỏ đi, không tái sử dụng cho tuning/hiệu chuẩn/test.

## Xuất báo cáo thực nghiệm Chương 4 từ artifact đã lưu

Mỗi lần chạy tạo thư mục mới `reports/chapter4_export_<thời điểm>/`, gồm
`BAO_CAO_THUC_NGHIEM.md`, HTML tự chứa, `DANH_MUC_BANG_HINH.md`,
`DU_LIEU_CON_THIEU.md`, `tables/`, `figures/` (PNG 300 dpi và SVG) và `manifest.json`.
Có thể chỉ định `--output reports/ten_thu_muc_moi`; thư mục đã tồn tại bị từ chối.
Chức năng chỉ đọc artifact của `reports/thesis_run/`, không gọi fit hoặc dự đoán
mô hình, không thay đổi ngưỡng/split/quy tắc. Kiểm tra số liệu fold, metric holdout,
điểm/nhóm, SHAP, liên kết và SHA256 nguồn trước khi ghi manifest thành công.
Thiếu AP từng fold sigmoid được ghi rõ, không thay bằng AP OOF gộp.

Các bộ báo cáo có verifier độc lập kiểm tra tính toàn vẹn và số liệu.

Verifier đối chiếu SHA256, PNG 300 dpi/SVG, liên kết và tính lại chỉ số từ dự đoán
đã lưu ở cả hai ngưỡng. `--root .` kiểm tra thêm đầu vào hiện tại so với lúc xuất;
kiểm tra không có tùy chọn này chỉ xét tính toàn vẹn nội bộ của bản xuất lịch sử.
Nếu mã nguồn hoặc dữ liệu đã thay đổi sau khi xuất, kiểm tra hash đầu vào sẽ báo rõ.

## Xuất hình và bảng phương pháp Chương 3

Tạo thư mục mới `reports/chapter3_export_<thời điểm>/`, gồm bốn sơ đồ A4
SVG/PNG 300 dpi và mã Mermaid `.mmd`, bảng Markdown/CSV, bản trích Chương 3
dùng đối chiếu, manifest SHA256 và `DANH_MUC_HINH_BANG_CHUONG_3.md`.
Không fit/dự đoán lại. Chỉ có bản trích luận văn trong workspace, chưa xác nhận
Word mới nhất; các thông tin chưa xác minh được ghi rõ. Agent được thể hiện là
kiến trúc đề xuất, phân biệt lõi ML cục bộ đã có với phần tích hợp chưa triển khai.
Các biểu đồ kết quả thực nghiệm thuộc bộ xuất Chương 4.

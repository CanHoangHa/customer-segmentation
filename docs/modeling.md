# Phương pháp phân khúc và cách so sánh

## Đầu vào chung

Mọi phương pháp nhận cùng bảng `customer_rfm.parquet`, một dòng cho mỗi khách. Pipeline kiểm tra
khóa khách, null, trùng lặp, miền giá trị R/F/M và timestamp trước khi chạy. RFM gốc được giữ để
giải thích. Ma trận mô hình dùng `log1p` cho R, F, M rồi chuẩn hóa bằng `StandardScaler` đúng một lần.

## Các phương pháp

- Baseline dùng percentile rank để chia R, F, M thành bốn mức. Giá trị bằng nhau nhận cùng điểm.
  Năm nhóm baseline có thứ tự ưu tiên và phủ hết khách.
- K-Means chạy số cụm từ 3 đến 6 với seed cố định, `n_init=20`.
- Gaussian Mixture chạy 3 đến 6 thành phần với covariance đầy đủ, ba lần khởi tạo và regularization.
- BIRCH chạy 3 đến 6 cụm cuối với nhiều threshold. Báo cáo lưu cả số cụm yêu cầu và số cụm thực tế.

## Cách đo

Mỗi cấu hình làm nóng một lần rồi đo `fit_predict` ít nhất ba lần. Thời gian báo cáo là trung vị.
Silhouette dùng cùng không gian đặc trưng và cùng mẫu cố định tối đa 5.000 khách. Pipeline lưu seed,
cỡ mẫu và hash của chỉ số mẫu. Silhouette chỉ đo mức tách cụm, không phải độ chính xác có nhãn.

Pipeline ưu tiên cấu hình có Silhouette cao nhất trong các cấu hình có ít nhất hai cụm và không có
cụm nhỏ hơn 1% cohort. Nếu không có cấu hình đạt ngưỡng kích thước, pipeline chọn cấu hình còn lại
có Silhouette hợp lệ và ghi rõ tỷ trọng cụm nhỏ nhất.

## Nhãn và hồ sơ phân khúc

Nhãn số do thuật toán tạo không ổn định về ý nghĩa. Pipeline remap nhãn theo tổng M, median M,
median F và median R thành `S1...Sk`. Tên hiển thị ban đầu giữ trung tính, ví dụ `K-Means S1`.
Tên kinh doanh và đề xuất CRM chỉ được chốt sau khi xem profile thực tế.

Mỗi profile ghi số khách, tỷ trọng khách, median R/F/M, tổng và tỷ trọng M, số khách mua lặp và tỷ
lệ mua lặp trong kỳ. Tổng khách và tổng M của từng phương pháp phải khớp bảng RFM nguồn.

## Artifact

- `data/curated/customer_segments.parquet`: nhãn baseline và ba mô hình được chọn.
- `reports/model_comparison.csv`: cấu hình, Silhouette, thời gian, trạng thái và cờ chọn.
- `reports/segment_profiles.csv`: hồ sơ dùng trực tiếp cho dashboard.
- `reports/model_selection.json`: tiêu chí chọn và ánh xạ nhãn ổn định.
- `reports/run_metadata.json`: input hash, commit, môi trường, seed và metadata feature.

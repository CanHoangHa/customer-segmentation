# Kết quả phân khúc khách hàng

## Phạm vi dữ liệu

Pipeline đọc 2.633.521 dòng từ `kz.csv` và giữ 600.784 dòng mua hợp lệ trong năm 2020. Trong 2.032.737 dòng bị tách, 2.030.733 dòng không có `customer_id`, 1.436 dòng nằm ngoài phạm vi thời gian và 568 dòng có giá không dương. Vì vậy, kết quả chỉ đại diện cho phần giao dịch có thể gắn với khách hàng, tương đương 22,81% số dòng nguồn.

Bảng RFM có 234.359 khách hàng, 402.993 đơn hàng và ngày chốt 22/11/2020. Có 74.783 khách mua ít nhất hai đơn trong kỳ, tương đương 31,9096%. Tổng M là 118.372.961,62 đơn vị giá theo nguồn và đã được đối chiếu với tổng giá của giao dịch sạch. Nguồn không xác nhận đồng tiền, vì vậy báo cáo không gọi M là doanh thu kế toán, lợi nhuận hoặc giá trị vòng đời.

## Thiết kế thực nghiệm

Tất cả phương pháp dùng cùng 234.359 khách hàng. K-Means, GMM và BIRCH nhận ma trận `log1p` của R, F, M rồi chuẩn hóa bằng `StandardScaler`. Grid thử số cụm từ 3 đến 6; BIRCH thử thêm threshold 0,3, 0,5 và 0,7. Mỗi cấu hình được làm nóng một lần và đo ba lần. Silhouette dùng cùng mẫu cố định 5.000 khách với seed 42. Một cấu hình đủ điều kiện chọn khi có ít nhất hai cụm và cụm nhỏ nhất chiếm tối thiểu 1% số khách; nếu một phương pháp không có cấu hình đạt ngưỡng, pipeline giữ cấu hình có Silhouette hợp lệ cao nhất và ghi rõ đây là phương án fallback.

## So sánh phương pháp được chọn

| Phương pháp | Cấu hình | Số nhóm | Silhouette | Trung vị thời gian fit | Nhóm nhỏ nhất | Nhận xét |
|---|---:|---:|---:|---:|---:|---|
| Ngưỡng RFM | 5 nhóm | 5 | 0,1969 | Không áp dụng | 12,84% | Dễ đặt tên và giải thích bằng quy tắc |
| K-Means | k = 3 | 3 | 0,3470 | 0,774 giây | 21,47% | Cân bằng giữa độ tách, tốc độ và quy mô nhóm |
| GMM | k = 3 | 3 | 0,1919 | 3,534 giây | 14,52% | Tách rõ khách mua một lần và khách mua lặp |
| BIRCH | k = 3, threshold = 0,7 | 3 | 0,4862 | 2,567 giây | 0,095% | Silhouette cao nhưng phân bố quá lệch; đây là fallback |

BIRCH đạt Silhouette cao nhất nhưng 97,42% khách nằm trong một cụm và cụm nhỏ nhất chỉ có 223 khách. Kết quả này không đạt điều kiện tối thiểu 1%, nên không phù hợp làm phân khúc CRM chính. K-Means k = 3 được đề xuất làm góc nhìn vận hành mặc định vì ba nhóm đều đủ lớn, thời gian fit thấp nhất trong các mô hình học máy được chọn và Silhouette cao hơn baseline cùng GMM. Baseline RFM vẫn hữu ích khi cần một quy tắc minh bạch để chọn đối tượng chiến dịch.

## Hồ sơ K-Means và giả thuyết CRM

### Nhóm S1 có giá trị và tần suất cao

S1 có 50.318 khách, chiếm 21,47% số khách nhưng đóng góp 59,69% tổng M. Trung vị R/F/M lần lượt là 78 ngày, 3 đơn và 909,48 đơn vị giá; 99,95% khách có ít nhất hai đơn.

Giả thuyết cần thử nghiệm là ưu đãi thành viên hoặc gợi ý mua bổ sung có thể duy trì hành vi mua lặp tốt hơn thông điệp đại trà. Thử nghiệm nên chia ngẫu nhiên nhóm nhận và không nhận chiến dịch, theo dõi tỷ lệ có đơn mới, số ngày đến đơn tiếp theo và M tăng thêm. Không kết luận chiến dịch làm tăng doanh thu trước khi có nhóm đối chứng.

### Nhóm S2 mua ít và đã lâu chưa quay lại

S2 có 121.895 khách, chiếm 52,01% số khách và 27,41% tổng M. Trung vị R/F/M là 119 ngày, 1 đơn và 150,44 đơn vị giá; tỷ lệ mua lặp trong kỳ là 12,40%.

Giả thuyết là một chiến dịch tái tương tác chi phí thấp, có giới hạn tần suất gửi, phù hợp hơn ưu đãi sâu trên toàn nhóm. KPI nên gồm tỷ lệ quay lại trong cửa sổ cố định, tỷ lệ hủy đăng ký và chi phí trên một khách quay lại. Cần dừng hoặc thu hẹp chiến dịch nếu chi phí và phản hồi tiêu cực tăng mà không có chênh lệch so với nhóm đối chứng.

### Nhóm S3 mới mua gần đây

S3 có 62.146 khách, chiếm 26,52% số khách và 12,90% tổng M. Trung vị R/F/M là 19 ngày, 1 đơn và 104,14 đơn vị giá; tỷ lệ mua lặp là 15,09%.

Giả thuyết là chuỗi onboarding sau mua, hướng dẫn sử dụng và gợi ý sản phẩm bổ sung đúng thời điểm có thể thúc đẩy đơn thứ hai. Theo dõi tỷ lệ có đơn thứ hai trong 30 hoặc 60 ngày, thời gian đến đơn thứ hai và tỷ lệ từ chối nhận tin. Không trộn nhóm này với chiến dịch tái kích hoạt vì thời gian từ lần mua gần nhất khác rõ rệt.

### Nhóm giá trị cao cần tái tương tác theo baseline

Baseline RFM xác định 40.775 khách, tương đương 17,40%, có trung vị R = 135 ngày và M = 465,25 đơn vị giá. Nhóm đóng góp 22,00% tổng M quan sát. Đây là tệp dễ giải thích cho một thử nghiệm win-back, nhưng tên nhóm chỉ mô tả hành vi trong kỳ và không chứng minh khách đã rời bỏ.

## Giới hạn

- Chỉ 22,81% dòng nguồn có đủ điều kiện để gắn khách và đưa vào RFM; không suy rộng kết quả cho toàn bộ lượt mua của cửa hàng.
- Khoảng quan sát kết thúc ngày 21/11/2020 và ngày chốt là 22/11/2020. Tỷ lệ mua lặp trong kỳ không phải retention của cohort tương lai.
- Đơn vị tiền chưa được nguồn xác nhận. M là tổng giá ghi trong dữ liệu, không phải lợi nhuận hay doanh thu thuần.
- Silhouette được ước lượng trên mẫu cố định 5.000 khách và chỉ đo độ tách trong không gian đặc trưng, không đo hiệu quả chiến dịch.
- Phân khúc là mô tả, không tạo bằng chứng nhân quả. Mọi hành động CRM cần A/B test, giới hạn ngân sách, điều kiện dừng và kiểm tra quyền liên hệ.

## Khả năng tái lập

Chạy `python scripts/run_pipeline.py` để tạo dữ liệu sạch và RFM trong môi trường Python 3.11, PySpark 3.5.8, Java 17. Nếu Python worker của Spark không khởi động được trên Windows, dùng `python scripts/run_portable_rfm.py` để tạo Parquet tương thích và đối chiếu với báo cáo Spark đã commit. Sau đó chạy `python scripts/run_segmentation.py --expected-rows 234359` và `streamlit run app/app.py`.

Các artifact nguồn của bảng này nằm trong `reports/cleaning_summary.json`, `reports/rfm_summary.json`, `reports/model_comparison.csv`, `reports/model_selection.json`, `reports/segment_profiles.csv` và `reports/run_metadata.json`.

## Công cụ AI và kiểm chứng

Nhóm sử dụng Codex để hỗ trợ lập kế hoạch, viết mã, tạo kiểm thử và chuẩn bị tài liệu. Các số liệu trong tài liệu được sinh từ pipeline trên dữ liệu thật, đối chiếu bằng artifact đã commit và kiểm thử tự động. Nhóm vẫn chịu trách nhiệm đọc mã, chạy lại lệnh, kiểm tra kết quả và trình bày đúng giới hạn dữ liệu.

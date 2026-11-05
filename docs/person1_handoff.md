# Bàn giao phần dữ liệu và RFM

## Công việc người 1

1. Khảo sát cấu trúc, dữ liệu thiếu và khoảng ngày trong file gốc bằng PySpark.
2. Chốt quy tắc sửa dòng ngắn, tách dòng không hợp lệ và định nghĩa RFM.
3. Làm sạch bằng PySpark, lưu Parquet và bảng chất lượng trước–sau.
4. Tính RFM, đối chiếu tổng tiền và tính lại ba mẫu từ giao dịch sạch.
5. Cung cấp notebook và script chạy lại; bàn giao schema cho người 2–3.

## Kết quả trên file hiện tại

| Chỉ số | Giá trị |
|---|---:|
| Dòng gốc | 2.633.521 |
| Dòng hợp lệ | 600.784 (22,81%) |
| Dòng bị tách | 2.032.737 |
| Dòng sửa 6 trường được giữ | 37.961 |
| Khách có RFM | 234.359 |
| Đơn hợp lệ | 402.993 |
| Khách có ít nhất 2 đơn | 74.783 (31,91%) |
| Tổng M | 118.372.961,6200 đơn vị giá theo nguồn |

Trong các dòng bị tách: 2.030.733 thiếu mã khách, 1.436 ngoài năm 2020,
568 có giá không dương. Đây là số đếm theo lý do chính, mỗi dòng chỉ tính một lần.

## Bảng cho người 2

Đọc `data/processed/customer_rfm.parquet` để tạo đầu vào cho mô hình.

| Cột | Kiểu | Ý nghĩa |
|---|---|---|
| `customer_id` | string | Mã khách; không chuyển sang số thực |
| `recency_days` | int | Số ngày từ lần mua cuối đến 22/11/2020 |
| `frequency_orders` | long | Số mã đơn riêng biệt |
| `monetary_value` | decimal(30,4) | Tổng giá của các dòng mua hợp lệ |
| `last_purchase_at` | timestamp, UTC | Thời điểm mua gần nhất |

Giữ bảng gốc để diễn giải; tạo bản riêng khi biến đổi đặc trưng cho mô hình.
Bảng `customer_rfm_original_rows.parquet` dùng cùng ngày chốt, chỉ gồm dòng gốc đủ 8 trường.
Người 2 dùng bảng này để kiểm tra ảnh hưởng của việc sửa dòng ngắn; tập khách có thể khác bảng chính.

## Bảng cho người 3

`data/processed/purchases_clean.parquet` có `source_record`, `row_status`, `event_time`,
`order_id`, `product_id`, `category_id`, `category_code`, `brand`, `price`, `customer_id`.
Mã là chuỗi, `price` là decimal(20,4), `event_time` theo UTC.
`source_record` là số thứ tự bản ghi dữ liệu trong CSV, bắt đầu từ 1 sau header.

Đọc chất lượng từ `reports/cleaning_summary.json`, `reports/cleaning_quality.csv`;
ngày chốt và KPI từ `reports/rfm_summary.json`.
Chưa có nhãn phân khúc; phần này do người 2 cung cấp.

## Cách kiểm chứng và giới hạn

- Có 3 bài kiểm tra: sửa dòng ngắn; làm sạch và đọc lại Parquet; công thức RFM trên mẫu tính tay.
- `reports/rfm_hand_check.csv` đối chiếu công thức trên giao dịch sạch của 3 khách. Tổng M khớp tổng giá dữ liệu sạch.
- F đếm đơn, không đếm dòng. Một đơn có nhiều sản phẩm vẫn chỉ tăng F một lần.
- Giữ dòng giống nhau vì thiếu mã dòng mua; M có thể bị ảnh hưởng nếu nguồn thực sự có lỗi trùng.
- Dòng sửa theo mẫu quan sát được đánh dấu, chưa được cửa hàng xác nhận.
- Chỉ 22,81% dòng đủ điều kiện; kết quả mô tả khách có mã, không suy rộng ra toàn cửa hàng.
- M không phải lợi nhuận hay doanh thu thuần. Đồng tiền và quyền chia sẻ lại file còn cần làm rõ.

Chạy lại theo `README.md`. Pipeline giữ nguyên file gốc và thay các đầu ra.

Ví dụ kiểm công thức trong test: khách mua đơn A ngày 20/11 với ba dòng giá 10, 5, 10;
mua đơn B ngày 21/11 giá 20. Với ngày chốt 22/11, R = 1, F = 2, M = 45.
Đây là mẫu kiểm thử nhỏ. Bảng đối chiếu 3 khách dùng giao dịch sạch từ dữ liệu thật.

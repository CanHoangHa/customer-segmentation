# Nguồn dữ liệu

- Tên: **eCommerce purchase history from electronics store**.
- Bên công bố: REES46 / Open CDP; cửa hàng được ẩn danh.
- Bản nhóm dùng: Kaggle Version 2, file `kz.csv`.
- Theo mô tả nguồn: giao dịch mua hàng từ tháng 4 đến tháng 11/2020. Khoảng ngày trong file phải được kiểm tra riêng.
- Trang dataset: <https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-electronics-store>.
- Trang nhà cung cấp: <https://data.rees46.com/>.
- File đối chiếu: <https://data.rees46.com/datasets/electronics-purchases/purchases.csv.gz>.

## File đang dùng

File khoảng **298,65 MB**, đặt tại `data/raw/kz.csv`.
Giữ nguyên file này, không đưa vào Git.

File có 2.633.521 dòng dữ liệu, gồm 2.201.567 dòng đủ 8 trường và 431.954 dòng có 6 trường.
Notebook khảo sát hiển thị mẫu nguyên gốc và khoảng ngày theo năm. Hai bảng thống kê
`reports/row_structure.csv` và `reports/column_quality.csv` lưu số trường theo dòng và số ô thiếu trong nhóm đủ 8 trường.

| Cột nguồn | Ý nghĩa | Kiểu sau xử lý |
|---|---|---|
| `event_time` | Thời điểm mua | Timestamp UTC |
| `order_id` | Mã đơn | Chuỗi |
| `product_id` | Mã sản phẩm | Chuỗi |
| `category_id`, `category_code` | Mã và tên phân loại | Chuỗi |
| `brand` | Thương hiệu | Chuỗi |
| `price` | Giá ghi trên dòng mua | Decimal(20,4) |
| `user_id` | Mã khách ẩn danh | Chuỗi, đổi tên thành `customer_id` |

Khi viết báo cáo, ghi nguồn REES46/Open CDP và liên kết Kaggle. Kiểm tra điều kiện sử dụng trước khi
chia sẻ lại dữ liệu. Khi chưa xác minh đồng tiền, không tự gắn USD hay GBP cho cột giá.

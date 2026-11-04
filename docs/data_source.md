# Nguồn dữ liệu

- Tên: **eCommerce purchase history from electronics store**.
- Bên công bố: REES46 / Open CDP; cửa hàng được ẩn danh.
- Bản nhóm dùng: Kaggle Version 2, file `kz.csv`.
- Theo mô tả nguồn: giao dịch mua hàng từ tháng 4 đến tháng 11/2020. Khoảng ngày trong file phải được kiểm tra riêng.
- Trang dataset: <https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-electronics-store>.
- Trang nhà cung cấp: <https://data.rees46.com/>.
- File đối chiếu: <https://data.rees46.com/datasets/electronics-purchases/purchases.csv.gz>.

## File đang dùng

Khảo sát ngày **04/11/2026**. File khoảng **298,65 MB**, đặt tại `data/raw/kz.csv`.
Giữ nguyên file này, không đưa vào Git.

File có cả dòng đủ 8 cột và dòng chỉ có 6 giá trị. Notebook hiển thị mẫu thật trước khi sửa dòng ngắn
theo điều kiện; dòng không khớp mẫu được tách riêng.
Khoảng ngày thực tế trong file có thể khác mô tả; xem kết quả khảo sát để chọn phạm vi.

Khi viết báo cáo, ghi nguồn REES46/Open CDP và liên kết Kaggle. Kiểm tra điều kiện sử dụng trước khi
chia sẻ lại dữ liệu. Khi chưa xác minh đồng tiền, không tự gắn USD hay GBP cho cột giá.

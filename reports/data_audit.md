# Kết quả khảo sát

Chạy trên toàn bộ `kz.csv`, ngày **04/11/2026**. Xem cách tính trong
[`data_audit.ipynb`](../notebooks/data_audit.ipynb).

## File có gì?

File có **2.633.521 dòng** và tiêu đề 8 cột. Trong đó:

- **2.201.567 dòng** đủ 8 giá trị.
- **431.954 dòng** chỉ có 6 giá trị, được để riêng vì có thể bị lệch cột.

## Quan sát gì trước khi sửa?

Mục 2 của notebook hiển thị dòng thật theo từng vị trí, gồm ví dụ có mã khách và ví dụ thiếu mã khách.
Trên toàn bộ **431.954 dòng ngắn**, vị trí 4 đều trống, vị trí 5 đều có dạng số,
vị trí 6 đều là mã dạng số hoặc trống. Không có dòng 6 trường nằm ngoài mẫu này.

Theo mẫu đó, giữ ba giá trị đầu, đặt hai giá trị cuối về `price` và `user_id`,
để ba cột danh mục/thương hiệu trống. Xem bảng trước–sau trong notebook hoặc hai file
`short_rows_before.csv` và `short_rows_after.csv`.

Đây là sửa vị trí theo mẫu quan sát, chưa phải đối soát với cửa hàng. Dòng đã sửa vẫn cần qua
kiểm tra ngày, giá và mã khách; không tự tạo mã khách cho ô trống.
Chưa xóa các dòng giống nhau vì có thể là mua nhiều sản phẩm giống nhau.

## Còn dùng được bao nhiêu?

Chọn dòng đủ cột hoặc sửa theo mẫu, ngày trong năm 2020, có mã khách/đơn hợp lệ, giá dương
và đơn không mâu thuẫn khách.

| Chỉ số | Kết quả |
|---|---:|
| Dòng đủ điều kiện từ phần ban đầu đủ cột | 562.823 |
| Dòng đủ điều kiện dùng thêm sau sửa | 37.961 |
| Tổng dòng đủ điều kiện khảo sát | 600.784, bằng 22,81% file gốc |
| Khách hàng | 234.359 |
| Đơn riêng biệt | 402.993 |
| Khách có ít nhất 2 đơn | 74.783, bằng 31,91% khách đủ điều kiện |

Khoảng ngày: **05/01–21/11/2020**. Ngày chốt RFM đề xuất: **22/11/2020, UTC**.

## Kết luận

Có đủ khách mua lặp để thử RFM và K-Means. Tuy nhiên, phần dùng được chỉ chiếm khoảng 23% số dòng;
kết quả chỉ mô tả nhóm khách xác định được, không đại diện cho toàn bộ người mua.

Giai đoạn 2 sẽ lưu Parquet, kiểm chứng RFM và so sánh phân khúc khi có/không có dòng sửa theo
`docs/data_rules.md`.
Đây là số liệu khảo sát ban đầu, chưa phải kết quả cuối sau làm sạch.

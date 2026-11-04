# Phạm vi, quy tắc và KPI

## Phạm vi

Phân khúc khách có mã định danh trong dữ liệu mua hàng điện tử năm 2020.
Kết quả chỉ mô tả phần khách đủ dữ liệu, không đại diện cho mọi người mua của cửa hàng.
Khảo sát trên dòng đủ 8 trường và dòng ngắn khớp mẫu cho khoảng ngày 05/01–21/11/2020;
ngày chốt đề xuất là 22/11/2020, UTC. Nếu đổi phạm vi, tính và lưu lại ngày chốt.

## Quy tắc cho giai đoạn 2

| Trường hợp | Cách xử lý dự kiến |
|---|---|
| Dòng đủ 8 trường | Xét tiếp ngày, giá, mã khách và mã đơn |
| Dòng 6 trường khớp mẫu quan sát | Sửa vị trí giá và mã khách, rồi kiểm tra như dòng bình thường |
| Dòng sai cấu trúc không khớp mẫu | Tách riêng, không đoán cách sửa |
| Thiếu mã khách hoặc mã đơn | Tách khỏi RFM, không tự tạo mã thay thế |
| Ngày không đọc được hoặc ngoài năm 2020 | Tách và ghi lý do |
| Giá thiếu, sai kiểu hoặc không dương | Tách khỏi RFM, không điền bằng 0 |
| Một đơn gắn nhiều khách | Tách toàn bộ đơn mâu thuẫn để kiểm tra |
| Thiếu thương hiệu hoặc ngành hàng | Vẫn giữ nếu đủ trường tính RFM |
| Dòng giống nhau | Chưa xóa: có thể là mua nhiều đơn vị cùng sản phẩm |
| Giá cao bất thường | Kiểm tra, chưa tự loại khách chi tiêu lớn |

## Mẫu quan sát trước khi sửa

Notebook hiển thị ví dụ thật, đánh số vị trí từ 1 đến 6, rồi kiểm tra toàn bộ dòng ngắn.
Mẫu chấp nhận: vị trí 4 trống, vị trí 5 là số thập phân, vị trí 6 là mã dạng số hoặc trống.

Giữ ba giá trị đầu; đặt hai giá trị cuối về `price` và `user_id`;
để `category_id`, `category_code`, `brand` trống. Không tự điền mã khách còn thiếu.
Dòng sửa được đánh dấu `repaired_6_fields` khi khảo sát để đếm riêng ảnh hưởng của quy tắc.

Xem ví dụ trước–sau ở mục 2 của notebook và `reports/short_rows_before.csv`,
`reports/short_rows_after.csv`. Đây là sửa theo mẫu quan sát, chưa phải đối soát giao dịch với cửa hàng.
Khi làm mô hình, cần so sánh kết quả có/không có các dòng đã sửa.

## KPI

- **Ngày chốt:** ngày sau ngày mua hợp lệ cuối cùng của phạm vi được chọn, theo UTC. Lưu cố định cùng kết quả.
- **R:** số ngày từ ngày mua gần nhất của khách đến ngày chốt.
- **F:** số mã đơn riêng biệt của khách; một đơn nhiều dòng chỉ tính một lần.
- **M:** tổng giá trị `price` trên các dòng mua hợp lệ, chỉ sau khi xác minh cách ghi giá của nguồn.
- **Tỷ lệ mua lại trong kỳ:** số khách có F từ 2 trở lên / tổng khách được tính RFM.
- **Tỷ trọng giá trị mua:** tổng M của nhóm / tổng M của toàn bộ khách được phân khúc.
- **Silhouette:** mức phân tách cụm trên cùng bộ đặc trưng chuẩn hóa; tính ở giai đoạn mô hình.

Không tự thêm số lượng để nhân giá. Khi chưa xác minh đồng tiền, dùng nhãn “đơn vị giá theo nguồn”.
Không gọi M là lợi nhuận, doanh thu thuần hay giá trị vòng đời khách hàng.
Nếu vẫn giữ các dòng giống nhau, phải nêu khả năng M bị ảnh hưởng; không mặc định đó là lỗi trùng.

## Bàn giao

Người 1 xác minh ý nghĩa giá và giấy phép, rồi triển khai làm sạch, Parquet và RFM.
Người 2 nhận cùng phạm vi khách và cùng ngày chốt để so sánh baseline với K-Means.
Người 3 hiển thị độ bao phủ và ngày chốt bên cạnh các kết quả phân khúc.

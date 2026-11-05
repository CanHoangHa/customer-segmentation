# Phạm vi, quy tắc và KPI

## Phạm vi

Phân khúc khách có mã định danh trong dữ liệu mua hàng điện tử năm 2020.
Kết quả chỉ mô tả phần khách đủ dữ liệu, không đại diện cho mọi người mua của cửa hàng.
Giao dịch hợp lệ nằm trong khoảng 05/01–21/11/2020. Ngày chốt là 22/11/2020 theo UTC.
Nếu đổi phạm vi, tính và lưu lại ngày chốt.

## Quy tắc làm sạch

| Trường hợp | Cách xử lý |
|---|---|
| Dòng đủ 8 trường | Xét tiếp ngày, giá, mã khách và mã đơn |
| Dòng 6 trường khớp mẫu quan sát | Sửa vị trí giá và mã khách, rồi kiểm tra như dòng bình thường |
| Dòng sai cấu trúc không khớp mẫu | Tách riêng, không đoán cách sửa |
| Thiếu mã khách hoặc mã đơn | Tách khỏi RFM, không tự tạo mã thay thế |
| Ngày không đọc được hoặc ngoài năm 2020 | Tách và ghi lý do |
| Giá thiếu, sai kiểu hoặc không dương | Tách khỏi RFM, không điền bằng 0 |
| Một đơn gắn nhiều khách | Tách toàn bộ đơn mâu thuẫn để kiểm tra |
| Thiếu thương hiệu hoặc ngành hàng | Vẫn giữ nếu đủ trường tính RFM |
| Dòng giống nhau | Giữ: có thể là mua nhiều đơn vị cùng sản phẩm |
| Giá cao bất thường | Kiểm tra, chưa tự loại khách chi tiêu lớn |

## Mẫu quan sát trước khi sửa

Notebook khảo sát hiển thị mẫu gốc theo thứ tự các trường.
Bước làm sạch chỉ sửa dòng có vị trí 4 trống, vị trí 5 là số và vị trí 6 là mã dạng số hoặc trống.

Giữ ba giá trị đầu; đặt hai giá trị cuối về `price` và `user_id`;
để `category_id`, `category_code`, `brand` trống. Không tự điền mã khách còn thiếu.
Dòng sửa được đánh dấu `repaired_6_fields` để đếm riêng ảnh hưởng của quy tắc.

Xem mẫu gốc trong `notebooks/data_audit.ipynb` và mẫu đã sửa trong `notebooks/cleaning_rfm.ipynb`.
Quy tắc sửa dựa trên mẫu quan sát trong file.
Khi làm mô hình, cần so sánh kết quả có/không có các dòng đã sửa.

## KPI

- **Ngày chốt:** ngày sau ngày mua hợp lệ cuối cùng của phạm vi được chọn, theo UTC. Lưu cố định cùng kết quả.
- **R:** số ngày từ ngày mua gần nhất của khách đến ngày chốt.
- **F:** số mã đơn riêng biệt của khách; một đơn nhiều dòng chỉ tính một lần.
- **M:** tổng `price` trên các dòng mua hợp lệ, theo cách ghi mỗi dòng sản phẩm mua của nguồn. Không nhân thêm số lượng.
- **Tỷ lệ mua lại trong kỳ:** số khách có F từ 2 trở lên / tổng khách được tính RFM.
- **Tỷ trọng giá trị mua:** tổng M của nhóm / tổng M của toàn bộ khách được phân khúc.
- **Silhouette:** mức phân tách cụm trên cùng bộ đặc trưng chuẩn hóa; tính ở giai đoạn mô hình.

Không tự thêm số lượng để nhân giá. Khi chưa xác minh đồng tiền, dùng nhãn “đơn vị giá theo nguồn”.
Không gọi M là lợi nhuận, doanh thu thuần hay giá trị vòng đời khách hàng.
Nếu vẫn giữ các dòng giống nhau, phải nêu khả năng M bị ảnh hưởng; không mặc định đó là lỗi trùng.

## Bàn giao

Người 1 bàn giao giao dịch sạch, bảng RFM và thống kê chất lượng; xem `docs/person1_handoff.md`.
Đồng tiền và điều kiện chia sẻ lại dữ liệu chưa được xác minh đầy đủ; không gắn tên đồng tiền
hoặc đưa file dữ liệu lên GitHub khi chưa làm rõ.
Người 2 nhận cùng phạm vi khách và cùng ngày chốt để so sánh baseline với K-Means.
Người 3 hiển thị độ bao phủ và ngày chốt bên cạnh các kết quả phân khúc.

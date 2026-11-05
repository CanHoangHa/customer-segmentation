# Dashboard phân khúc khách hàng

## Cách chạy

Sau khi chạy `scripts/run_segmentation.py`, mở dashboard bằng:

```powershell
streamlit run app/app.py
```

Dashboard chỉ đọc Parquet, CSV và JSON đã được pipeline tạo. Bộ lọc không huấn luyện lại mô hình,
không đổi RFM và không đổi ngày chốt.

## Nội dung

- Phạm vi dữ liệu hiển thị số khách, tỷ lệ mua lặp trong kỳ, tổng M và độ bao phủ dòng hợp lệ.
- Hồ sơ phân khúc hiển thị quy mô, tỷ trọng M, median R/F/M và scatter trên mẫu cố định.
- So sánh phương pháp hiển thị Silhouette, thời gian chạy, số cụm và quy mô cụm nhỏ nhất.
- Giả thuyết CRM nối quan sát định lượng với thử nghiệm, KPI theo dõi và rủi ro.

Silhouette không phải độ chính xác và không chứng minh hiệu quả kinh doanh. Dashboard cảnh báo khi
mô hình được chọn theo fallback vì không có cấu hình đạt ngưỡng quy mô cụm tối thiểu 1%.

## Quy tắc riêng tư

Dashboard không hiển thị `customer_id` trong biểu đồ và không cung cấp nút tải raw data mặc định.
Đơn vị M là đơn vị giá theo nguồn do đồng tiền chưa được xác minh.

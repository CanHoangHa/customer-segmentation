# customer-segmentation

Phân khúc khách hàng cửa hàng điện tử bằng RFM và K-Means. Dữ liệu giao dịch năm 2020 do REES46 công bố.

## Chuẩn bị

Đặt bản Kaggle Version 2 tại `data/raw/kz.csv`. Cấu hình đã kiểm tra gồm Python 3.11, PySpark 3.5.8 và Java 17.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
```

## Khảo sát và xử lý

1. Chạy `jupyter lab`, mở `notebooks/data_audit.ipynb` và chọn **Run All** để xem vài bản ghi gốc, đếm số trường trên toàn file, rồi xem mẫu dòng ngắn, dữ liệu thiếu và khoảng ngày.
2. Chạy `python scripts/run_pipeline.py` hoặc mở `notebooks/cleaning_rfm.ipynb` để căn cột, làm sạch và tính RFM. Hai cách tạo cùng đầu ra.
3. Chạy `python -m pytest -q` để kiểm tra pipeline dữ liệu, hợp đồng RFM và baseline phân khúc.

Nếu môi trường Windows không cho PySpark khởi động Python worker, có thể chạy
`python scripts/run_portable_rfm.py`. Đây là runner tương thích để tạo Parquet phục vụ mô hình,
không thay thế pipeline PySpark chính. Runner đọc streaming hai lượt và mặc định chỉ hoàn thành khi
số dòng, số khách, số đơn, tổng M và ngày chốt khớp các báo cáo Spark đã commit.

## Chuẩn bị đặc trưng và baseline phân khúc

Sau khi có `data/processed/customer_rfm.parquet`, chạy:

```powershell
python scripts/run_segmentation.py --expected-rows 234359
```

Lệnh này kiểm tra hợp đồng RFM, sắp xếp khách theo `customer_id`, tạo ma trận đặc trưng
`log1p + StandardScaler`, chạy baseline RFM, K-Means, GMM và BIRCH rồi ghi các phương pháp được
chọn vào `data/curated/customer_segments.parquet`. Bảng so sánh, profile, lựa chọn mô hình và
metadata lần chạy nằm trong `reports/`.

Để chỉ kiểm tra hợp đồng và baseline, thêm `--baseline-only`. Tham số benchmark có thể xem bằng
`python scripts/run_segmentation.py --help`.

Pipeline dừng với lỗi rõ ràng nếu thiếu cột, null, trùng khách, R/F không nguyên hợp lệ,
M không dương hoặc timestamp không đọc được. Không sửa trực tiếp bảng RFM bàn giao.

Hai notebook dùng chung bộ đọc CSV theo từng bản ghi trong Spark để giữ đúng số trường. Khảo sát tạo báo cáo quan sát. Pipeline giữ nguyên file nguồn, thay các đầu ra mỗi lần chạy và ghi giao dịch bị tách kèm lý do.
PySpark xử lý dữ liệu và tính RFM. PyArrow ghi Parquet trên Windows khi máy thiếu Hadoop native.

- `PLAN.md` ghi phân công và tiến độ nhóm.
- `docs/data_source.md` mô tả nguồn và các trường.
- `docs/data_rules.md` ghi quy tắc làm sạch và công thức KPI.
- `docs/person1_handoff.md` ghi kết quả, tên bảng và schema bàn giao.

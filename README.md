# customer-segmentation

Phân khúc khách hàng cửa hàng điện tử bằng RFM và K-Means. Dữ liệu: REES46, bản Kaggle năm 2020.

## Khảo sát dữ liệu

Đặt `kz.csv` vào `data/raw/`. File gốc không được đưa vào Git.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-audit.txt
jupyter lab
```

Nếu đã có môi trường `.venv`, chỉ cần kích hoạt và cài các thư viện còn thiếu.
Mở `notebooks/data_audit.ipynb`, chọn **Run All**. Notebook cập nhật các báo cáo trong `reports/`;
không sửa file gốc và chưa xuất dữ liệu sạch.

- `PLAN.md`: phân công và tiến độ nhóm.
- `docs/data_source.md`: nguồn và kiểm tra file tải.
- `docs/data_rules.md`: phạm vi, quy tắc và KPI.
- `reports/data_audit.md`: kết luận khảo sát ngắn.
- `docs/pipeline.md`: cách chạy phần làm sạch và đọc các đầu ra.

## Làm sạch dữ liệu

```powershell
python -m pip install -r requirements.txt
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
python scripts/prepare_data.py
```

Pipeline lưu Parquet trong `data/processed/`, các dòng bị tách trong `data/quarantine/`
và thống kê trước–sau trong `reports/`.

Chú ý: file nguồn có cả dòng 8 trường và dòng 6 trường. Mục 2 của notebook hiển thị mẫu thật,
kiểm tra điều kiện và ví dụ trước–sau khi sửa vị trí cột. Không dùng riêng kết quả pandas đọc mặc định
để kết luận tỷ lệ thiếu giá hoặc mã khách.

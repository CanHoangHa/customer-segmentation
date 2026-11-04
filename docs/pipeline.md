# Chạy phần dữ liệu

## Chuẩn bị

Đặt file gốc tại `data/raw/kz.csv`. Cài thư viện và chọn Java 17:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:JAVA_HOME = "C:\Program Files\Java\jdk-17"
```

Đường dẫn Java có thể thay đổi theo máy. Cấu hình đã kiểm tra: Python 3.11, PySpark 3.5.8, Java 17.

## Làm sạch

Chạy toàn bộ phần người 1 bằng `python scripts/run_pipeline.py`, hoặc chạy từng bước dưới đây.
Notebook `notebooks/cleaning_rfm.ipynb` trình bày cùng các bước và hiển thị kết quả.

```powershell
python scripts/prepare_data.py
```

Luồng chạy:

1. Đọc CSV bằng bộ đọc chuẩn để nhận diện chính xác số trường.
2. Sửa dòng 6 trường khớp mẫu đã quan sát, giữ số thứ tự dòng và dấu đánh dấu đã sửa.
3. Dùng PySpark để kiểm tra ngày, giá, mã khách, mã đơn và quan hệ khách–đơn.
4. Lưu giao dịch hợp lệ và các dòng bị tách, kèm lý do.

Mỗi dòng bị tách có một lý do chính theo thứ tự kiểm tra, nên tổng số dòng trước–sau đối chiếu được.
Lỗi trên cùng dòng vẫn có thể nhiều hơn một; lý do chính không phải toàn bộ lỗi của dòng đó.

| Đầu ra | Nội dung |
|---|---|
| `data/processed/purchases_clean.parquet` | Giao dịch hợp lệ, có `customer_id` và `row_status` |
| `data/quarantine/purchases_rejected.parquet` | Dòng bị tách và `rejection_reason` |
| `reports/cleaning_summary.json` | Số dòng được giữ/tách theo lý do |
| `reports/cleaning_quality.csv` | Dữ liệu thiếu trước và sau kiểm tra |

Bảng trước kiểm tra đã được căn chỉnh cấu trúc; file gốc được giữ nguyên.
Các dòng giống nhau được giữ vì nguồn không có mã riêng cho từng dòng mua.

PySpark thực hiện kiểm tra và tổng hợp. PyArrow ghi Parquet theo từng lô để hạn chế RAM
và chạy trên Windows mà không cần cài thêm thư viện Hadoop native.
Chạy lại sẽ thay các file đầu ra của pipeline, không nối thêm dữ liệu.

## Tính RFM

```powershell
python scripts/build_rfm.py
python scripts/check_rfm.py
```

RFM có một dòng cho mỗi khách: R là số ngày từ lần mua cuối đến ngày chốt,
F là số đơn riêng biệt, M là tổng giá trên các dòng mua hợp lệ.
Ngày chốt được lưu trong `reports/rfm_summary.json`.

- `data/processed/customer_rfm.parquet`: bảng RFM dùng cho mô hình.
- `data/processed/customer_rfm_original_rows.parquet`: bảng so sánh chỉ dùng dòng gốc đủ 8 trường, cùng ngày chốt.
- `reports/rfm_hand_check.csv`: đối chiếu 3 khách với phép tính trực tiếp từ CSV gốc.

Tổng M được đối chiếu với tổng giá của dữ liệu sạch. M dùng đơn vị giá theo nguồn.

## Kiểm tra

```powershell
python -m pytest -q
```

Giữ số lượng kiểm thử nhỏ, tập trung vào sửa cấu trúc, quy tắc loại dòng và công thức RFM trên mẫu tính tay.

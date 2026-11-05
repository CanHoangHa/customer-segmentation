# Kiến trúc hệ thống

```mermaid
flowchart LR
    A[kz.csv] --> B[Khảo sát cấu trúc]
    A --> C[Làm sạch và quarantine]
    C --> D[purchases_clean.parquet]
    D --> E[Tính RFM]
    E --> F[customer_rfm.parquet]
    F --> G[Kiểm tra hợp đồng]
    G --> H[Baseline RFM]
    G --> I[log1p và StandardScaler]
    I --> J[K-Means]
    I --> K[GMM]
    I --> L[BIRCH]
    H --> M[Đánh giá và profile]
    J --> M
    K --> M
    L --> M
    M --> N[customer_segments.parquet]
    M --> O[CSV và JSON trong reports]
    N --> P[Dashboard Streamlit]
    O --> P
    O --> Q[Báo cáo và slide]
```

## Ranh giới trách nhiệm

- `src/prepare_data.py` và `src/rfm.py` xử lý dữ liệu bằng PySpark. `src/portable_rfm.py` chỉ là runner tương thích khi Python worker của Spark không chạy được trên Windows.
- `src/segmentation/features.py` kiểm tra hợp đồng và chuẩn bị đặc trưng. RFM gốc không bị ghi đè.
- `src/segmentation/baseline.py`, `models.py`, `evaluation.py` và `pipeline.py` tạo nhãn, benchmark, chọn cấu hình và ghi artifact.
- `app/data.py` chỉ đọc và kiểm tra artifact; `app/charts.py` tạo biểu đồ; `app/app.py` điều phối giao diện. Dashboard không tính lại nhãn hoặc KPI bằng một công thức khác.

## Luồng tái lập

```text
python scripts/run_pipeline.py
python scripts/run_segmentation.py --expected-rows 234359
python -m pytest -q
streamlit run app/app.py
```

File dữ liệu gốc và các Parquet lớn được loại khỏi Git. Mã nguồn, kiểm thử, metadata và các bảng kết quả tổng hợp được version-control để review được quyết định mô hình.

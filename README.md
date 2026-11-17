# Phân khúc khách hàng theo hành vi mua sắm

Bài tập lớn CO4033, đề tài 04. Nhóm so sánh baseline ngưỡng RFM với K-Means, GMM và BIRCH để hỗ trợ bộ phận marketing và CRM chọn nhóm khách cần chăm sóc.

- Có thể phân biệt khách mới mua và khách đã lâu chưa quay lại dựa trên lịch sử mua hàng như thế nào?
- Phương pháp nào cho nhóm đủ lớn, dễ giải thích và có độ tách tốt?

## Dữ liệu

Tải `kz.csv` bản Version 2 từ [Kaggle](https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-electronics-store) và đặt tại `data/raw/kz.csv`. Kaggle ghi quyền dữ liệu là *Data files © Original Authors*. Repo cung cấp mã nguồn và dữ liệu kiểm thử giả lập.

Dữ liệu có **2.633.521 dòng**. Pipeline giữ **600.784 dòng (22,81%)** sau khi căn lại dòng ngắn hợp lệ và lọc giao dịch thiếu mã khách, sai phạm vi ngày hoặc có giá không hợp lệ. Xem [schema và nguồn dữ liệu](docs/data_source.md), [quy tắc xử lý](docs/data_rules.md) và [bảng chất lượng trước–sau](reports/cleaning_quality.csv).

## Chạy lại

Chạy từ thư mục gốc của repo. Môi trường đã kiểm tra dùng **Python 3.11, Java 17 và PySpark 3.5.8**. Đặt `JAVA_HOME` trỏ tới thư mục JDK 17 trên máy.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/run_all.py
python -m streamlit run app/app.py
```

`run_all.py` chạy làm sạch, tạo RFM rồi phân khúc. Mở URL Streamlit in trong terminal để xem kết quả và lọc theo phương pháp hoặc phân khúc.

Nếu PySpark trên Windows gặp lỗi Python worker, chạy `python scripts/run_portable_rfm.py`, sau đó chạy `python scripts/run_segmentation.py --expected-rows 234359` trước khi mở dashboard.

## Kiểm thử và kết quả

- **Kiểm thử** — chạy `python -m pytest -q`. [Ba ca kiểm thử dữ liệu giả lập](tests/test_prepare_data.py) kiểm tra căn dòng ngắn, làm sạch và đọc lại Parquet, rồi đối chiếu RFM bằng tay.
- **KPI** — R là số ngày từ lần mua cuối đến ngày chốt, F là số đơn riêng biệt và M là tổng giá trị mua. Tỷ lệ mua lại trong kỳ là tỷ lệ khách có từ hai đơn, đạt **31,91%** trên **234.359 khách**. Silhouette đo độ tách cụm trên cùng mẫu **5.000 khách**.
- **So sánh** — [Bảng benchmark](reports/model_comparison.csv) ghi Silhouette, quy mô cụm và trung vị ba lần đo. Nhóm chọn K-Means ba cụm (Silhouette **0,3470**). BIRCH có điểm cao hơn nhưng cụm nhỏ nhất chỉ chiếm **0,095%** số khách.
- **Minh chứng** — [Sơ đồ pipeline](docs/architecture.md), [notebook](notebooks/), [mẫu đối chiếu RFM](reports/rfm_hand_check.csv), [cấu hình benchmark](reports/run_metadata.json) và [hướng dẫn demo](docs/demo.md).

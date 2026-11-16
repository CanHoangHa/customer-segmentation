# Kế hoạch bài tập lớn: phân khúc khách hàng theo hành vi mua sắm

## 1. Phạm vi đã thống nhất

- Đề tài 04: phân khúc khách hàng theo hành vi mua sắm.
- Nhóm gồm 3 người, ưu tiên hoàn thành một pipeline dễ chạy lại và giải thích được.
- Dataset: **eCommerce Purchase History from Electronics Store**, do REES46/Open CDP công bố; dùng giao dịch thực tế năm 2020 đã ẩn danh.
- So sánh **baseline theo ngưỡng RFM, K-Means, GMM và BIRCH**. Người 2 triển khai và đánh giá cả bốn phương pháp.
- Người dùng dashboard: nhân viên CRM hoặc quản lý marketing của cửa hàng điện tử.
- Nhánh tích hợp là `dev`. Phần dữ liệu của người 1 nằm trên `feat/data-rfm`.

Tên đề tài đề xuất: **Phân khúc khách hàng cửa hàng điện tử từ dữ liệu giao dịch thực tế bằng RFM và các thuật toán phân cụm**.

### Câu hỏi kinh doanh

1. Khách hàng khác nhau như thế nào về thời gian mua gần nhất, số lần mua và giá trị mua?
2. Nhóm khách nào đóng góp giá trị mua cao nhưng đã lâu chưa quay lại, cần ưu tiên chăm sóc?
3. Ngưỡng RFM, K-Means, GMM và BIRCH khác nhau thế nào về mức phân tách, quy mô nhóm, thời gian chạy và khả năng giải thích?

Tên nhóm và nhận xét kinh doanh chỉ được đặt sau khi xem kết quả. Không đặt trước kết luận rằng K-Means tốt hơn hoặc một nhóm chắc chắn đã rời bỏ cửa hàng.

## 2. Nguồn dữ liệu và việc cần xác minh

- Nguồn nhà cung cấp: <https://data.rees46.com/>.
- Dataset: <https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-electronics-store>.
- Mục purchases của nhà cung cấp mô tả khoảng **2,5 triệu dòng mua hàng**, giai đoạn **04–11/2020**, file `purchases.csv.gz` khoảng 50 MB. Đây là thông tin công bố, chưa phải số liệu nhóm tự đo; không gọi 2,5 triệu dòng là 2,5 triệu đơn hàng.
- Người 1 phải ghi tên file, phiên bản, URL tải, ngày tải, số dòng thực đọc, thời gian thực tế và điều kiện sử dụng/ghi nguồn. Không coi dữ liệu công khai là tự động có giấy phép phân phối lại.
- Nếu bản Kaggle và bản trực tiếp có khác biệt về thời gian hoặc số dòng, ghi rõ phiên bản được chọn và dùng nhất quán cho tất cả phương pháp. Không ghép các bản khác nhau để tăng số dòng.
- Phạm vi là các bản ghi mua hàng năm 2020 có thời gian hợp lệ, nằm trong khoảng quan sát đã xác minh. Không ép ngày đầu/cuối theo mô tả nếu chưa kiểm tra dữ liệu.

### Schema dự kiến để khảo sát

| Trường nguồn | Vai trò dự kiến | Kiểm tra bắt buộc |
|---|---|---|
| `event_time` | Thời gian mua | Parse ngày/UTC, kiểm tra ngày thiếu, ngoài năm 2020 hoặc giá trị mặc định |
| `order_id` | Mã đơn | Đọc dạng chuỗi, kiểm tra thiếu và một đơn có bị gán nhiều khách không |
| `user_id` | Mã khách hàng ẩn danh | Đọc dạng chuỗi, phân biệt null, chuỗi rỗng và mã giả nếu có bằng chứng |
| `product_id` | Mã sản phẩm | Đọc dạng chuỗi, kiểm tra thiếu |
| `category_id`, `category_code` | Ngành hàng | Chuẩn hóa kiểu, thống kê thiếu và tính nhất quán |
| `brand` | Thương hiệu | Thống kê thiếu, chuẩn hóa khoảng trắng/cách viết |
| `price` | Giá trị giá được ghi trong dòng mua | Kiểm tra kiểu, đơn vị tiền, ý nghĩa đơn giá/thành tiền và giá trị không dương |

Schema này phải được đối chiếu file thực tế và tài liệu nguồn. Không chuyển mã ID dài sang float vì có thể mất chữ số. Không tự thêm `Quantity`, mã hóa đơn hủy kiểu UCI hoặc cột hoàn trả nếu nguồn không có.

## 3. Tech stack

| Thành phần | Công cụ | Cách sử dụng |
|---|---|---|
| Ngôn ngữ | Python | Một môi trường chung, khóa phiên bản dependencies sau khi kiểm tra tương thích |
| Khảo sát | PySpark, Jupyter | Xem mẫu gốc, đếm số trường, đo ô thiếu và phạm vi ngày |
| Pipeline dữ liệu | PySpark, chạy local | Dùng chung bộ đọc CSV với khảo sát, căn cột, kiểm tra chất lượng và tính RFM |
| Lưu trữ | Parquet, PyArrow | Ghi bảng sạch và RFM trên Windows khi máy thiếu Hadoop native |
| Phân tích | scikit-learn | Chuẩn hóa RFM, K-Means, GMM, BIRCH và Silhouette |
| Dashboard | Streamlit + Plotly | Đọc kết quả đã tính, lọc, vẽ biểu đồ, xuất bảng kết quả |
| Kiểm thử | pytest | Kiểm chứng quy tắc tiền xử lý, công thức RFM và đối chiếu đầu ra |
| Quản lý mã | Git + GitHub | Nhánh chức năng, review và tích hợp vào `dev` |

Scikit-learn nhận bảng RFM đã tổng hợp theo khách hàng. Dashboard đọc kết quả phân nhóm đã lưu để áp dụng bộ lọc.

Chưa cần xây API backend, cơ sở dữ liệu server, Kafka, HDFS, Docker hoặc cụm Spark nhiều máy. Spark local là môi trường thực nghiệm đơn máy; báo cáo đúng cấu hình và giới hạn của nó.

## 4. Luồng xử lý và các bảng bàn giao

```text
kz.csv -> đọc bản ghi bằng Spark
    ├── khảo sát cấu trúc, mẫu gốc, dữ liệu thiếu và khoảng ngày
    └── căn cột, kiểm tra và tách dòng lỗi
        -> giao dịch sạch -> RFM theo khách
        -> ngưỡng RFM / K-Means / GMM / BIRCH
        -> đánh giá và hồ sơ phân khúc
        -> dashboard, nhận xét và đề xuất CRM
```

| Đầu ra | Chủ trì | Nội dung bàn giao |
|---|---|---|
| `data/raw/` | Người 1 | File gốc giữ nguyên và metadata truy vết |
| `data/processed/purchases_clean.parquet` | Người 1 | Giao dịch hợp lệ để tính RFM |
| `data/quarantine/purchases_rejected.parquet` | Người 1 | Dòng bị tách và mã lý do |
| `reports/row_structure.csv`, `reports/column_quality.csv` | Người 1 | Số trường theo dòng và tỷ lệ thiếu của nhóm đủ 8 trường |
| `reports/cleaning_summary.json`, `reports/cleaning_quality.csv` | Người 1 | Số dòng giữ hoặc tách theo lý do và tỷ lệ thiếu trước–sau |
| `data/processed/customer_rfm.parquet` | Người 1 | Một dòng/khách: `customer_id`, `recency_days`, `frequency_orders`, `monetary_value`, `last_purchase_at` |
| `reports/rfm_summary.json`, `reports/rfm_hand_check.csv` | Người 1 | Ngày chốt, KPI, đối chiếu tổng M và ba mẫu RFM |
| `reports/run_metadata.json` | Người 2 | Cấu hình phần cứng, seed và cách đo thời gian so sánh |
| `data/curated/customer_segments.parquet` | Người 2 | RFM gốc, nhãn và tên phân khúc của các phương pháp đã chạy |
| `reports/segment_profiles.csv` | Người 2 | Quy mô, RFM điển hình, tỷ trọng giá trị mua, tỷ lệ mua lại theo từng phương pháp/nhóm |
| `reports/model_comparison.csv` | Người 2 | Cấu hình, chỉ số đánh giá, thời gian và nhận xét so sánh |
| `app/` | Người 3 | Dashboard đọc đầu ra chung, không chứa công thức KPI độc lập khác pipeline |

Người 1 và người 2 thống nhất schema bàn giao trước khi triển khai. Người 3 có thể dùng một mẫu nhỏ ghi rõ là dữ liệu minh họa để dựng giao diện, sau đó thay bằng kết quả thật. Không dùng số minh họa trong báo cáo kết quả.

## 5. Định nghĩa KPI và quy tắc chung

### RFM

- Chọn một **ngày chốt cố định**, mặc định là ngày sau ngày mua hợp lệ cuối cùng trong phạm vi phân tích. Lưu ngày chốt vào metadata, không dùng ngày hệ thống.
- **R:** số ngày từ ngày mua hợp lệ gần nhất của khách đến ngày chốt.
- **F:** số `order_id` riêng biệt của khách trong kỳ. Một đơn nhiều mặt hàng chỉ tính một lần.
- **M:** tổng giá trị mua được ghi nhận cho khách trên các dòng hợp lệ trong kỳ.
- Nếu nguồn xác nhận mỗi dòng là một sản phẩm được mua và `price` là khoản giá tương ứng, tính M bằng tổng `price`. Nếu ý nghĩa khác, cập nhật công thức dựa trên tài liệu nguồn trước khi tính. Không mặc định nhân với số lượng không có trong dữ liệu.
- Đơn vị tiền theo nguồn sau xác minh. Nếu không xác minh được đồng tiền, ghi “đơn vị tiền theo dữ liệu nguồn”, không tự gắn USD/GBP.
- Không gọi M là lợi nhuận, doanh thu thuần kế toán hoặc giá trị vòng đời khách hàng.

### Khách quay lại và các chỉ số dashboard

- **Tỷ lệ khách mua lại trong kỳ** = số khách có F >= 2 / tổng khách đủ điều kiện tính RFM.
- Đây là tỷ lệ mua lặp trong khoảng quan sát, không phải retention của một cohort ở tương lai. Các nhóm có thời gian quan sát khác nhau phải được giải thích khi so sánh.
- **Tỷ trọng giá trị mua của nhóm** = tổng M của nhóm / tổng M của toàn bộ khách được phân khúc.
- **Silhouette:** đánh giá mức phân tách các nhóm trên cùng không gian đặc trưng đã biến đổi và chuẩn hóa; không phải độ chính xác có nhãn thật.
- Luôn hiển thị độ bao phủ: số dòng, số đơn và giá trị mua có thể gán khách so với phần xác định được từ dữ liệu gốc. Không báo cáo một tỷ lệ về tiền nếu giá thiếu làm mẫu số không xác định đầy đủ.

## 6. Phân công chi tiết

### Người 1 — khảo sát, quy tắc, làm sạch, Parquet và RFM

**Giai đoạn 1: khảo sát dữ liệu, chốt phạm vi và quy tắc.**

- Ghi nguồn, phiên bản, phạm vi và giới hạn sử dụng trong `docs/data_source.md`.
- Dùng `notebooks/data_audit.ipynb` để xem vài bản ghi gốc trước, rồi đếm số trường trên toàn file. Sau đó xem mẫu dòng ngắn, thống kê ô thiếu trên nhóm đủ 8 trường và quan sát khoảng ngày.
- Chốt định nghĩa RFM, ngày chốt, xử lý thiếu khách/đơn/giá, ngày không hợp lệ và ngoại lệ.
- Phân biệt cột cần cho RFM với cột mô tả phụ. Thiếu brand/category không tự động loại giao dịch có đủ thông tin RFM.
- Không tự điền mã khách bằng mã đơn, gán nhiều khách thiếu ID thành một khách hoặc điền giá thiếu bằng 0.
- Các dòng giống nhau có thể là mua nhiều đơn vị cùng sản phẩm; cần tìm bằng chứng trước khi deduplicate. Không dùng `(order_id, product_id)` làm khóa duy nhất khi nguồn chưa xác nhận.
- Bản ghi ngày mặc định, ngoài phạm vi hoặc mâu thuẫn khách–đơn phải được kiểm tra và tách theo quy tắc xác định.

**Giai đoạn 2: làm sạch, lưu Parquet và tính RFM.**

- Dùng `scripts/run_pipeline.py` để chạy từ CSV gốc đến Parquet. `notebooks/cleaning_rfm.ipynb` trình bày cùng các bước.
- Căn cột cho dòng ngắn khớp mẫu, kiểm tra ngày, giá và mã. Tách dòng lỗi kèm lý do và ghi bảng chất lượng trước–sau.
- Xuất giao dịch sạch và bảng RFM theo schema bàn giao. Báo cáo số đơn và tỷ lệ khách mua lại trong kỳ.
- Giữ 3 bài kiểm thử cho sửa cấu trúc, làm sạch và đọc lại Parquet, công thức RFM có đơn nhiều dòng.
- Đối chiếu tổng M với tổng giá giao dịch sạch. Tính lại RFM của ba khách từ các dòng mua sạch.

**Hoàn thành khi:** có bảng chất lượng, định nghĩa KPI, pipeline chạy lại được, Parquet hợp lệ và các kiểm chứng RFM đã qua. Nếu số khách mua lặp quá ít hoặc dữ liệu thiếu làm kết quả không đáng tin, báo cáo ảnh hưởng sớm cho cả nhóm trước khi kết luận về phân khúc.

### Người 2 — phân nhóm theo ngưỡng RFM, K-Means, GMM và BIRCH

- Nhận bảng RFM, ngày chốt và định nghĩa KPI từ người 1.
- Xây baseline bằng ngưỡng trên RFM gốc. Có thể chọn ngưỡng theo phân vị. Khách có cùng giá trị F phải được xét cùng một ngưỡng.
- Định nghĩa các nhóm baseline bằng quy tắc có thứ tự ưu tiên, loại trừ lẫn nhau và phủ hết khách đủ điều kiện.
- Chạy **K-Means** và **GMM**. K-Means gán khách theo tâm cụm gần nhất. GMM cho phép các cụm có độ phân tán khác nhau. Dùng nhãn có xác suất cao nhất của GMM để so sánh.
- Chạy **BIRCH** để so cách gom khách thành các nhóm nhỏ trước khi tạo cụm cuối. Ghi `threshold` và số cụm thực tế để đánh giá tốc độ và chất lượng trên cùng dữ liệu.

#### Kế hoạch so sánh

1. **Chuẩn bị đầu vào chung.** Dùng cùng bảng RFM và cùng tập khách. Chọn cách biến đổi `log1p` nếu cần sau khi xem phân bố, rồi chuẩn hóa một lần cho các thuật toán. Giữ RFM gốc để áp dụng ngưỡng và mô tả nhóm.
2. **Thử cùng số cụm.** Bắt đầu với 3 đến 6 cụm cho K-Means, GMM và BIRCH. Ghi seed của K-Means và GMM, `n_init` của K-Means, kiểu hiệp phương sai của GMM, `threshold` của BIRCH và số cụm thực tế.
3. **Đo chất lượng.** Tính Silhouette trên cùng không gian RFM đã chuẩn hóa và cùng mẫu cố định, tối đa 5.000 khách nếu cần. Ghi cỡ mẫu và seed. Nếu nhãn trên mẫu không đủ điều kiện tính Silhouette, ghi không áp dụng.
4. **Đo thời gian.** Đo bước phân nhóm và gán nhãn riêng với bước tính Silhouette, trên cùng máy. Ghi phần cứng, phiên bản thư viện và số khách. Chạy làm nóng một lần rồi lấy trung vị của ít nhất ba lần đo.
5. **Lập bảng và giải thích.** Mỗi phương pháp có cấu hình, số nhóm, Silhouette, thời gian chạy, quy mô nhóm và nhận xét nguyên nhân chênh lệch. Dùng RFM gốc và tỷ lệ mua lại để mô tả nhóm. Kiểm tra xem các mô hình có tách được khách chỉ mua một đơn thành nhóm mới mua và nhóm đã lâu chưa mua hay không.

**Hoàn thành khi** cả bốn phương pháp chạy lại được, nhãn nối đúng theo `customer_id`, bảng đánh giá có số thực đo và mỗi phân khúc có mô tả hành vi.

### Người 3 — dashboard, nhận xét và đề xuất

- Thống nhất schema với hai người còn lại; dựng khung giao diện từ ngày 2.
- Dùng Streamlit + Plotly, đọc Parquet và bảng kết quả đã được bàn giao.
- Làm ba phần: tổng quan dữ liệu/chất lượng; hồ sơ phân khúc; so sánh phương pháp và đề xuất CRM.
- Hiển thị ngày chốt, phạm vi quan sát, đơn vị M, số khách được phân khúc và các giới hạn về độ bao phủ.
- Bộ lọc tối thiểu: phương pháp và phân khúc. Bộ lọc brand/category chỉ bổ sung khi có bảng hỗ trợ đúng mức dữ liệu.
- Nếu cho lọc ngày, phải phân biệt biểu đồ giao dịch theo ngày với nhãn phân khúc tại ngày chốt cố định. Không làm người xem tưởng bộ lọc đã huấn luyện lại mô hình hoặc tính lại RFM.
- Hiển thị khách mua lại, RFM điển hình, quy mô nhóm, tỷ trọng giá trị mua và chỉ số đánh giá mô hình. Nêu mẫu số khi KPI được tính trên tập đang lọc.
- Viết ít nhất 3 nhận xét có số liệu, mỗi nhận xét gắn với một hành động và điều kiện áp dụng. Ví dụ hướng phân tích: nhóm giá trị cao lâu chưa mua, nhóm mua thường xuyên, nhóm mới mua; không đặt sẵn số liệu/kết luận.
- Đề xuất chăm sóc ở mức giả thuyết cần thử nghiệm. Không khẳng định chiến dịch sẽ tăng doanh thu hoặc khách sẽ quay lại khi chưa có bằng chứng can thiệp.
- Tổng hợp ảnh dashboard, phần BI/nhận xét và bố cục slide. Người 1 viết phần dữ liệu/pipeline; người 2 viết phần phương pháp/thực nghiệm; cả nhóm cùng hoàn thiện báo cáo và tập demo.

**Hoàn thành khi:** dashboard chạy từ hướng dẫn chung, số liệu khớp các bảng nguồn, có bộ lọc hoạt động, ít nhất 3 nhận xét kiểm chứng được và giải thích được các giới hạn.

## 7. Trạng thái hiện tại và kế hoạch hiện thực phần còn lại

### 7.1. Mốc đã hoàn thành trên nhánh `dev`

Phần Người 1 đã có thể xem là đầu vào ổn định cho giai đoạn mô hình, với điều kiện không đổi schema mà không cập nhật hợp đồng dữ liệu:

- Đã có khảo sát dữ liệu, quy tắc căn dòng ngắn, làm sạch và tách dòng lỗi.
- Đã có pipeline PySpark từ `data/raw/kz.csv` đến giao dịch sạch và RFM.
- Đã có kiểm thử sửa cấu trúc, kiểm thử làm sạch/Parquet và mẫu tính tay RFM.
- Đã có các báo cáo chất lượng và bàn giao schema cho Người 2–3.
- Snapshot hiện tại gồm 234.359 khách, ngày chốt 22/11/2020, 31,9096% khách có ít nhất hai đơn và tổng M 118.372.961,6200 đơn vị giá theo nguồn.

Các phần sau đây là phạm vi còn lại tại thời điểm lập kế hoạch; đến lần chạy hoàn tất ngày 06/11/2026, toàn bộ đã được hiện thực và kiểm chứng:

1. Baseline phân khúc theo ngưỡng RFM.
2. K-Means, GMM và BIRCH trên cùng tập khách.
3. Đánh giá Silhouette, thời gian chạy, hồ sơ cụm và bảng so sánh.
4. File nhãn phân khúc dùng chung và dữ liệu curated cho dashboard.
5. Dashboard Streamlit/Plotly, nhận xét định lượng và đề xuất CRM.
6. Kiểm thử mô hình, kiểm thử hợp đồng đầu ra, kiểm thử dashboard và chạy toàn pipeline.
7. README hoàn chỉnh, báo cáo, slide, ảnh/log minh chứng và kịch bản demo.

### 7.2. Quyết định kỹ thuật chung

- `customer_id` luôn là chuỗi và là khóa nối duy nhất. Trước khi chạy mô hình phải kiểm tra một dòng/khách, không null và không trùng.
- Giữ RFM gốc để tính KPI và giải thích. Tạo ma trận mô hình riêng theo thứ tự `recency_days`, `frequency_orders`, `monetary_value`.
- Với mô hình học máy, dùng `log1p` cho cả ba đặc trưng không âm, sau đó `StandardScaler`. Lưu thông số biến đổi và không ghi đè RFM gốc.
- Baseline dùng RFM gốc. Điểm R đảo chiều; F và M cùng chiều. Dùng percentile rank với `method="average"` trước khi chia bốn mức để các giá trị F bằng nhau không bị tách tùy ý.
- Tất cả phương pháp dùng cùng cohort 234.359 khách sau bước kiểm tra schema. Không tự loại ngoại lệ riêng cho một thuật toán.
- Seed mặc định là `42`. Sắp xếp theo `customer_id` trước khi lấy mẫu hoặc ghi file để kết quả tái lập được.
- Huấn luyện/gán nhãn trên toàn bộ cohort. Silhouette tính trên cùng mẫu cố định tối đa 5.000 khách để tránh chi phí bộ nhớ bậc hai; lưu seed, danh sách/hash mẫu và cỡ mẫu.
- Tách thời gian `fit_predict` khỏi thời gian tính Silhouette. Mỗi cấu hình làm nóng một lần, đo ít nhất ba lần và báo cáo trung vị.
- Nhãn cụm số của thuật toán không có ý nghĩa kinh doanh. Sau khi lập profile, ánh xạ ổn định thành `S1...Sk`; tên kinh doanh nằm trong một file mapping được review, không hard-code rải rác trong dashboard.
- Dashboard chỉ đọc artifact đã tính. Bộ lọc không huấn luyện lại mô hình, không tính lại RFM và không thay đổi ngày chốt.

### 7.3. Hợp đồng file cần tạo

```text
src/segmentation/
    __init__.py
    features.py          # kiểm tra schema, cohort, log1p và chuẩn hóa
    baseline.py          # điểm RFM và 5 nhóm baseline loại trừ lẫn nhau
    models.py            # K-Means, GMM, BIRCH và cấu hình ứng viên
    evaluation.py        # Silhouette, timing, profile và kiểm tra đối chiếu
    pipeline.py          # điều phối, chọn mô hình và ghi artifact
scripts/
    run_segmentation.py  # CLI cho phần Người 2
    run_all.py           # chạy data/RFM rồi segmentation theo thứ tự
app/
    app.py               # entrypoint Streamlit
    data.py              # đọc/kiểm tra artifact, cache dữ liệu
    charts.py            # biểu đồ thuần, không tự tính KPI khác pipeline
config/
    segment_labels.json  # nhãn và giả thuyết hành động sau khi xem profile
tests/
    test_features.py
    test_baseline.py
    test_models.py
    test_artifacts.py
    test_dashboard.py
docs/
    modeling.md
    dashboard.md
    results.md
```

Artifact đầu ra:

| File | Grain và trường tối thiểu | Điều kiện đối chiếu |
|---|---|---|
| `data/curated/customer_segments.parquet` | Một dòng/khách/phương pháp: RFM gốc, `method`, `segment_id`, `segment_name`, `is_repeat_customer`; GMM có thể thêm xác suất | Mỗi phương pháp đủ đúng 234.359 khách, không trùng khóa `(customer_id, method)` |
| `reports/model_comparison.csv` | Một dòng/cấu hình: phương pháp, tham số, số cụm yêu cầu/thực tế, Silhouette, cỡ mẫu, thời gian từng lần và trung vị, trạng thái chọn | Không so Silhouette từ không gian hoặc mẫu khác nhau |
| `reports/segment_profiles.csv` | Một dòng/phương pháp/phân khúc: số khách, tỷ trọng khách, median R/F/M, tổng M, tỷ trọng M, số và tỷ lệ khách mua lại | Tổng số khách và tổng M của từng phương pháp phải khớp RFM nguồn |
| `reports/run_metadata.json` | Thời điểm chạy, commit, Python/OS/CPU/RAM, phiên bản thư viện, seed, ngày chốt, input hash, cấu hình biến đổi | Đủ thông tin để chạy và giải thích lại thí nghiệm |
| `reports/model_selection.json` | Cấu hình được chọn, tiêu chí chọn và lý do loại cấu hình lỗi/thoái hóa | Không mặc định phương pháp có Silhouette cao nhất là tốt nhất về kinh doanh |

### 7.4. Baseline RFM bắt buộc

Baseline dùng bốn mức cho từng R/F/M và năm nhóm có thứ tự ưu tiên sau:

1. `champions`: R >= 3, F >= 3, M >= 3.
2. `loyal`: F >= 3 và R >= 2, sau khi đã lấy `champions`.
3. `high_value_at_risk`: M >= 3 và R <= 2, sau hai nhóm trên.
4. `new_or_promising`: R >= 3 và F <= 2, sau ba nhóm trên.
5. `needs_attention`: các khách còn lại.

Các ngưỡng và thứ tự phải nằm trong code/config, có test phủ hết khách và không giao nhau. Đây là baseline giải thích được, không phải chân lý về CRM; tên nhóm có thể điều chỉnh sau khi xem profile nhưng quy tắc đã dùng phải được lưu cùng kết quả.

### 7.5. Kế hoạch thí nghiệm mô hình

| Phương pháp | Cấu hình cần chạy | Ghi chú |
|---|---|---|
| Baseline RFM | 5 nhóm cố định | Là mốc giải thích được và phương án bắt buộc để so với K-Means |
| K-Means | `k=3..6`, `random_state=42`, `n_init=20`, `max_iter=300` | Ghi inertia để chẩn đoán, không dùng inertia thay Silhouette |
| GMM | `k=3..6`, `random_state=42`, `covariance_type="full"`, `n_init=3`, có `reg_covar` | Ghi hội tụ và phân bố xác suất gán nhãn |
| BIRCH | `n_clusters=3..6`, thử `threshold` trong tập nhỏ đã định nghĩa | Ghi threshold và số cụm thực tế vì BIRCH có thể tạo số cụm khác yêu cầu |

Thực hiện hai lớp so sánh:

1. So sánh công bằng chính ở năm nhóm/cụm cho cả bốn phương pháp.
2. Với từng thuật toán học máy, chọn thêm cấu hình tốt nhất trong `k=3..6` theo Silhouette, nhưng loại cấu hình có cụm rỗng, chỉ một cụm, hoặc cụm quá nhỏ dưới ngưỡng đã công bố. Nếu các chỉ số gần nhau, ưu tiên cấu hình dễ giải thích và cân bằng hơn.

Mỗi cụm sau khi chọn được remap ổn định theo profile, ưu tiên tổng/median M giảm dần, F giảm dần và R tăng dần. Sau đó mới review và điền tên kinh doanh trong `config/segment_labels.json`.

### 7.6. Các giai đoạn hiện thực

#### Giai đoạn A — khóa hợp đồng và môi trường

- Bổ sung `numpy`, `pandas`, `scikit-learn`, `streamlit` và `plotly` vào `requirements.txt` với khoảng phiên bản tương thích Python 3.11.
- Tạo validator cho schema RFM, kiểu dữ liệu, null, trùng khách, giá trị âm và số dòng.
- Tạo CLI `scripts/run_segmentation.py` nhận đường dẫn input/output/report, seed và cỡ mẫu Silhouette; không hard-code đường dẫn ngoài giá trị mặc định của repo.
- Chốt schema artifact với Người 3 trước khi dựng UI.

**Nghiệm thu:** validator chạy qua bảng bàn giao thật và thất bại rõ ràng trên fixture sai schema/null/trùng khóa.

#### Giai đoạn B — feature pipeline và baseline

- Đọc Parquet bằng PyArrow/Pandas, sắp xếp khóa, tạo `is_repeat_customer = frequency_orders >= 2`.
- Tạo RFM percentile scores, năm nhóm baseline và ma trận `log1p + StandardScaler` dùng chung.
- Lưu metadata của scaler, thứ tự cột, số khách và thống kê trước/sau biến đổi.

**Nghiệm thu:** không mất khách, baseline phủ 100%, các nhóm loại trừ lẫn nhau, phép biến đổi hữu hạn và tái lập với cùng input.

#### Giai đoạn C — K-Means, GMM và BIRCH

- Tách hàm tạo model khỏi vòng chạy benchmark để unit test được.
- Chạy toàn bộ grid nhỏ đã chốt, bắt lỗi hội tụ/thoái hóa và vẫn ghi một dòng thất bại vào bảng so sánh.
- Dùng cùng ma trận feature và cùng mẫu Silhouette; không fit scaler lại cho từng model.
- Lưu nhãn của baseline, cấu hình năm cụm và cấu hình được chọn của từng thuật toán.

**Nghiệm thu:** cùng seed cho cùng nhãn/kết quả; mỗi model được chọn có từ hai cụm hợp lệ; nhãn nối đúng 234.359 `customer_id`.

#### Giai đoạn D — đánh giá, profile và artifact

- Tính Silhouette, thời gian, quy mô cụm, median R/F/M, tỷ trọng M và tỷ lệ mua lại trong kỳ.
- Kiểm tra tổng số khách, tổng M và số khách mua lại sau group-by phải khớp báo cáo RFM.
- Tạo bảng so sánh chứa cả baseline, cấu hình năm cụm và cấu hình được chọn.
- Viết `docs/modeling.md` mô tả feature, tham số, cách đo, cách chọn và giới hạn của Silhouette.

**Nghiệm thu:** bốn artifact trong Mục 7.3 được tạo tự động từ một lệnh, schema ổn định và mọi phép đối chiếu đều qua.

#### Giai đoạn E — dashboard và insight

Dashboard gồm bốn trang hoặc bốn tab:

1. **Chất lượng và phạm vi:** dòng gốc/sạch/tách, độ bao phủ 22,81%, phạm vi ngày, ngày chốt và cảnh báo đồng tiền chưa xác minh.
2. **Hồ sơ phân khúc:** bộ lọc phương pháp/phân khúc, KPI số khách, tỷ lệ mua lại, median R/F/M, tỷ trọng M; biểu đồ quy mô và profile chuẩn hóa.
3. **So sánh phương pháp:** Silhouette, thời gian, số cụm, phân bố quy mô; giải thích baseline và giới hạn so sánh.
4. **Hành động CRM:** ít nhất ba insight có số thực đo, giả thuyết chiến dịch, đối tượng, KPI theo dõi, rủi ro và điều kiện dừng/thử nghiệm.

Scatter plot nhiều điểm phải dùng sample cố định và ghi cỡ mẫu; KPI/tables vẫn dùng toàn bộ dữ liệu. Không hiển thị `customer_id` như thông tin cần hành động và không cho tải raw data mặc định.

**Nghiệm thu:** `streamlit run app/app.py` khởi động được; bộ lọc không làm thay đổi tổng ngoài phạm vi đã chọn; số trên UI khớp `segment_profiles.csv`; không có công thức KPI độc lập mâu thuẫn pipeline.

#### Giai đoạn F — kiểm thử, tài liệu và sản phẩm nộp

- Unit test: schema/feature, tie ở F, baseline precedence, cấu hình model, metric không áp dụng và remap nhãn.
- Integration test trên fixture RFM nhỏ: chạy bốn phương pháp, ghi/đọc Parquet/CSV/JSON, kiểm tra cardinality và tổng M.
- Dashboard smoke test bằng `streamlit.testing.v1.AppTest` hoặc lớp đọc dữ liệu tách biệt nếu môi trường không hỗ trợ render UI.
- Chạy lại `pytest -q`, pipeline Người 1, segmentation và dashboard theo README trong môi trường sạch.
- Bổ sung README với bốn lệnh: cài đặt, data/RFM, segmentation, dashboard; ghi Java/Python tương thích và vị trí artifact.
- Hoàn thiện `docs/results.md`, sơ đồ kiến trúc, bảng so sánh, ít nhất ba insight, giới hạn, công cụ AI đã dùng và phân công đóng góp.
- Chuẩn bị ảnh/log chạy pipeline, ảnh dashboard, báo cáo PDF/DOCX, slide và kịch bản demo có thể chạy lại.

**Nghiệm thu:** một người không viết module vẫn có thể làm theo README để tạo lại artifact và mở dashboard; số liệu trong dashboard, báo cáo và slide khớp nhau.

### 7.7. Thứ tự PR và phân công phần còn lại

| PR | Nhánh | Chủ trì | Phạm vi | Phụ thuộc |
|---|---|---|---|---|
| 1 | `feat/segmentation-contract` | Người 2 | Dependencies, schema validator, feature pipeline, baseline, test | RFM Người 1 |
| 2 | `feat/segmentation` | Người 2 | Ba model, benchmark, selection, profile, artifact, docs modeling | PR 1 |
| 3 | `feat/dashboard` | Người 3 | Data loader, charts, filters, KPI, CRM page, UI tests | Schema PR 1; dữ liệu thật từ PR 2 |
| 4 | `docs/final-deliverables` | Cả nhóm | README end-to-end, results, kiến trúc, báo cáo, slide, demo | PR 2–3 |

Người 1 review các phép đối chiếu số khách/tổng M/độ bao phủ. Người 2 review số liệu mô hình trên dashboard. Người 3 review tính dễ hiểu và điều kiện áp dụng của insight. Mỗi PR vào `dev` phải kèm lệnh chạy và kết quả test.

### 7.8. Rủi ro cần kiểm soát

| Rủi ro | Cách xử lý trong code/báo cáo |
|---|---|
| F có nhiều giá trị bằng 1 làm chia quantile lỗi | Dùng percentile rank giữ tie, test riêng trường hợp nhiều giá trị bằng nhau |
| RFM lệch mạnh và khách M rất lớn chi phối khoảng cách | Dùng `log1p + StandardScaler`; báo cáo phân bố gốc và không tự xóa khách giá trị cao |
| Silhouette toàn bộ 234k khách tốn bộ nhớ lớn | Dùng cùng mẫu cố định tối đa 5.000; ghi rõ đây là ước lượng trên mẫu |
| Cụm rất nhỏ hoặc model không hội tụ | Đánh dấu cấu hình không hợp lệ, ghi lý do, không âm thầm bỏ dòng khỏi bảng |
| Nhãn cluster đổi số giữa lần chạy | Seed cố định, sort input và remap theo profile; không dùng raw cluster ID làm tên kinh doanh |
| Chỉ 22,81% dòng gốc đủ điều kiện | Luôn hiển thị coverage và giới hạn suy rộng; không gọi kết quả là toàn bộ khách cửa hàng |
| Chưa xác minh đồng tiền và quyền phân phối file | Dùng “đơn vị giá theo nguồn”, không commit dữ liệu, ghi URL và điều kiện sử dụng |
| Dashboard và báo cáo lệch KPI | Dashboard đọc artifact profile; thêm test đối chiếu và một bước review số liệu trước khi chụp ảnh |

## 8. Tiến độ mẫu cho 5 ngày

Đây là lịch tương đối, giả định khoảng 3–4 giờ/người/ngày; điều chỉnh theo hạn nộp thực tế.

| Ngày | Người 1 | Người 2 | Người 3 | Mốc bàn giao |
|---|---|---|---|---|
| 1 | Khảo sát nguồn và chất lượng; đề xuất quy tắc | Thiết kế baseline, cấu hình và cách đánh giá | Chốt người dùng, câu hỏi và bố cục dashboard | Cả nhóm chốt KPI, phạm vi, schema bàn giao |
| 2 | Làm sạch, Parquet, RFM và mẫu tính tay | Dựng baseline trên mẫu RFM | Dựng giao diện và biểu đồ bằng mẫu có nhãn minh họa | Có pipeline và RFM bản đầu |
| 3 | Kiểm chứng và ổn định đầu ra dữ liệu | Chạy ngưỡng RFM, K-Means, GMM và BIRCH. Xuất hồ sơ nhóm và bảng so sánh | Nối kết quả thật, hoàn thiện bộ lọc | Có bảng so sánh và dashboard bản đầu |
| 4 | Viết phần dữ liệu, chất lượng, kiến trúc | Viết phần thực nghiệm và giải thích chênh lệch giữa các phương pháp | Viết nhận xét, đề xuất, chụp dashboard | Báo cáo nháp, đối chiếu số liệu toàn bộ |
| 5 | Chạy pipeline từ đầu theo README | Kiểm tra tái lập và số liệu trong báo cáo | Hoàn thiện dashboard, slide, kịch bản demo | Cả nhóm review, tập trình bày và chốt sản phẩm |

## 9. Làm việc trên GitHub

- `main`: bản ổn định; `dev`: tích hợp công việc của nhóm.
- Nhánh đề xuất: `feat/data-rfm`, `feat/segmentation`, `feat/dashboard`.
- Mỗi người mở PR vào `dev`, ghi rõ thay đổi, cách chạy và bằng chứng kiểm chứng. Một người khác review trước khi merge.
- Thống nhất sớm tên cột và kiểu dữ liệu; thay đổi schema cần cập nhật đồng thời bên tạo và bên dùng.
- Không commit raw/processed data dung lượng lớn, môi trường ảo, cache Spark hoặc thông tin đăng nhập. Bước triển khai phải thêm `.gitignore` thích hợp.
- README phải có cách lấy đúng phiên bản dữ liệu, cài môi trường Python/Java tương thích, chạy pipeline, chạy phân nhóm và mở dashboard.
- Dữ liệu mẫu nếu chia sẻ phải tuân thủ điều kiện của nguồn. Ghi rõ công cụ AI đã dùng và cách nhóm tự kiểm chứng kết quả.

## 10. Điều kiện hoàn thành bài

- [x] Nguồn, điều kiện sử dụng, phiên bản dữ liệu và phạm vi thời gian được ghi rõ.
- [x] Có ít nhất 2 câu hỏi kinh doanh và người dùng dashboard xác định.
- [x] Có bảng chất lượng trước–sau, các quy tắc và số dòng tách theo lý do.
- [x] RFM đúng trên mẫu tính tay; pipeline chạy lại không tự nhân dữ liệu.
- [x] Ngưỡng RFM, K-Means, GMM và BIRCH dùng cùng tập khách. Bảng so sánh ghi số thực đo và nguyên nhân chênh lệch.
- [x] Có Silhouette hợp lệ hoặc giải thích trường hợp không áp dụng, tỷ lệ mua lại trong kỳ và RFM.
- [x] Dashboard nhất quán với dữ liệu, có bộ lọc và ít nhất 3 nhận xét dựa trên số liệu.
- [x] Có đề xuất CRM, rủi ro, giới hạn dữ liệu và điều kiện áp dụng.
- [x] Có README, mã nguồn, kiểm thử, báo cáo, slide/demo và phân công đóng góp.
- [x] Cả 3 người có tài liệu định nghĩa KPI, báo cáo, slide và kịch bản demo để ôn phần phụ trách.

Quy mô và hiệu năng phải được báo cáo trung thực. Số dòng lớn hơn một triệu không tự chứng minh hệ thống phân tán cần thiết. Nếu bổ sung dữ liệu tăng tải mô phỏng, tách khỏi kết quả kinh doanh trên dữ liệu thật và ghi rõ cách tạo.

## 11. Tài liệu tham khảo kỹ thuật

- PySpark: <https://spark.apache.org/docs/latest/api/python/getting_started/install.html>.
- K-Means: <https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html>.
- GMM: <https://scikit-learn.org/stable/modules/mixture.html>.
- BIRCH: <https://scikit-learn.org/stable/modules/generated/sklearn.cluster.Birch.html>.
- Silhouette: <https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html>.
- Streamlit: <https://docs.streamlit.io/get-started>.

Các chi tiết chưa được xác minh từ file thực tế phải được cập nhật trong giai đoạn khảo sát, không trình bày như kết quả đã đo.

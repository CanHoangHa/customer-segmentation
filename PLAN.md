# Kế hoạch bài tập lớn: phân khúc khách hàng theo hành vi mua sắm

## 1. Phạm vi đã thống nhất

- Đề tài 04: phân khúc khách hàng theo hành vi mua sắm.
- Nhóm gồm 3 người, ưu tiên hoàn thành một pipeline dễ chạy lại và giải thích được.
- Dataset: **eCommerce Purchase History from Electronics Store**, do REES46/Open CDP công bố; dùng giao dịch thực tế năm 2020 đã ẩn danh.
- Phương pháp so sánh chính: **phân nhóm theo ngưỡng RFM và K-Means**.
- Người dùng dashboard: nhân viên CRM hoặc quản lý marketing của cửa hàng điện tử.
- Nhánh tích hợp: `dev`. Kế hoạch này chưa bao gồm tải dữ liệu hay triển khai pipeline.

Tên đề tài đề xuất: **Phân khúc khách hàng cửa hàng điện tử từ dữ liệu giao dịch thực tế bằng RFM và K-Means**.

### Câu hỏi kinh doanh

1. Khách hàng khác nhau như thế nào về thời gian mua gần nhất, số lần mua và giá trị mua?
2. Nhóm khách nào đóng góp giá trị mua cao nhưng đã lâu chưa quay lại, cần ưu tiên chăm sóc?
3. Cách chia nhóm theo ngưỡng RFM và K-Means khác nhau thế nào về mức phân tách, quy mô nhóm, thời gian chạy và khả năng giải thích?

Tên nhóm và nhận xét kinh doanh chỉ được đặt sau khi xem kết quả. Không đặt trước kết luận rằng K-Means tốt hơn hoặc một nhóm chắc chắn đã rời bỏ cửa hàng.

## 2. Nguồn dữ liệu và việc cần xác minh

- Nguồn nhà cung cấp: <https://data.rees46.com/>.
- Dataset: <https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-electronics-store>.
- Mục purchases của nhà cung cấp mô tả khoảng **2,5 triệu dòng mua hàng**, giai đoạn **04–11/2020**, file `purchases.csv.gz` khoảng 50 MB. Đây là thông tin công bố, chưa phải số liệu nhóm tự đo; không gọi 2,5 triệu dòng là 2,5 triệu đơn hàng.
- Người 1 phải ghi tên file, phiên bản, URL tải, ngày tải, SHA-256, số dòng thực đọc, thời gian thực tế và điều kiện sử dụng/ghi nguồn. Không coi dữ liệu công khai là tự động có giấy phép phân phối lại.
- Nếu bản Kaggle và bản trực tiếp có khác biệt về thời gian hoặc số dòng, ghi rõ phiên bản được chọn và dùng nhất quán cho cả hai phương pháp. Không ghép các bản khác nhau để tăng số dòng.
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
| Khảo sát | pandas, Jupyter | Đọc mẫu, kiểm tra schema và kiểm chứng trên tập dữ liệu nhỏ |
| Pipeline dữ liệu | PySpark DataFrame / Spark SQL, chạy local | Đọc dữ liệu, kiểm tra chất lượng, làm sạch và tổng hợp RFM |
| Lưu trữ | Parquet, engine PyArrow khi cần | Lưu bảng sạch, RFM và kết quả phân nhóm |
| Phân tích | scikit-learn | Biến đổi/chuẩn hóa RFM, K-Means và Silhouette |
| Dashboard | Streamlit + Plotly | Đọc kết quả đã tính, lọc, vẽ biểu đồ, xuất bảng kết quả |
| Kiểm thử | pytest | Kiểm chứng quy tắc tiền xử lý, công thức RFM và đối chiếu đầu ra |
| Quản lý mã | Git + GitHub | Nhánh chức năng, review và tích hợp vào `dev` |

Chỉ đưa bảng RFM đã tổng hợp theo khách hàng từ Spark sang scikit-learn; tránh đưa toàn bộ dữ liệu giao dịch về pandas. Dashboard không chạy lại Spark hoặc huấn luyện K-Means mỗi khi đổi bộ lọc.

Chưa cần xây API backend, cơ sở dữ liệu server, Kafka, HDFS, Docker hoặc cụm Spark nhiều máy. Spark local là môi trường thực nghiệm đơn máy; báo cáo đúng cấu hình và giới hạn của nó.

## 4. Luồng xử lý và các bảng bàn giao

```text
Dữ liệu gốc + metadata nguồn
    -> khảo sát schema và chất lượng
    -> giao dịch sạch + các dòng tách riêng + log quy tắc
    -> bảng RFM theo khách hàng
    -> baseline theo ngưỡng RFM / K-Means
    -> đánh giá và hồ sơ phân khúc
    -> dashboard, nhận xét và đề xuất CRM
```

Các đường dẫn dưới đây là cấu trúc dự kiến, chưa được tạo trong bước lập kế hoạch này.

| Đầu ra dự kiến | Chủ trì | Nội dung bàn giao |
|---|---|---|
| `data/raw/` | Người 1 | File gốc giữ nguyên và metadata truy vết |
| `data/processed/purchases_clean.parquet` | Người 1 | Giao dịch hợp lệ để tính RFM |
| `data/quarantine/` | Người 1 | Dòng bị tách với mã lý do; không âm thầm bỏ dữ liệu |
| `reports/data_quality.json` và bản tóm tắt | Người 1 | Thống kê trước–sau, từng lý do xử lý, ảnh hưởng tới độ bao phủ |
| `data/processed/customer_rfm.parquet` | Người 1 | Một dòng/khách: `customer_id`, `recency_days`, `frequency_orders`, `monetary_value`, `last_purchase_at` |
| `reports/run_metadata.json` | Người 1 phối hợp người 2 | Phiên bản nguồn, ngày chốt, phạm vi, cấu hình, seed và thời gian chạy |
| `data/curated/customer_segments.parquet` | Người 2 | RFM gốc, nhãn baseline, nhãn K-Means và tên phân khúc sau diễn giải |
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

- Kiểm tra nguồn và quyền sử dụng; đọc mẫu rồi đo chất lượng toàn bộ file.
- Báo cáo số dòng, khách, đơn, sản phẩm, khoảng ngày, thiếu theo cột, dòng giống nhau, giá không dương và ngày bất thường nếu có.
- Kiểm tra số đơn/khách và tỷ lệ mua lặp để đánh giá dữ liệu có đủ tín hiệu phân khúc hay không.
- Chốt định nghĩa RFM, ngày chốt, xử lý thiếu khách/đơn/giá, ngày không hợp lệ và ngoại lệ.
- Phân biệt cột cần cho RFM với cột mô tả phụ. Thiếu brand/category không tự động loại giao dịch có đủ thông tin RFM.
- Không tự điền mã khách bằng mã đơn, gán nhiều khách thiếu ID thành một khách hoặc điền giá thiếu bằng 0.
- Các dòng giống nhau có thể là mua nhiều đơn vị cùng sản phẩm; cần tìm bằng chứng trước khi deduplicate. Không dùng `(order_id, product_id)` làm khóa duy nhất khi nguồn chưa xác nhận.
- Bản ghi ngày mặc định, ngoài phạm vi hoặc mâu thuẫn khách–đơn phải được kiểm tra và tách theo quy tắc xác định.

**Giai đoạn 2: làm sạch, lưu Parquet và tính RFM.**

- Viết pipeline PySpark có cấu hình đầu vào/đầu ra, schema và log số dòng qua từng bước.
- Giữ raw nguyên vẹn; tách dòng lỗi với lý do, ghi bảng chất lượng trước–sau và thống kê chênh lệch tiền có thể xác định.
- Xuất giao dịch sạch và RFM theo schema bàn giao.
- Viết script chạy lại thay vì chỉ giữ thao tác trong notebook.
- Kiểm chứng ít nhất 3 tình huống: RFM của một khách tính tay; một đơn nhiều dòng không tăng F; dòng thiếu khách/giá/ngày được tách đúng quy tắc.
- Bổ sung đối chiếu tổng M theo khách với tổng giá trị giao dịch sạch trong cùng phạm vi và sai số cho phép.

**Hoàn thành khi:** có bảng chất lượng, định nghĩa KPI, pipeline chạy lại được, Parquet hợp lệ và các kiểm chứng RFM đã qua. Nếu số khách mua lặp quá ít hoặc dữ liệu thiếu làm kết quả không đáng tin, báo cáo ảnh hưởng sớm cho cả nhóm trước khi kết luận về phân khúc.

### Người 2 — baseline theo ngưỡng RFM và K-Means

- Nhận bảng RFM và ngày chốt từ người 1; không tự thay đổi tập khách hoặc cách tính KPI.
- Xây baseline bằng các ngưỡng RFM có cấu hình. Có thể dùng quantile; phải xử lý trường hợp nhiều khách có cùng F mà không tùy tiện chia các giá trị bằng nhau vào nhóm khác nhau.
- Định nghĩa các nhóm baseline bằng quy tắc có thứ tự ưu tiên, loại trừ lẫn nhau và phủ hết khách đủ điều kiện.
- Khảo sát độ lệch R/F/M, thử biến đổi `log1p` khi phù hợp với miền giá trị rồi chuẩn hóa. Giữ RFM gốc để diễn giải.
- Chạy K-Means, đề xuất thử k = 3..6, seed = 42, `n_init` khai báo rõ; điều chỉnh nếu dữ liệu không hỗ trợ số cụm đó.
- Đánh giá Silhouette cùng quy mô cụm và khả năng giải thích. Không chọn cụm chỉ theo một chỉ số.
- Khi tính Silhouette cần lấy mẫu, dùng cùng tập khách lấy mẫu cố định cho hai phương pháp và các cấu hình; ghi cỡ mẫu, seed và kiểm tra mẫu có đủ nhãn hợp lệ. Có thể giới hạn 5.000 khách để tránh chi phí quá lớn.
- So sánh trên cùng tập khách và cùng không gian RFM đã chuẩn hóa. Nếu không thỏa điều kiện tính Silhouette thì ghi không áp dụng, không gán 0.
- Đo riêng thời gian phân nhóm và thời gian đánh giá. Ghi phần cứng, phiên bản, số khách, cấu hình; có một lần warm-up và ít nhất 3 lần đo để báo cáo trung vị.
- Kiểm tra độ ổn định K-Means qua một số seed nếu thời gian cho phép; không dùng seed khác nhau làm lợi thế cho một cấu hình.
- Xuất nhãn hai phương pháp, hồ sơ phân khúc và bảng so sánh. Giải thích tên nhóm dựa trên RFM thực đo; không coi các nhãn số 0, 1, 2 là thứ hạng.

**Hoàn thành khi:** hai cách chạy lại được, nhãn nối đúng theo `customer_id`, bảng đánh giá có số thực đo và mỗi phân khúc có mô tả hành vi rõ ràng.

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

## 7. Tiến độ mẫu cho 5 ngày

Đây là lịch tương đối, giả định khoảng 3–4 giờ/người/ngày; điều chỉnh theo hạn nộp thực tế.

| Ngày | Người 1 | Người 2 | Người 3 | Mốc bàn giao |
|---|---|---|---|---|
| 1 | Khảo sát nguồn và chất lượng; đề xuất quy tắc | Thiết kế baseline, cấu hình và cách đánh giá | Chốt người dùng, câu hỏi và bố cục dashboard | Cả nhóm chốt KPI, phạm vi, schema bàn giao |
| 2 | Làm sạch, Parquet, RFM và mẫu tính tay | Dựng baseline trên mẫu RFM | Dựng giao diện và biểu đồ bằng mẫu có nhãn minh họa | Có pipeline và RFM bản đầu |
| 3 | Kiểm chứng và ổn định đầu ra dữ liệu | Chạy baseline/K-Means, đánh giá, xuất hồ sơ nhóm | Nối kết quả thật, hoàn thiện bộ lọc | Có bảng so sánh và dashboard bản đầu |
| 4 | Viết phần dữ liệu, chất lượng, kiến trúc | Viết phần phương pháp và thực nghiệm | Viết nhận xét, đề xuất, chụp dashboard | Báo cáo nháp, đối chiếu số liệu toàn bộ |
| 5 | Chạy pipeline từ đầu theo README | Kiểm tra tái lập và số liệu trong báo cáo | Hoàn thiện dashboard, slide, kịch bản demo | Cả nhóm review, tập trình bày và chốt sản phẩm |

## 8. Làm việc trên GitHub

- `main`: bản ổn định; `dev`: tích hợp công việc của nhóm.
- Nhánh đề xuất: `feature/data-rfm`, `feature/segmentation`, `feature/dashboard`.
- Mỗi người mở PR vào `dev`, ghi rõ thay đổi, cách chạy và bằng chứng kiểm chứng. Một người khác review trước khi merge.
- Thống nhất sớm tên cột và kiểu dữ liệu; thay đổi schema cần cập nhật đồng thời bên tạo và bên dùng.
- Không commit raw/processed data dung lượng lớn, môi trường ảo, cache Spark hoặc thông tin đăng nhập. Bước triển khai phải thêm `.gitignore` thích hợp.
- README phải có cách lấy đúng phiên bản dữ liệu, cài môi trường Python/Java tương thích, chạy pipeline, chạy phân nhóm và mở dashboard.
- Dữ liệu mẫu nếu chia sẻ phải tuân thủ điều kiện của nguồn. Ghi rõ công cụ AI đã dùng và cách nhóm tự kiểm chứng kết quả.

## 9. Điều kiện hoàn thành bài

- [ ] Nguồn, điều kiện sử dụng, phiên bản dữ liệu và phạm vi thời gian được ghi rõ.
- [ ] Có ít nhất 2 câu hỏi kinh doanh và người dùng dashboard xác định.
- [ ] Có bảng chất lượng trước–sau, các quy tắc và số dòng tách theo lý do.
- [ ] RFM đúng trên mẫu tính tay; pipeline chạy lại không tự nhân dữ liệu.
- [ ] Baseline và K-Means dùng cùng tập khách; kết quả so sánh là số thực đo.
- [ ] Có Silhouette hợp lệ hoặc giải thích trường hợp không áp dụng, tỷ lệ mua lại trong kỳ và RFM.
- [ ] Dashboard nhất quán với dữ liệu, có bộ lọc và ít nhất 3 nhận xét dựa trên số liệu.
- [ ] Có đề xuất CRM, rủi ro, giới hạn dữ liệu và điều kiện áp dụng.
- [ ] Có README, mã nguồn, kiểm thử, báo cáo, slide/demo và phân công đóng góp.
- [ ] Cả 3 người hiểu cách tính KPI và giải thích được phần mình thực hiện.

Quy mô và hiệu năng phải được báo cáo trung thực. Số dòng lớn hơn một triệu không tự chứng minh hệ thống phân tán cần thiết. Nếu bổ sung dữ liệu tăng tải mô phỏng, tách khỏi kết quả kinh doanh trên dữ liệu thật và ghi rõ cách tạo.

## 10. Tài liệu tham khảo kỹ thuật

- PySpark: <https://spark.apache.org/docs/latest/api/python/getting_started/install.html>.
- K-Means: <https://scikit-learn.org/stable/modules/generated/sklearn.cluster.KMeans.html>.
- Silhouette: <https://scikit-learn.org/stable/modules/generated/sklearn.metrics.silhouette_score.html>.
- Streamlit: <https://docs.streamlit.io/get-started>.

Các chi tiết chưa được xác minh từ file thực tế phải được cập nhật trong giai đoạn khảo sát, không trình bày như kết quả đã đo.

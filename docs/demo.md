# Kịch bản demo

## Chuẩn bị trước khi trình bày

1. Kiểm tra `data/processed/customer_rfm.parquet` và `data/curated/customer_segments.parquet` đã tồn tại.
2. Chạy `python -m pytest -q` và lưu kết quả terminal.
3. Chạy `streamlit run app/app.py` rồi mở địa chỉ local do Streamlit cung cấp.
4. Giữ sẵn `reports/model_comparison.csv` và `reports/segment_profiles.csv` để đối chiếu khi được hỏi.

## Luồng trình bày 8 phút

1. **Bài toán và phạm vi, 45 giây.** Nêu ba câu hỏi kinh doanh và cảnh báo kết quả chỉ đại diện cho 22,81% dòng nguồn có thể gắn khách.
2. **Dữ liệu và RFM, 75 giây.** Trình bày 600.784 dòng sạch, 234.359 khách, ngày chốt 22/11/2020 và công thức R/F/M.
3. **Pipeline, 60 giây.** Đi theo sơ đồ từ CSV đến Parquet, RFM, bốn phương pháp, artifact và dashboard.
4. **So sánh mô hình, 90 giây.** Chọn tab so sánh, giải thích mẫu Silhouette 5.000 khách và thời gian fit. Chỉ ra BIRCH có Silhouette cao nhưng cụm nhỏ nhất chỉ 0,095%.
5. **Hồ sơ K-Means, 90 giây.** Chọn K-Means và lần lượt xem S1, S2, S3. Đối chiếu quy mô, median R/F/M, tỷ trọng M và tỷ lệ mua lặp.
6. **Giả thuyết CRM, 90 giây.** Trình bày thử nghiệm duy trì S1, tái tương tác S2 và onboarding đơn thứ hai cho S3. Nhấn mạnh cần nhóm đối chứng.
7. **Giới hạn và kết luận, 30 giây.** Nhắc coverage, đồng tiền chưa xác minh, Silhouette không phải hiệu quả kinh doanh và phân khúc không chứng minh nhân quả.

## Câu hỏi thường gặp

- **Vì sao không chọn BIRCH?** Cấu hình được chọn theo fallback có 97,42% khách trong một cụm và cụm nhỏ nhất 0,095%, nên khó dùng cho CRM dù Silhouette cao.
- **Vì sao dùng log1p?** RFM lệch phải và có giá trị lớn; log1p giảm ảnh hưởng cực trị trước khi chuẩn hóa mà vẫn giữ toàn bộ khách.
- **Tỷ lệ mua lặp có phải retention không?** Không. Đây là tỷ lệ F >= 2 trong khoảng quan sát, không theo dõi một cohort sang kỳ tương lai.
- **K-Means có phải mô hình tốt nhất tuyệt đối không?** Không. K-Means là lựa chọn vận hành mặc định trong thí nghiệm này vì cụm cân bằng, chạy nhanh và dễ diễn giải. Baseline vẫn phù hợp khi cần quy tắc minh bạch.
- **Có thể gửi chiến dịch ngay không?** Chỉ nên dùng phân khúc để tạo giả thuyết, sau đó kiểm tra quyền liên hệ và chạy thử nghiệm có nhóm đối chứng.

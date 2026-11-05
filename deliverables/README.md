# Bộ sản phẩm nộp

| File | Nội dung | Kiểm tra |
|---|---|---|
| `Customer_Segmentation_Report.docx` | Báo cáo Word 11 trang, bảng và hình kết quả | Xuất bằng Microsoft Word và kiểm tra đủ 11 trang |
| `Customer_Segmentation_Report.pdf` | Bản PDF của cùng báo cáo | Render 11 trang bằng Poppler và kiểm tra từng trang |
| `Customer_Segmentation_Presentation.pptx` | Slide 10 trang, 3 chart và 4 table native | Finalizer đạt 0 finding; mở bằng PowerPoint thành công |

## SHA-256

```text
144798BB7FC7ADD98EEB1F585588038E1EE35B3EE15F0FA9BEB2BCDFED042DDA  Customer_Segmentation_Report.docx
4980F7BA50B4D4FD5EBEDA7D54ED8E04188EA2A68D6B047BCE615176D5DE48F5  Customer_Segmentation_Report.pdf
A4AC1E7C6595D2ADB9D5543CE85EF552F250011F6B9431304BBC253CDAF88DE3  Customer_Segmentation_Presentation.pptx
```

`scripts/build_report.py` tạo lại DOCX và các hình nguồn. `scripts/build_presentation.mjs` tạo lại PPTX trong Codex primary runtime. PDF được xuất từ DOCX bằng Microsoft Word để giữ đúng bố cục.

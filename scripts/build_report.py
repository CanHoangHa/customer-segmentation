"""Build the final Vietnamese report and its supporting figures."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
DELIVERABLES = ROOT / "deliverables"
FIGURES = DELIVERABLES / "figures"
OUTPUT = DELIVERABLES / "Customer_Segmentation_Report.docx"

NAVY = "17324D"
BLUE = "2C6EAA"
TEAL = "2A9D8F"
GOLD = "E9C46A"
RED = "C75B5B"
LIGHT = "EAF1F7"
MID = "D4E2EE"
TEXT = "243447"
WHITE = "FFFFFF"


def load_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def load_csv(name: str) -> list[dict[str, str]]:
    with (REPORTS / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: str, radius: int = 18) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def save_coverage_figure(cleaning: dict) -> Path:
    path = FIGURES / "coverage.png"
    width, height = 1500, 720
    image = Image.new("RGB", (width, height), "#F7FAFC")
    draw = ImageDraw.Draw(image)
    draw.text((70, 45), "Phạm vi dữ liệu sau kiểm tra chất lượng", fill="#17324D", font=font(38, True))
    raw = cleaning["raw_rows"]
    clean = cleaning["clean_rows"]
    values = [
        ("Dòng nguồn", raw, "#2C6EAA"),
        ("Dòng hợp lệ", clean, "#2A9D8F"),
        ("Thiếu customer_id", cleaning["rows_by_primary_reason"]["missing_customer_id"], "#C75B5B"),
        ("Ngoài phạm vi ngày", cleaning["rows_by_primary_reason"]["date_outside_scope"], "#E9C46A"),
        ("Giá không dương", cleaning["rows_by_primary_reason"]["nonpositive_price"], "#8D99AE"),
    ]
    y0, max_w = 160, 820
    for index, (label, value, color) in enumerate(values):
        y = y0 + index * 96
        draw.text((80, y + 10), label, fill="#243447", font=font(25, index < 2))
        bar_x = 410
        bar_w = max(5, int(max_w * value / raw))
        rounded_rect(draw, (bar_x, y, bar_x + bar_w, y + 54), color, 12)
        draw.text((bar_x + bar_w + 20, y + 8), f"{value:,}".replace(",", "."), fill="#243447", font=font(25, True))
    coverage = clean / raw * 100
    rounded_rect(draw, (1030, 520, 1430, 650), "#17324D", 22)
    draw.text((1080, 542), f"{coverage:.2f}%".replace(".", ","), fill="white", font=font(46, True))
    draw.text((1080, 600), "dòng được giữ", fill="#D4E2EE", font=font(23))
    image.save(path)
    return path


def save_model_figure(rows: list[dict[str, str]]) -> Path:
    path = FIGURES / "model_comparison.png"
    selected = [row for row in rows if row["selected"].lower() == "true"]
    order = ["rfm_threshold", "kmeans", "gmm", "birch"]
    selected.sort(key=lambda row: order.index(row["method"]))
    labels = ["Ngưỡng RFM", "K-Means", "GMM", "BIRCH"]
    colors = ["#8D99AE", "#2A9D8F", "#2C6EAA", "#E9C46A"]
    width, height = 1500, 820
    image = Image.new("RGB", (width, height), "#F7FAFC")
    draw = ImageDraw.Draw(image)
    draw.text((70, 45), "So sánh cấu hình được chọn", fill="#17324D", font=font(38, True))
    draw.text((70, 100), "Silhouette trên cùng mẫu 5.000 khách", fill="#52677A", font=font(23))
    chart_left, chart_top, chart_width, chart_height = 140, 190, 1160, 460
    draw.line((chart_left, chart_top + chart_height, chart_left + chart_width, chart_top + chart_height), fill="#7B8C9A", width=3)
    for tick in range(6):
        value = tick / 10
        y = chart_top + chart_height - int(value / 0.5 * chart_height)
        draw.line((chart_left, y, chart_left + chart_width, y), fill="#D4E2EE", width=2)
        draw.text((75, y - 14), f"{value:.1f}".replace(".", ","), fill="#52677A", font=font(20))
    gap = chart_width / len(selected)
    for index, row in enumerate(selected):
        value = float(row["silhouette"])
        bar_w = 150
        x = int(chart_left + gap * index + (gap - bar_w) / 2)
        y = chart_top + chart_height - int(value / 0.5 * chart_height)
        rounded_rect(draw, (x, y, x + bar_w, chart_top + chart_height), colors[index], 16)
        draw.text((x + 20, y - 42), f"{value:.3f}".replace(".", ","), fill="#17324D", font=font(25, True))
        draw.text((x - 10, chart_top + chart_height + 22), labels[index], fill="#243447", font=font(22, True))
    draw.text((70, 735), "BIRCH có Silhouette cao nhất nhưng cụm nhỏ nhất chỉ chiếm 0,095% số khách.", fill="#C75B5B", font=font(25, True))
    image.save(path)
    return path


def save_kmeans_figure(profiles: list[dict[str, str]]) -> Path:
    path = FIGURES / "kmeans_profiles.png"
    rows = [row for row in profiles if row["method"] == "kmeans"]
    rows.sort(key=lambda row: row["segment_id"])
    width, height = 1500, 820
    image = Image.new("RGB", (width, height), "#F7FAFC")
    draw = ImageDraw.Draw(image)
    draw.text((70, 45), "Hồ sơ ba nhóm K-Means", fill="#17324D", font=font(38, True))
    colors = ["#2A9D8F", "#2C6EAA", "#E9C46A"]
    for index, row in enumerate(rows):
        x0 = 70 + index * 475
        rounded_rect(draw, (x0, 145, x0 + 420, 710), "#FFFFFF", 24)
        draw.rounded_rectangle((x0, 145, x0 + 420, 250), radius=24, fill=colors[index])
        draw.rectangle((x0, 220, x0 + 420, 250), fill=colors[index])
        draw.text((x0 + 34, 172), row["segment_id"], fill="white" if index < 2 else "#17324D", font=font(42, True))
        metrics = [
            ("Số khách", f"{int(row['customers']):,}".replace(",", ".")),
            ("Tỷ trọng khách", f"{float(row['customer_pct']):.2f}%".replace(".", ",")),
            ("Trung vị R", f"{float(row['median_recency_days']):.0f} ngày"),
            ("Trung vị F", f"{float(row['median_frequency_orders']):.0f} đơn"),
            ("Trung vị M", f"{float(row['median_monetary_value']):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
            ("Tỷ trọng M", f"{float(row['monetary_share_pct']):.2f}%".replace(".", ",")),
            ("Mua lặp", f"{float(row['repeat_customer_pct']):.2f}%".replace(".", ",")),
        ]
        for row_index, (label, value) in enumerate(metrics):
            y = 285 + row_index * 58
            draw.text((x0 + 32, y), label, fill="#52677A", font=font(20))
            box = draw.textbbox((0, 0), value, font=font(23, True))
            draw.text((x0 + 388 - (box[2] - box[0]), y - 2), value, fill="#243447", font=font(23, True))
    image.save(path)
    return path


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=100, start=110, bottom=100, end=110) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for margin, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{margin}"))
        if node is None:
            node = OxmlElement(f"w:{margin}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_cant_split(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    cant_split = OxmlElement("w:cantSplit")
    tr_pr.append(cant_split)


def add_page_number(paragraph) -> None:
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = paragraph.add_run("Trang ")
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr_text = OxmlElement("w:instrText")
    instr_text.set(qn("xml:space"), "preserve")
    instr_text.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run._r.append(fld_char1)
    run._r.append(instr_text)
    run._r.append(fld_char2)


def add_table(doc: Document, headers: list[str], rows: list[list[str]], widths: list[float] | None = None) -> None:
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    header = table.rows[0]
    set_repeat_table_header(header)
    set_cant_split(header)
    for index, text in enumerate(headers):
        cell = header.cells[index]
        cell.text = text
        set_cell_shading(cell, NAVY)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        set_cell_margins(cell)
        for run in cell.paragraphs[0].runs:
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            run.font.size = Pt(9)
    for row_index, values in enumerate(rows):
        added_row = table.add_row()
        set_cant_split(added_row)
        cells = added_row.cells
        for index, text in enumerate(values):
            cells[index].text = str(text)
            cells[index].vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            set_cell_margins(cells[index])
            if row_index % 2 == 1:
                set_cell_shading(cells[index], "F3F7FA")
            for paragraph in cells[index].paragraphs:
                for run in paragraph.runs:
                    run.font.size = Pt(8.5)
    if widths:
        for row in table.rows:
            for index, width in enumerate(widths):
                row.cells[index].width = Inches(width)
    doc.add_paragraph()


def add_bullets(doc: Document, items: list[str]) -> None:
    for item in items:
        paragraph = doc.add_paragraph(style="List Bullet")
        paragraph.add_run(item)


def add_figure(doc: Document, image_path: Path, caption: str, width: float = 6.7) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(image_path), width=Inches(width))
    caption_paragraph = doc.add_paragraph(caption, style="Caption")
    caption_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER


def add_callout(doc: Document, title: str, body: str, color: str = LIGHT) -> None:
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = table.cell(0, 0)
    set_cell_shading(cell, color)
    set_cell_margins(cell, top=170, start=180, bottom=170, end=180)
    paragraph = cell.paragraphs[0]
    run = paragraph.add_run(title + "\n")
    run.bold = True
    run.font.color.rgb = RGBColor.from_string(NAVY)
    paragraph.add_run(body)
    doc.add_paragraph()


def configure_styles(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor.from_string(TEXT)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.15
    for name, size, color in (("Title", 30, NAVY), ("Heading 1", 19, NAVY), ("Heading 2", 14, BLUE), ("Heading 3", 11.5, TEAL)):
        style = doc.styles[name]
        style.font.name = "Arial"
        style._element.rPr.rFonts.set(qn("w:ascii"), "Arial")
        style._element.rPr.rFonts.set(qn("w:hAnsi"), "Arial")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(12)
        style.paragraph_format.space_after = Pt(6)
        style.paragraph_format.keep_with_next = True
    doc.styles["Caption"].font.name = "Arial"
    doc.styles["Caption"].font.size = Pt(9)
    doc.styles["Caption"].font.italic = True
    doc.styles["Caption"].font.color.rgb = RGBColor.from_string("52677A")


def configure_sections(doc: Document) -> None:
    for section in doc.sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(1.8)
        section.left_margin = Cm(2.3)
        section.right_margin = Cm(2.0)
        section.header_distance = Cm(0.8)
        section.footer_distance = Cm(0.8)
        header = section.header.paragraphs[0]
        header.text = "CO4033  |  Phân khúc khách hàng theo hành vi mua sắm"
        header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        for run in header.runs:
            run.font.name = "Arial"
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor.from_string("6B7C8C")
        footer = section.footer.paragraphs[0]
        add_page_number(footer)
        for run in footer.runs:
            run.font.name = "Arial"
            run.font.size = Pt(8)
            run.font.color.rgb = RGBColor.from_string("6B7C8C")


def build_report() -> Path:
    DELIVERABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    cleaning = load_json("cleaning_summary.json")
    rfm = load_json("rfm_summary.json")
    metadata = load_json("run_metadata.json")
    selections = load_json("model_selection.json")
    comparison = load_csv("model_comparison.csv")
    profiles = load_csv("segment_profiles.csv")
    coverage_figure = save_coverage_figure(cleaning)
    model_figure = save_model_figure(comparison)
    kmeans_figure = save_kmeans_figure(profiles)

    doc = Document()
    configure_styles(doc)
    section = doc.sections[0]
    section.top_margin = Cm(2.2)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.1)

    # Cover
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(36)
    r = p.add_run("BÀI TẬP LỚN CO4033")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor.from_string(BLUE)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(70)
    r = p.add_run("PHÂN KHÚC KHÁCH HÀNG\nTHEO HÀNH VI MUA SẮM")
    r.bold = True
    r.font.name = "Arial"
    r.font.size = Pt(29)
    r.font.color.rgb = RGBColor.from_string(NAVY)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("RFM, K-Means, Gaussian Mixture và BIRCH\ntrên dữ liệu giao dịch cửa hàng điện tử")
    r.font.name = "Arial"
    r.font.size = Pt(15)
    r.font.color.rgb = RGBColor.from_string("52677A")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(95)
    r = p.add_run("Đề tài 04  |  Báo cáo thực nghiệm")
    r.bold = True
    r.font.size = Pt(12)
    r.font.color.rgb = RGBColor.from_string(TEAL)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Ngày hoàn thiện 06/11/2026")
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor.from_string("52677A")
    doc.add_page_break()

    doc.add_heading("Tóm tắt", level=1)
    doc.add_paragraph(
        "Báo cáo xây dựng một pipeline tái lập để phân khúc khách hàng từ dữ liệu giao dịch thực tế năm 2020. "
        "Pipeline làm sạch dữ liệu, tổng hợp RFM, so sánh baseline theo ngưỡng với K-Means, Gaussian Mixture và BIRCH, "
        "sau đó cung cấp artifact cho dashboard Streamlit."
    )
    add_callout(
        doc,
        "Kết quả chính",
        "Từ 2.633.521 dòng nguồn, pipeline giữ 600.784 dòng hợp lệ và tạo RFM cho 234.359 khách. "
        "K-Means k = 3 được đề xuất làm góc nhìn vận hành mặc định vì ba nhóm đủ lớn, Silhouette đạt 0,3470 và "
        "trung vị thời gian fit là 0,774 giây. BIRCH đạt Silhouette 0,4862 nhưng cụm nhỏ nhất chỉ chiếm 0,095%, "
        "nên không đạt tiêu chí 1% đã chốt.",
    )
    doc.add_paragraph(
        "Kết quả chỉ đại diện cho phần giao dịch có customer_id và vượt qua quy tắc chất lượng. Mọi đề xuất CRM trong "
        "báo cáo là giả thuyết cần kiểm tra bằng thử nghiệm có nhóm đối chứng; phân khúc không chứng minh tác động nhân quả."
    )

    doc.add_heading("Mục lục", level=1)
    toc_items = [
        "1  Bài toán và phạm vi",
        "2  Dữ liệu và kiểm soát chất lượng",
        "3  Phương pháp",
        "4  Thiết kế thực nghiệm",
        "5  Kết quả",
        "6  Dashboard và giả thuyết CRM",
        "7  Kiểm thử và khả năng tái lập",
        "8  Giới hạn và kết luận",
        "Phụ lục A  Artifact bàn giao",
        "Phụ lục B  Phân công đóng góp",
        "Tài liệu tham khảo",
    ]
    add_bullets(doc, toc_items)
    doc.add_page_break()

    doc.add_heading("1  Bài toán và phạm vi", level=1)
    doc.add_heading("1.1  Câu hỏi kinh doanh", level=2)
    add_bullets(
        doc,
        [
            "Khách hàng khác nhau như thế nào về thời gian mua gần nhất, số lần mua và giá trị mua?",
            "Nhóm khách nào có giá trị mua cao nhưng đã lâu chưa quay lại và nên được ưu tiên trong một thử nghiệm tái tương tác?",
            "Baseline RFM, K-Means, GMM và BIRCH khác nhau thế nào về mức phân tách, quy mô nhóm, thời gian fit và khả năng giải thích?",
        ],
    )
    doc.add_heading("1.2  Người dùng và sản phẩm", level=2)
    doc.add_paragraph(
        "Người dùng chính là nhân viên CRM hoặc quản lý marketing của cửa hàng điện tử. Sản phẩm gồm pipeline dữ liệu, "
        "pipeline phân khúc, bảng kết quả, dashboard Streamlit, báo cáo và slide. Dashboard không huấn luyện lại mô hình; "
        "nó đọc nhãn và KPI đã được pipeline tạo và kiểm tra."
    )
    doc.add_heading("1.3  Định nghĩa KPI", level=2)
    add_table(
        doc,
        ["KPI", "Định nghĩa trong dự án", "Điều không được suy diễn"],
        [
            ["Recency", "Số ngày từ lần mua hợp lệ gần nhất đến 22/11/2020", "Không phải xác suất rời bỏ"],
            ["Frequency", "Số order_id riêng biệt của khách trong kỳ", "Không đếm số dòng sản phẩm"],
            ["Monetary", "Tổng price trên dòng hợp lệ", "Không phải lợi nhuận hoặc CLV"],
            ["Khách mua lặp", "Khách có F >= 2 chia tổng khách RFM", "Không phải retention của cohort tương lai"],
            ["Silhouette", "Độ tách cụm trong không gian đã chuẩn hóa", "Không phải độ chính xác hoặc hiệu quả CRM"],
        ],
        [1.2, 3.1, 2.2],
    )

    doc.add_heading("2  Dữ liệu và kiểm soát chất lượng", level=1)
    doc.add_heading("2.1  Nguồn và phiên bản", level=2)
    doc.add_paragraph(
        "Dữ liệu eCommerce Purchase History from Electronics Store do REES46/Open CDP công bố. Nhóm dùng file kz.csv "
        "từ Kaggle Version 2, gồm các trường thời gian, đơn hàng, sản phẩm, ngành hàng, thương hiệu, giá và mã khách ẩn danh. "
        "File gốc không được commit vào Git."
    )
    add_figure(doc, coverage_figure, "Hình 1  Phạm vi dữ liệu sau kiểm tra chất lượng")
    doc.add_heading("2.2  Quy tắc làm sạch", level=2)
    add_bullets(
        doc,
        [
            "Giữ giao dịch năm 2020 có event_time, order_id, user_id và price hợp lệ; price phải dương.",
            "Căn dòng 6 trường theo cấu trúc nguồn đã quan sát; 37.961 dòng sửa cấu trúc được chấp nhận.",
            "Không tự điền customer_id, không thay giá thiếu bằng 0 và không xóa dòng lặp khi nguồn không có khóa dòng duy nhất.",
            "Tách dòng không hợp lệ kèm lý do để đo ảnh hưởng của từng quy tắc.",
        ],
    )
    add_table(
        doc,
        ["Chỉ số", "Giá trị"],
        [
            ["Dòng nguồn", f"{cleaning['raw_rows']:,}".replace(",", ".")],
            ["Dòng hợp lệ", f"{cleaning['clean_rows']:,}".replace(",", ".")],
            ["Dòng bị tách", f"{cleaning['quarantine_rows']:,}".replace(",", ".")],
            ["Khách hàng RFM", f"{rfm['customers']:,}".replace(",", ".")],
            ["Đơn hàng", f"{rfm['orders']:,}".replace(",", ".")],
            ["Khách mua lặp", f"{rfm['repeat_customers']:,}".replace(",", ".") + f" ({rfm['repeat_customer_pct']:.4f}%)"],
            ["Tổng M", "118.372.961,62 đơn vị giá theo nguồn"],
        ],
        [3.2, 3.0],
    )
    add_callout(
        doc,
        "Giới hạn độ bao phủ",
        "600.784 dòng hợp lệ chiếm 22,81% số dòng nguồn. Nguyên nhân lớn nhất là thiếu customer_id. "
        "Kết quả phân khúc không đại diện cho các giao dịch không thể gắn với khách.",
        "FCE8E8",
    )

    doc.add_heading("3  Phương pháp", level=1)
    doc.add_heading("3.1  RFM và baseline", level=2)
    doc.add_paragraph(
        "Ngày chốt được cố định ở 22/11/2020, một ngày sau giao dịch hợp lệ cuối cùng. Baseline dùng percentile rank; "
        "điểm R đảo chiều còn F và M cùng chiều. Cách xếp hạng trung bình giữ các khách có F bằng nhau trong cùng ngưỡng. "
        "Năm quy tắc có thứ tự ưu tiên, loại trừ lẫn nhau và phủ 100% khách."
    )
    add_table(
        doc,
        ["Nhóm baseline", "Số khách", "Tỷ trọng", "Median R/F/M", "Tỷ trọng M"],
        [
            [row["segment_name"], f"{int(row['customers']):,}".replace(",", "."), f"{float(row['customer_pct']):.2f}%".replace(".", ","), f"{float(row['median_recency_days']):.0f} / {float(row['median_frequency_orders']):.0f} / {float(row['median_monetary_value']):.2f}".replace(".", ","), f"{float(row['monetary_share_pct']):.2f}%".replace(".", ",")]
            for row in profiles if row["method"] == "rfm_threshold"
        ],
        [2.0, 0.8, 0.8, 1.2, 0.8],
    )
    doc.add_heading("3.2  Chuẩn bị đặc trưng", level=2)
    doc.add_paragraph(
        "Ma trận mô hình dùng thứ tự R, F, M. Pipeline áp dụng log1p cho ba đặc trưng không âm rồi dùng StandardScaler. "
        "RFM gốc được giữ lại để tính KPI và giải thích. Tất cả phương pháp học máy dùng cùng scaler, cùng cohort và cùng thứ tự khách."
    )
    add_table(
        doc,
        ["Đặc trưng", "Giá trị nhỏ nhất", "Giá trị lớn nhất", "Trung bình sau log1p", "Độ lệch dùng chuẩn hóa"],
        [
            [name, f"{metadata['features']['raw_min'][name]:,.2f}", f"{metadata['features']['raw_max'][name]:,.2f}", f"{metadata['features']['logged_mean'][name]:.4f}", f"{metadata['features']['logged_scale'][name]:.4f}"]
            for name in metadata["features"]["feature_order"]
        ],
        [1.2, 1.0, 1.0, 1.25, 1.25],
    )
    doc.add_heading("3.3  Thuật toán", level=2)
    add_bullets(
        doc,
        [
            "K-Means tối thiểu hóa tổng bình phương khoảng cách đến tâm cụm. Grid thử k từ 3 đến 6, n_init = 20, seed = 42.",
            "Gaussian Mixture dùng covariance_type = full, n_init = 3 và gán nhãn theo xác suất hậu nghiệm lớn nhất.",
            "BIRCH gom dữ liệu thành subcluster trước khi tạo số cụm cuối; grid thử threshold 0,3, 0,5 và 0,7 với k từ 3 đến 6.",
        ],
    )

    doc.add_heading("4  Thiết kế thực nghiệm", level=1)
    doc.add_heading("4.1  Nguyên tắc so sánh", level=2)
    add_bullets(
        doc,
        [
            "Huấn luyện và gán nhãn trên toàn bộ 234.359 khách.",
            "Tính Silhouette trên cùng mẫu cố định 5.000 khách, seed 42; hash mẫu được lưu trong run_metadata.json.",
            "Làm nóng một lần, đo fit_predict ba lần và báo cáo trung vị; thời gian Silhouette không nằm trong thời gian fit.",
            "Chỉ chọn cấu hình có cụm nhỏ nhất từ 1% trở lên. Nếu một phương pháp không có cấu hình đạt ngưỡng, dùng fallback Silhouette hợp lệ cao nhất và cảnh báo.",
        ],
    )
    doc.add_heading("4.2  Môi trường", level=2)
    env = metadata["environment"]
    add_table(
        doc,
        ["Thành phần", "Giá trị"],
        [
            ["Hệ điều hành", env["platform"]],
            ["CPU logic", str(env["cpu_count"])],
            ["Python", env["python"]],
            ["NumPy", env["numpy"]],
            ["Pandas", env["pandas"]],
            ["PyArrow", env["pyarrow"]],
            ["scikit-learn", env["scikit_learn"]],
        ],
        [2.2, 3.8],
    )

    doc.add_heading("5  Kết quả", level=1)
    add_figure(doc, model_figure, "Hình 2  Silhouette của các cấu hình được chọn")
    selected_rows = [row for row in comparison if row["selected"].lower() == "true"]
    selected_rows.sort(key=lambda row: ["rfm_threshold", "kmeans", "gmm", "birch"].index(row["method"]))
    method_names = {"rfm_threshold": "Ngưỡng RFM", "kmeans": "K-Means", "gmm": "GMM", "birch": "BIRCH"}
    add_table(
        doc,
        ["Phương pháp", "Cấu hình", "Cụm", "Silhouette", "Fit trung vị", "Cụm nhỏ nhất", "Đủ điều kiện"],
        [
            [
                method_names[row["method"]],
                row["config_id"],
                row["actual_clusters"],
                f"{float(row['silhouette']):.4f}".replace(".", ","),
                "Không áp dụng" if row["method"] == "rfm_threshold" else f"{float(row['median_fit_seconds']):.3f} s".replace(".", ","),
                f"{float(row['smallest_segment_pct']) * 100:.3f}%".replace(".", ","),
                "Có" if row["eligible_for_selection"].lower() == "true" else "Không, fallback",
            ]
            for row in selected_rows
        ],
        [1.0, 1.25, 0.45, 0.75, 0.85, 0.85, 1.0],
    )
    doc.add_heading("5.1  Quyết định mô hình", level=2)
    doc.add_paragraph(
        "K-Means k = 3 là lựa chọn mặc định cho dashboard và thảo luận CRM. Mô hình đạt Silhouette 0,3470, có nhóm nhỏ nhất "
        "21,47% và fit nhanh hơn GMM cùng BIRCH được chọn. Baseline RFM được giữ như góc nhìn minh bạch theo quy tắc. "
        "BIRCH không được khuyến nghị làm phân khúc chính vì cấu hình fallback dồn 97,42% khách vào S1 và chỉ có 223 khách ở S3."
    )
    add_figure(doc, kmeans_figure, "Hình 3  Hồ sơ ba nhóm K-Means trên toàn bộ cohort")
    doc.add_heading("5.2  Đọc hồ sơ K-Means", level=2)
    add_bullets(
        doc,
        [
            "S1 gồm 50.318 khách, chiếm 21,47% số khách nhưng 59,69% tổng M. Median R/F/M là 78 ngày, 3 đơn và 909,48.",
            "S2 gồm 121.895 khách, chiếm 52,01% số khách và 27,41% tổng M. Median R/F/M là 119 ngày, 1 đơn và 150,44.",
            "S3 gồm 62.146 khách, chiếm 26,52% số khách và 12,90% tổng M. Median R/F/M là 19 ngày, 1 đơn và 104,14.",
        ],
    )

    doc.add_heading("6  Dashboard và giả thuyết CRM", level=1)
    doc.add_heading("6.1  Thiết kế dashboard", level=2)
    doc.add_paragraph(
        "Dashboard có bốn tab: phạm vi dữ liệu, hồ sơ phân khúc, so sánh phương pháp và giả thuyết CRM. Bộ lọc phương pháp "
        "và phân khúc chỉ lọc artifact đã tạo; nó không làm thay đổi ngày chốt hoặc huấn luyện lại mô hình. customer_id không "
        "xuất hiện trong biểu đồ và không có chức năng tải raw data mặc định."
    )
    doc.add_heading("6.2  Danh mục thử nghiệm đề xuất", level=2)
    add_table(
        doc,
        ["Đối tượng", "Quan sát", "Giả thuyết thử nghiệm", "KPI chính", "Rủi ro và điều kiện dừng"],
        [
            ["K-Means S1", "21,47% khách; 59,69% M; 99,95% mua lặp", "Quyền lợi thành viên hoặc gợi ý mua bổ sung", "Đơn mới, thời gian đến đơn, M tăng thêm", "Không gửi quá tần suất; dừng nếu phản hồi tiêu cực tăng"],
            ["K-Means S2", "52,01% khách; median R = 119; F = 1", "Tái tương tác chi phí thấp với nhóm đối chứng", "Tỷ lệ quay lại, chi phí/khách quay lại", "Dừng nếu chi phí tăng mà không hơn đối chứng"],
            ["K-Means S3", "26,52% khách; median R = 19; F = 1", "Onboarding sau mua để thúc đẩy đơn thứ hai", "Đơn thứ hai trong 30/60 ngày", "Kiểm soát quyền liên hệ và tỷ lệ từ chối"],
            ["Baseline giá trị cao cần tái tương tác", "17,40% khách; median R = 135; M = 465,25", "Win-back có giới hạn ưu đãi", "Lợi nhuận tăng thêm nếu có dữ liệu chi phí", "Không gọi là churn khi chưa có nhãn tương lai"],
        ],
        [0.85, 1.35, 1.7, 1.3, 1.55],
    )
    add_callout(
        doc,
        "Nguyên tắc diễn giải",
        "Những quan sát trên mô tả hành vi trong khoảng dữ liệu. Chúng không chứng minh khách sẽ phản hồi hoặc chiến dịch sẽ tạo doanh thu tăng thêm.",
        "FFF4D6",
    )

    doc.add_heading("7  Kiểm thử và khả năng tái lập", level=1)
    doc.add_heading("7.1  Kiểm thử", level=2)
    doc.add_paragraph(
        "Bộ kiểm thử không phụ thuộc Spark gồm 21 test và đã chạy qua sau khi merge dashboard. Test bao phủ hợp đồng schema, "
        "tie trong percentile rank, precedence baseline, cấu hình model, trường hợp metric không áp dụng, remap nhãn, ghi artifact, "
        "loader dashboard và việc không rò customer_id vào biểu đồ. Ba test PySpark vẫn cần môi trường Python 3.11 và Java 17 như README."
    )
    doc.add_heading("7.2  Lệnh chạy", level=2)
    add_table(
        doc,
        ["Mục tiêu", "Lệnh"],
        [
            ["Cài dependencies", "python -m pip install -r requirements.txt"],
            ["Làm sạch và RFM", "python scripts/run_pipeline.py"],
            ["Runner tương thích Windows", "python scripts/run_portable_rfm.py"],
            ["Phân khúc", "python scripts/run_segmentation.py --expected-rows 234359"],
            ["Kiểm thử", "python -m pytest -q"],
            ["Dashboard", "streamlit run app/app.py"],
        ],
        [2.0, 4.2],
    )
    doc.add_heading("7.3  Đảm bảo tái lập", level=2)
    add_bullets(
        doc,
        [
            "Sắp xếp customer_id trước khi lấy mẫu và ghi file.",
            "Dùng seed 42 và lưu hash mẫu Silhouette.",
            "Lưu input SHA-256, phiên bản thư viện, cấu hình model và kết quả từng lần đo.",
            "Đối chiếu số khách, tổng M và khách mua lặp sau mỗi bước group-by.",
        ],
    )
    doc.add_heading("7.4  Công cụ AI và kiểm chứng", level=2)
    doc.add_paragraph(
        "Nhóm sử dụng Codex để hỗ trợ lập kế hoạch, viết mã, tạo kiểm thử và chuẩn bị tài liệu. Các số liệu được sinh từ "
        "pipeline trên dữ liệu thật và đối chiếu bằng artifact đã commit. Nhóm chịu trách nhiệm đọc mã, chạy lại lệnh, kiểm tra "
        "kết quả và trình bày đúng giới hạn."
    )

    doc.add_heading("8  Giới hạn và kết luận", level=1)
    doc.add_heading("8.1  Giới hạn", level=2)
    add_bullets(
        doc,
        [
            "Coverage theo dòng chỉ đạt 22,81% do phần lớn dòng thiếu customer_id.",
            "M là đơn vị giá theo nguồn; đồng tiền, lợi nhuận và chi phí chiến dịch chưa có trong dataset.",
            "Silhouette dùng mẫu 5.000 khách và chỉ phản ánh cấu trúc trong không gian RFM đã biến đổi.",
            "Khoảng dữ liệu kết thúc năm 2020; cần đánh giá drift trước khi áp dụng cho dữ liệu hiện tại.",
            "Không có nhãn churn hoặc kết quả chiến dịch, nên mọi hành động chỉ là giả thuyết cần thử nghiệm.",
        ],
    )
    doc.add_heading("8.2  Kết luận", level=2)
    doc.add_paragraph(
        "Dự án đã hoàn thành pipeline từ dữ liệu giao dịch đến RFM, bốn phương pháp phân khúc, benchmark, artifact và dashboard. "
        "K-Means k = 3 tạo ba nhóm đủ lớn và dễ dùng cho thảo luận CRM, trong khi baseline cung cấp quy tắc minh bạch cho các "
        "tệp chiến dịch cụ thể. BIRCH cho thấy vì sao không nên chọn mô hình chỉ dựa trên một chỉ số: Silhouette cao đi kèm phân bố "
        "cụm không phù hợp với vận hành. Bước tiếp theo hợp lý là chạy A/B test có nhóm đối chứng và cập nhật phân khúc trên dữ liệu mới."
    )

    doc.add_page_break()
    doc.add_heading("Phụ lục A  Artifact bàn giao", level=1)
    add_table(
        doc,
        ["Artifact", "Vai trò"],
        [
            ["data/processed/customer_rfm.parquet", "Một dòng cho mỗi khách và RFM gốc"],
            ["data/curated/customer_segments.parquet", "Nhãn của bốn phương pháp và RFM gốc"],
            ["reports/model_comparison.csv", "Kết quả 21 cấu hình và lựa chọn"],
            ["reports/segment_profiles.csv", "Quy mô, median RFM, tỷ trọng M và mua lặp"],
            ["reports/model_selection.json", "Cấu hình được chọn và ánh xạ nhãn ổn định"],
            ["reports/run_metadata.json", "Seed, sample hash, môi trường và metadata feature"],
            ["app/app.py", "Dashboard Streamlit"],
        ],
        [3.0, 3.2],
    )
    doc.add_heading("Phụ lục B  Phân công đóng góp", level=1)
    add_table(
        doc,
        ["Vai trò", "Phạm vi"],
        [
            ["Người 1", "Khảo sát dữ liệu, quy tắc chất lượng, PySpark, Parquet và RFM"],
            ["Người 2", "Hợp đồng dữ liệu, baseline, K-Means, GMM, BIRCH, benchmark và profile"],
            ["Người 3", "Dashboard, biểu đồ, diễn giải CRM, tài liệu trình bày và demo"],
            ["Cả nhóm", "Đối chiếu KPI, review giới hạn, chạy lại README và tập trình bày"],
        ],
        [1.5, 4.7],
    )
    doc.add_heading("Tài liệu tham khảo", level=1)
    refs = [
        "REES46. Ecommerce behavior data. https://data.rees46.com/",
        "Kaggle. eCommerce purchase history from electronics store. https://www.kaggle.com/datasets/mkechinov/ecommerce-purchase-history-from-electronics-store",
        "Apache Spark. PySpark documentation. https://spark.apache.org/docs/latest/api/python/",
        "scikit-learn. Clustering and Gaussian mixture documentation. https://scikit-learn.org/stable/",
        "Streamlit. Documentation. https://docs.streamlit.io/",
    ]
    for index, ref in enumerate(refs, start=1):
        doc.add_paragraph(f"[{index}] {ref}")
    configure_sections(doc)
    doc.core_properties.title = "Phân khúc khách hàng theo hành vi mua sắm"
    doc.core_properties.subject = "Bài tập lớn CO4033 - Đề tài 04"
    doc.core_properties.author = "Nhóm thực hiện đề tài 04"
    doc.core_properties.keywords = "RFM, customer segmentation, K-Means, GMM, BIRCH, Streamlit"
    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build_report())

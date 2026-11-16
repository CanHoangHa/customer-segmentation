// Rebuild the editable PowerPoint deliverable from verified project metrics.
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const workspaceDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const buildDir = path.join(workspaceDir, ".build/presentation");
const previewDir = path.join(buildDir, "previews");
const finalPath = path.join(workspaceDir, "deliverables/Customer_Segmentation_Presentation.pptx");
const runtimeModules = process.env.RUNTIME_NODE_MODULES ?? process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
const skillDir = process.env.PRESENTATIONS_SKILL_DIR;
const runtimePython = process.env.RUNTIME_PYTHON;
if (!runtimeModules || !skillDir || !runtimePython) {
  throw new Error("Set RUNTIME_NODE_MODULES, PRESENTATIONS_SKILL_DIR and RUNTIME_PYTHON before building the deck.");
}
const artifactToolPath = path.join(runtimeModules, "@oai/artifact-tool/dist/artifact_tool.mjs");

const { Presentation, PresentationFile } = await import(pathToFileURL(artifactToolPath).href);
const {
  finalizePresentation,
  applyPresentationChartFont,
} = await import(pathToFileURL(path.join(skillDir, "container_tools/artifact_tool_utils.mjs")).href);

const C = {
  navy: "#17324D",
  blue: "#2C6EAA",
  teal: "#2A9D8F",
  gold: "#E9C46A",
  red: "#C75B5B",
  ink: "#243447",
  muted: "#5E7183",
  pale: "#EAF1F7",
  grid: "#D4E2EE",
  white: "#FFFFFF",
  bg: "#F7FAFC",
};
const FONT = "Arial";
const W = 1280;
const H = 720;
const M = 72;

await fs.mkdir(previewDir, { recursive: true });
await fs.mkdir(path.dirname(finalPath), { recursive: true });

const deck = Presentation.create({ slideSize: { width: W, height: H } });

function textbox(slide, text, box, style = {}, name = undefined) {
  const shape = slide.shapes.add({
    geometry: "textbox",
    name,
    position: box,
    fill: "none",
    line: { style: "solid", fill: "none", width: 0 },
  });
  shape.text = text;
  shape.text.style = {
    typeface: FONT,
    fontSize: 24,
    color: C.ink,
    autoFit: "none",
    ...style,
  };
  return shape;
}

function rect(slide, box, fill, radius = "rounded-xl", name = undefined, lineFill = fill) {
  return slide.shapes.add({
    geometry: radius === "none" ? "rect" : "roundRect",
    name,
    position: box,
    fill,
    line: { style: "solid", fill: lineFill, width: 1 },
    ...(radius === "none" ? {} : { borderRadius: radius }),
  });
}

function title(slide, heading, subheading = "") {
  textbox(slide, heading, { left: M, top: 38, width: 1050, height: 74 }, { fontSize: 32, bold: true, color: C.navy }, "slide-title");
  if (subheading) textbox(slide, subheading, { left: M, top: 108, width: 1120, height: 34 }, { fontSize: 17, color: C.muted }, "slide-subtitle");
  textbox(slide, String(deck.slides.items.length).padStart(2, "0"), { left: 1168, top: 48, width: 42, height: 30 }, { fontSize: 15, bold: true, color: C.blue, alignment: "right" }, "slide-number");
}

function note(slide, text) {
  slide.speakerNotes.text = text;
  slide.speakerNotes.setVisible(true);
}

function styleTable(table, headerRows = 1) {
  table.borders.assign({ style: "solid", fill: C.grid, width: 1 });
  table.cells.block({ row: 0, column: 0, rowCount: table.rows.length, columnCount: table.columns.length }).assign({
    textStyle: { typeface: FONT, fontSize: 15, color: C.ink },
    margins: { left: 10, right: 10, top: 8, bottom: 8 },
    anchor: "middle",
  });
  if (headerRows > 0) {
    table.cells.block({ row: 0, column: 0, rowCount: headerRows, columnCount: table.columns.length }).assign({
      fill: C.navy,
      textStyle: { typeface: FONT, fontSize: 15, bold: true, color: C.white },
    });
  }
  for (let row = 0; row < table.rows.length; row += 1) {
    for (let column = 0; column < table.columns.length; column += 1) {
      const cell = table.getCell(row, column);
      cell.fill = row < headerRows ? C.navy : (row % 2 === 0 ? C.bg : C.white);
      cell.text.style = {
        typeface: FONT,
        fontSize: 14,
        bold: row < headerRows,
        color: row < headerRows ? C.white : C.ink,
      };
    }
  }
}

function styleChart(chart) {
  applyPresentationChartFont(chart, { fontFamily: FONT });
}

// 1 — cover
{
  const slide = deck.slides.add();
  slide.background.fill = C.navy;
  rect(slide, { left: 76, top: 98, width: 14, height: 470 }, C.teal, "none", "cover-accent");
  textbox(slide, "BÀI TẬP LỚN CO4033  ·  ĐỀ TÀI 04", { left: 126, top: 105, width: 760, height: 34 }, { fontSize: 16, bold: true, color: C.gold }, "cover-kicker");
  textbox(slide, "PHÂN KHÚC KHÁCH HÀNG\nTHEO HÀNH VI MUA SẮM", { left: 126, top: 195, width: 930, height: 190 }, { fontSize: 47, bold: true, color: C.white }, "cover-title");
  textbox(slide, "RFM · K-Means · Gaussian Mixture · BIRCH", { left: 130, top: 414, width: 780, height: 44 }, { fontSize: 25, color: C.pale }, "cover-subtitle");
  textbox(slide, "234.359 khách hàng  |  Dữ liệu giao dịch năm 2020  |  Hoàn thiện 06/11/2026", { left: 130, top: 555, width: 940, height: 34 }, { fontSize: 17, color: "#BFD2E2" }, "cover-meta");
  note(slide, "Mở đầu bằng ba câu hỏi kinh doanh. Nhấn mạnh đây là phân khúc mô tả, không phải mô hình dự đoán churn. Nguồn dữ liệu: https://data.rees46.com/");
}

// 2 — questions and scope
{
  const slide = deck.slides.add();
  slide.background.fill = C.bg;
  title(slide, "Ba câu hỏi định hướng toàn bộ dự án", "Đầu ra phục vụ nhân viên CRM và quản lý marketing");
  const items = [
    ["01", "Khách hàng khác nhau thế nào về R, F và M?"],
    ["02", "Nhóm nào có giá trị cao nhưng đã lâu chưa quay lại?"],
    ["03", "Bốn phương pháp khác nhau thế nào về chất lượng, tốc độ và khả năng giải thích?"],
  ];
  items.forEach(([num, text], i) => {
    const y = 170 + i * 126;
    textbox(slide, num, { left: 82, top: y + 8, width: 80, height: 44 }, { fontSize: 31, bold: true, color: C.teal }, `question-${num}`);
    textbox(slide, text, { left: 178, top: y, width: 880, height: 70 }, { fontSize: 25, bold: true, color: C.navy }, `question-text-${num}`);
    if (i < items.length - 1) rect(slide, { left: 178, top: y + 86, width: 930, height: 2 }, C.grid, "none", `divider-${num}`);
  });
  rect(slide, { left: 72, top: 570, width: 1136, height: 82 }, C.pale, "rounded-xl", "scope-callout", C.grid);
  textbox(slide, "Ranh giới", { left: 98, top: 592, width: 150, height: 34 }, { fontSize: 18, bold: true, color: C.blue });
  textbox(slide, "Không gọi M là lợi nhuận · Không gọi mua lặp là retention · Không kết luận tác động chiến dịch khi chưa có nhóm đối chứng", { left: 254, top: 585, width: 900, height: 48 }, { fontSize: 18, color: C.ink });
  note(slide, "Đây là ba câu hỏi đã khóa trong PLAN.md. Người dùng dashboard là CRM hoặc marketing. Mọi kết luận phải giữ đúng giới hạn KPI.");
}

// 3 — data quality
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "Chỉ 22,81% dòng nguồn đủ điều kiện vào RFM", "Thiếu customer_id là nguyên nhân loại lớn nhất");
  const chart = slide.charts.add("bar", {
    position: { left: 74, top: 166, width: 710, height: 405 },
    categories: ["Dòng nguồn", "Thiếu customer_id", "Dòng hợp lệ", "Ngoài phạm vi", "Giá không dương"],
    series: [{
      name: "Số dòng",
      values: [2633521, 2030733, 600784, 1436, 568],
      fill: C.blue,
      points: [
        { idx: 0, fill: C.blue }, { idx: 1, fill: C.red }, { idx: 2, fill: C.teal }, { idx: 3, fill: C.gold }, { idx: 4, fill: "#8D99AE" },
      ],
    }],
    barOptions: { direction: "bar", grouping: "clustered", gapWidth: 45, varyColors: true },
    hasLegend: false,
    xAxis: { visible: false, majorGridlines: null },
    yAxis: { textStyle: { fill: C.ink, fontSize: 15 }, line: { style: "solid", fill: C.grid, width: 1 } },
    dataLabels: { showValue: true, showCategoryName: true, separator: "  ", position: "outEnd", numberFormatCode: "#,##0", textStyle: { fill: C.navy, fontSize: 13, bold: true } },
    chartFill: C.white,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.white,
    plotAreaLine: { fill: "none", width: 0 },
  });
  styleChart(chart);
  rect(slide, { left: 846, top: 174, width: 330, height: 160 }, C.navy, "rounded-xl", "coverage-kpi");
  textbox(slide, "600.784", { left: 876, top: 204, width: 270, height: 58 }, { fontSize: 42, bold: true, color: C.white, alignment: "center" });
  textbox(slide, "dòng mua hợp lệ", { left: 876, top: 271, width: 270, height: 34 }, { fontSize: 18, color: C.pale, alignment: "center" });
  textbox(slide, "234.359 khách\n402.993 đơn\n31,9096% mua lặp", { left: 858, top: 372, width: 310, height: 148 }, { fontSize: 25, bold: true, color: C.navy, alignment: "center" });
  textbox(slide, "Kết quả chỉ đại diện cho phần giao dịch gắn được customer_id.", { left: 840, top: 555, width: 345, height: 54 }, { fontSize: 17, color: C.red, bold: true, alignment: "center" });
  note(slide, "Nguồn số liệu: reports/cleaning_summary.json và reports/rfm_summary.json. Tổng dòng 2.633.521; hợp lệ 600.784; thiếu customer_id 2.030.733.");
}

// 4 — RFM and methods
{
  const slide = deck.slides.add();
  slide.background.fill = C.bg;
  title(slide, "Một cohort, hai cách phân khúc", "RFM gốc để giải thích · log1p + StandardScaler để học máy");
  const cols = [
    { x: 72, color: C.teal, label: "RFM", big: "R · F · M", lines: "Recency: số ngày\nFrequency: số đơn riêng biệt\nMonetary: tổng price" },
    { x: 430, color: C.blue, label: "BASELINE", big: "5 nhóm", lines: "Percentile rank giữ tie\nQuy tắc có thứ tự ưu tiên\nPhủ 100% khách" },
    { x: 788, color: C.gold, label: "HỌC MÁY", big: "3–6 cụm", lines: "K-Means · GMM · BIRCH\nCùng scaler, cùng cohort\nSeed 42" },
  ];
  cols.forEach((item, i) => {
    rect(slide, { left: item.x, top: 170, width: 324, height: 392 }, C.white, "rounded-xl", `method-card-${i}`, C.grid);
    rect(slide, { left: item.x, top: 170, width: 324, height: 12 }, item.color, "none", `method-accent-${i}`);
    textbox(slide, item.label, { left: item.x + 28, top: 210, width: 270, height: 30 }, { fontSize: 15, bold: true, color: item.color });
    textbox(slide, item.big, { left: item.x + 28, top: 262, width: 270, height: 64 }, { fontSize: 38, bold: true, color: C.navy });
    textbox(slide, item.lines, { left: item.x + 28, top: 360, width: 270, height: 140 }, { fontSize: 20, color: C.ink });
  });
  textbox(slide, "kz.csv  →  giao dịch sạch  →  RFM theo khách  →  4 phương pháp  →  profile và dashboard", { left: 112, top: 610, width: 1050, height: 38 }, { fontSize: 20, bold: true, color: C.navy, alignment: "center" });
  note(slide, "Ngày chốt 22/11/2020. Baseline dùng RFM gốc. Ba thuật toán dùng log1p và StandardScaler nhưng giữ RFM gốc trong artifact để giải thích.");
}

// 5 — experiment setup
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "So sánh công bằng trên cùng dữ liệu và cùng mẫu", "Huấn luyện toàn cohort · Silhouette trên mẫu cố định 5.000 khách");
  const table = slide.tables.add({
    rows: 5,
    columns: 5,
    left: 72,
    top: 164,
    width: 1136,
    height: 300,
    columnWidths: [220, 210, 165, 210, 331],
    values: [
      ["Phương pháp", "Grid", "Seed", "Đo thời gian", "Tiêu chí chọn"],
      ["Ngưỡng RFM", "1 cấu hình", "Không áp dụng", "Không benchmark", "Baseline giải thích được"],
      ["K-Means", "k = 3…6", "42", "Warm-up + 3 lần", "Silhouette cao nhất, cụm min ≥ 1%"],
      ["GMM", "k = 3…6", "42", "Warm-up + 3 lần", "Silhouette cao nhất, cụm min ≥ 1%"],
      ["BIRCH", "k = 3…6; t = 0,3/0,5/0,7", "—", "Warm-up + 3 lần", "Fallback nếu không cấu hình nào đạt 1%"],
    ],
  });
  styleTable(table);
  rect(slide, { left: 72, top: 505, width: 1136, height: 112 }, C.pale, "rounded-xl", "experiment-note", C.grid);
  textbox(slide, "Silhouette không phải độ chính xác", { left: 100, top: 529, width: 380, height: 34 }, { fontSize: 21, bold: true, color: C.blue });
  textbox(slide, "Chỉ số đo độ tách cụm trong không gian RFM đã biến đổi. Quyết định cuối còn xét quy mô cụm, tốc độ và khả năng dùng cho CRM.", { left: 492, top: 520, width: 680, height: 66 }, { fontSize: 19, color: C.ink });
  note(slide, "Nguồn: reports/run_metadata.json và docs/modeling.md. Mẫu Silhouette có hash lưu trong metadata để tái lập.");
}

// 6 — model comparison
{
  const slide = deck.slides.add();
  slide.background.fill = C.bg;
  title(slide, "BIRCH tách mạnh nhất nhưng không tạo nhóm vận hành cân bằng", "K-Means k = 3 là lựa chọn mặc định cho dashboard");
  const chart = slide.charts.add("bar", {
    position: { left: 70, top: 164, width: 700, height: 372 },
    categories: ["Ngưỡng RFM", "K-Means", "GMM", "BIRCH"],
    series: [{
      name: "Silhouette",
      values: [0.1969, 0.3470, 0.1919, 0.4862],
      fill: C.blue,
      points: [
        { idx: 0, fill: "#8D99AE" }, { idx: 1, fill: C.teal }, { idx: 2, fill: C.blue }, { idx: 3, fill: C.gold },
      ],
    }],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 60, varyColors: true },
    hasLegend: false,
    xAxis: { textStyle: { fill: C.ink, fontSize: 14 }, line: { style: "solid", fill: C.grid, width: 1 } },
    yAxis: { min: 0, max: 0.55, majorUnit: 0.1, numberFormatCode: "0.0", textStyle: { fill: C.muted, fontSize: 12 }, majorGridlines: { style: "solid", fill: C.grid, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0.000", textStyle: { fill: C.navy, fontSize: 14, bold: true } },
    chartFill: C.bg,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.bg,
    plotAreaLine: { fill: "none", width: 0 },
  });
  styleChart(chart);
  const table = slide.tables.add({
    rows: 5,
    columns: 3,
    left: 800,
    top: 182,
    width: 408,
    height: 300,
    columnWidths: [140, 120, 148],
    values: [
      ["Phương pháp", "Fit trung vị", "Cụm nhỏ nhất"],
      ["RFM", "—", "12,84%"],
      ["K-Means", "0,774 s", "21,47%"],
      ["GMM", "3,534 s", "14,52%"],
      ["BIRCH", "2,567 s", "0,095%"],
    ],
  });
  styleTable(table);
  textbox(slide, "KẾT LUẬN", { left: 816, top: 525, width: 130, height: 28 }, { fontSize: 14, bold: true, color: C.red });
  textbox(slide, "BIRCH dồn 97,42% khách vào một cụm. K-Means cân bằng hơn và fit nhanh nhất trong ba mô hình học máy được chọn.", { left: 816, top: 557, width: 360, height: 86 }, { fontSize: 18, bold: true, color: C.navy });
  note(slide, "Nguồn: reports/model_comparison.csv và reports/segment_profiles.csv. BIRCH được chọn theo fallback vì không cấu hình nào đạt tỷ trọng cụm tối thiểu 1%.");
}

// 7 — KMeans profiles
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "Ba nhóm K-Means khác nhau về thời điểm mua và đóng góp M", "S1 chỉ 21,47% khách nhưng chiếm 59,69% tổng M");
  const chart = slide.charts.add("bar", {
    position: { left: 70, top: 166, width: 650, height: 360 },
    categories: ["S1", "S2", "S3"],
    series: [
      { name: "% khách", values: [21.47, 52.01, 26.52], fill: C.blue },
      { name: "% tổng M", values: [59.69, 27.41, 12.90], fill: C.teal },
    ],
    barOptions: { direction: "column", grouping: "clustered", gapWidth: 55 },
    legend: { position: "bottom", overlay: false, textStyle: { fill: C.ink, fontSize: 13 } },
    xAxis: { textStyle: { fill: C.ink, fontSize: 15, bold: true }, line: { style: "solid", fill: C.grid, width: 1 } },
    yAxis: { min: 0, max: 70, majorUnit: 10, numberFormatCode: "0\"%\"", textStyle: { fill: C.muted, fontSize: 12 }, majorGridlines: { style: "solid", fill: C.grid, width: 1 } },
    dataLabels: { showValue: true, position: "outEnd", numberFormatCode: "0.0\"%\"", textStyle: { fill: C.navy, fontSize: 13, bold: true } },
    chartFill: C.white,
    chartLine: { fill: "none", width: 0 },
    plotAreaFill: C.white,
    plotAreaLine: { fill: "none", width: 0 },
  });
  styleChart(chart);
  const table = slide.tables.add({
    rows: 4,
    columns: 5,
    left: 752,
    top: 188,
    width: 456,
    height: 250,
    columnWidths: [90, 120, 80, 75, 91],
    values: [
      ["Nhóm", "Khách", "R ngày", "F đơn", "M"],
      ["S1", "50.318", "78", "3", "909,48"],
      ["S2", "121.895", "119", "1", "150,44"],
      ["S3", "62.146", "19", "1", "104,14"],
    ],
  });
  styleTable(table);
  rect(slide, { left: 752, top: 468, width: 456, height: 140 }, C.pale, "rounded-xl", "profile-callout", C.grid);
  textbox(slide, "S1", { left: 782, top: 495, width: 56, height: 35 }, { fontSize: 25, bold: true, color: C.teal });
  textbox(slide, "giá trị và mua lặp cao", { left: 842, top: 494, width: 330, height: 35 }, { fontSize: 20, bold: true, color: C.navy });
  textbox(slide, "S2: mua ít, lâu chưa quay lại\nS3: mới mua gần đây", { left: 782, top: 540, width: 390, height: 58 }, { fontSize: 16, color: C.ink });
  note(slide, "Nguồn: reports/segment_profiles.csv. Tất cả KPI dùng toàn bộ cohort, không dùng mẫu biểu đồ.");
}

// 8 — CRM tests
{
  const slide = deck.slides.add();
  slide.background.fill = C.bg;
  title(slide, "Mỗi insight đi kèm một thử nghiệm và điều kiện dừng", "Phân khúc tạo giả thuyết; nhóm đối chứng mới đo được tác động");
  const table = slide.tables.add({
    rows: 5,
    columns: 4,
    left: 62,
    top: 160,
    width: 1156,
    height: 400,
    columnWidths: [180, 360, 290, 326],
    values: [
      ["Đối tượng", "Giả thuyết", "KPI", "Rủi ro / điều kiện dừng"],
      ["K-Means S1", "Quyền lợi thành viên hoặc gợi ý mua bổ sung", "Đơn mới, thời gian đến đơn, M tăng thêm", "Giới hạn tần suất; dừng nếu phản hồi tiêu cực tăng"],
      ["K-Means S2", "Tái tương tác chi phí thấp", "Tỷ lệ quay lại, chi phí/khách quay lại", "Dừng nếu không hơn nhóm đối chứng"],
      ["K-Means S3", "Onboarding sau mua để thúc đẩy đơn thứ hai", "Đơn thứ hai trong 30/60 ngày", "Kiểm tra quyền liên hệ và tỷ lệ từ chối"],
      ["Baseline giá trị cao", "Win-back có giới hạn ưu đãi", "Tác động tăng thêm nếu có dữ liệu chi phí", "Không gọi là churn khi chưa có nhãn tương lai"],
    ],
  });
  styleTable(table);
  rect(slide, { left: 62, top: 600, width: 1156, height: 58 }, "#FFF4D6", "rounded-xl", "causality-warning", "#F0D58A");
  textbox(slide, "Không gửi chiến dịch trực tiếp từ dashboard: cần kiểm tra quyền liên hệ, ngân sách và thiết kế A/B test trước.", { left: 88, top: 614, width: 1100, height: 30 }, { fontSize: 18, bold: true, color: C.navy, alignment: "center" });
  note(slide, "Nguồn: docs/results.md và logic app/data.py. Không diễn giải tương quan phân khúc thành quan hệ nhân quả.");
}

// 9 — architecture and reproducibility
{
  const slide = deck.slides.add();
  slide.background.fill = C.white;
  title(slide, "Pipeline tạo artifact một lần, dashboard chỉ đọc", "Một khóa customer_id · một ngày chốt · một định nghĩa KPI");
  textbox(slide, "kz.csv  →  làm sạch / quarantine  →  customer_rfm.parquet  →  baseline + 3 model  →  reports + segments  →  Streamlit", { left: 82, top: 174, width: 1110, height: 88 }, { fontSize: 25, bold: true, color: C.navy, alignment: "center" }, "pipeline-text");
  const facts = [
    ["TÁI LẬP", "Sort customer_id\nSeed 42\nHash mẫu Silhouette"],
    ["ĐỐI CHIẾU", "Số khách\nTổng M\nKhách mua lặp"],
    ["BÀN GIAO", "Parquet curated\nCSV profiles\nJSON metadata"],
  ];
  facts.forEach(([head, body], i) => {
    const x = 98 + i * 378;
    rect(slide, { left: x, top: 334, width: 330, height: 210 }, i === 1 ? C.pale : C.bg, "rounded-xl", `architecture-fact-${i}`, C.grid);
    textbox(slide, head, { left: x + 26, top: 368, width: 280, height: 30 }, { fontSize: 15, bold: true, color: i === 1 ? C.blue : C.teal, alignment: "center" });
    textbox(slide, body, { left: x + 26, top: 420, width: 280, height: 98 }, { fontSize: 22, bold: true, color: C.navy, alignment: "center" });
  });
  textbox(slide, "21 kiểm thử không phụ thuộc Spark đã qua  ·  Dashboard smoke test HTTP 200  ·  README có lệnh chạy end-to-end", { left: 100, top: 610, width: 1080, height: 34 }, { fontSize: 18, color: C.muted, alignment: "center" });
  note(slide, "Sơ đồ chi tiết: docs/architecture.md. Bộ kiểm thử 21 test đã chạy qua sau merge dashboard. PySpark cần Python 3.11 và Java 17 như README.");
}

// 10 — conclusion
{
  const slide = deck.slides.add();
  slide.background.fill = C.navy;
  textbox(slide, "KẾT LUẬN", { left: 78, top: 62, width: 240, height: 34 }, { fontSize: 16, bold: true, color: C.gold }, "conclusion-kicker");
  textbox(slide, "Chọn K-Means để vận hành,\ngiữ baseline để giải thích", { left: 78, top: 145, width: 820, height: 145 }, { fontSize: 43, bold: true, color: C.white }, "conclusion-title");
  const takeaways = [
    "234.359 khách trên cùng cohort và cùng ngày chốt",
    "K-Means k = 3: Silhouette 0,3470; cụm nhỏ nhất 21,47%",
    "BIRCH là cảnh báo: chỉ số cao không đủ nếu cụm mất cân bằng",
    "Bước tiếp theo: A/B test có nhóm đối chứng và đánh giá drift",
  ];
  takeaways.forEach((text, i) => {
    textbox(slide, `${i + 1}`, { left: 88, top: 340 + i * 66, width: 48, height: 38 }, { fontSize: 22, bold: true, color: C.teal, alignment: "center" });
    textbox(slide, text, { left: 156, top: 338 + i * 66, width: 940, height: 42 }, { fontSize: 21, color: C.pale });
  });
  textbox(slide, "Demo: streamlit run app/app.py", { left: 790, top: 650, width: 420, height: 28 }, { fontSize: 17, bold: true, color: C.gold, alignment: "right" });
  note(slide, "Kết lại bằng quyết định và giới hạn. Mời mở dashboard theo kịch bản trong docs/demo.md.");
}

// Export slide previews.
for (const [index, slide] of deck.slides.items.entries()) {
  const name = `slide-${String(index + 1).padStart(2, "0")}.png`;
  const blob = await deck.export({ slide, format: "png", scale: 1 });
  await fs.writeFile(path.join(previewDir, name), new Uint8Array(await blob.arrayBuffer()));
}

const requirements = {
  explicitTotalSlideCount: 10,
  requiredNativeTableOwnerSlides: [5, 6, 7, 8],
  requiredNativeChartOwnerSlides: [3, 6, 7],
  requiredEmbeddedWorkbookChartOwnerSlides: [],
  materializeLiteralChartWorkbooks: true,
  nativeChartTargetApplication: "powerpoint",
};
const fontPolicy = { basis: "design", families: [FONT, "Aptos"] };
const stagingDir = path.join(workspaceDir, ".codex-finalizer");
await fs.mkdir(stagingDir, { recursive: true });
const candidatePath = path.join(stagingDir, "customer-segmentation-candidate.pptx");
await (await PresentationFile.exportPptx(deck)).save(candidatePath);

const result = await finalizePresentation({
  ...requirements,
  workspaceDir,
  candidatePath,
  finalPath,
  pythonExecutable: runtimePython,
  integrityValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_package_integrity.py"),
  layoutValidatorPath: path.join(skillDir, "container_tools/inspect_presentation_layout_geometry.py"),
  layoutArgs: [
    "--expected-slide-size-emu", "12192000,6858000",
    "--validate-heading-fit",
    ...requirements.requiredNativeTableOwnerSlides.flatMap((number) => ["--require-native-table-slide", String(number)]),
  ],
  requiredNativeTableOwnerSlides: requirements.requiredNativeTableOwnerSlides,
  fontPolicy,
  verifyArtifactToolImport: true,
  receiptPath: path.join(stagingDir, "Customer_Segmentation_Presentation.v2.validation.json"),
});

console.log(JSON.stringify({ finalPath, result }, null, 2));

"""Interactive BI dashboard for persisted customer segmentation results."""

import os
from pathlib import Path
import sys

import streamlit as st

CODE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_ROOT))

from app.charts import (
    customer_scatter,
    model_comparison_chart,
    monetary_share_chart,
    rfm_profile_chart,
    segment_size_chart,
)
from app.data import DashboardDataError, crm_hypotheses, load_dashboard_data, method_label


DATA_ROOT = Path(os.environ.get("CUSTOMER_SEGMENTATION_ROOT", CODE_ROOT))


@st.cache_data(show_spinner=False)
def dashboard_data(root: str):
    return load_dashboard_data(root)


st.set_page_config(page_title="Phân khúc khách hàng", page_icon="📊", layout="wide")
st.title("Phân khúc khách hàng theo hành vi mua sắm")
st.caption("RFM, baseline theo ngưỡng và ba thuật toán phân cụm trên cùng cohort")

try:
    data = dashboard_data(str(DATA_ROOT))
except DashboardDataError as error:
    st.error(str(error))
    st.info("Chạy scripts/run_segmentation.py trước khi mở dashboard.")
    st.stop()

method_options = sorted(data.segments["method"].unique(), key=lambda value: method_label(value))
method = st.sidebar.selectbox(
    "Phương pháp",
    options=method_options,
    format_func=method_label,
    index=method_options.index("kmeans") if "kmeans" in method_options else 0,
)
selected_segments = data.segments[data.segments["method"] == method]
selected_profiles = data.profiles[data.profiles["method"] == method]
reference_date = data.run_metadata["reference_date"]

overview, profiles_tab, comparison_tab, actions_tab = st.tabs(
    ["Phạm vi dữ liệu", "Hồ sơ phân khúc", "So sánh phương pháp", "Giả thuyết CRM"]
)

with overview:
    customer_count = selected_segments["customer_id"].nunique()
    repeat_pct = selected_segments["is_repeat_customer"].mean() * 100
    total_m = selected_segments["monetary_value"].sum()
    coverage = data.cleaning_summary["clean_rows"] / data.cleaning_summary["raw_rows"] * 100
    first, second, third, fourth = st.columns(4)
    first.metric("Khách được phân khúc", f"{customer_count:,}")
    second.metric("Khách mua lặp trong kỳ", f"{repeat_pct:.2f}%")
    third.metric("Tổng M", f"{total_m:,.2f}")
    fourth.metric("Dòng hợp lệ", f"{coverage:.2f}%")
    st.write(
        f"Khoảng quan sát dùng ngày chốt **{reference_date}** theo UTC. "
        "M dùng đơn vị giá theo nguồn, không phải lợi nhuận hoặc doanh thu thuần kế toán."
    )
    if coverage < 50:
        st.warning(
            "Phần lớn dòng gốc thiếu mã khách nên kết quả chỉ mô tả khách có đủ dữ liệu, "
            "không đại diện cho toàn bộ người mua."
        )
    left, right = st.columns(2)
    left.plotly_chart(segment_size_chart(data.profiles, method), use_container_width=True)
    right.plotly_chart(monetary_share_chart(data.profiles, method), use_container_width=True)

with profiles_tab:
    options = selected_profiles["segment_name"].tolist()
    chosen = st.multiselect("Phân khúc hiển thị", options=options, default=options)
    filtered_profiles = data.profiles[
        (data.profiles["method"] == method) & data.profiles["segment_name"].isin(chosen)
    ]
    filtered_segments = data.segments[
        (data.segments["method"] == method) & data.segments["segment_name"].isin(chosen)
    ]
    if filtered_profiles.empty:
        st.info("Chọn ít nhất một phân khúc để xem hồ sơ.")
    else:
        st.plotly_chart(rfm_profile_chart(filtered_profiles, method), use_container_width=True)
        st.plotly_chart(customer_scatter(filtered_segments, method), use_container_width=True)
        st.dataframe(
            filtered_profiles[
                [
                    "segment_name",
                    "customers",
                    "customer_pct",
                    "median_recency_days",
                    "median_frequency_orders",
                    "median_monetary_value",
                    "monetary_share_pct",
                    "repeat_customer_pct",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

with comparison_tab:
    st.plotly_chart(model_comparison_chart(data.comparison), use_container_width=True)
    selected_comparison = data.comparison[data.comparison["selected"]].copy()
    selected_comparison["Phương pháp"] = selected_comparison["method"].map(method_label)
    st.dataframe(
        selected_comparison[
            [
                "Phương pháp",
                "config_id",
                "actual_clusters",
                "silhouette",
                "median_fit_seconds",
                "smallest_segment_pct",
                "eligible_for_selection",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )
    fallback = selected_comparison[~selected_comparison["eligible_for_selection"]]
    if not fallback.empty:
        names = ", ".join(fallback["Phương pháp"].tolist())
        st.warning(
            f"{names} dùng lựa chọn fallback vì mọi cấu hình hợp lệ đều có cụm nhỏ hơn ngưỡng 1%. "
            "Cần xem quy mô cụm cùng Silhouette trước khi chọn mô hình cho CRM."
        )
    st.caption(
        "Silhouette đo độ tách trên cùng mẫu cố định 5.000 khách. "
        "Chỉ số này không đo hiệu quả chiến dịch hoặc độ chính xác có nhãn."
    )

with actions_tab:
    st.write(
        "Các đề xuất dưới đây là giả thuyết cần thử bằng nhóm đối chứng. "
        "Dashboard không khẳng định chiến dịch sẽ làm khách quay lại."
    )
    st.dataframe(
        crm_hypotheses(data.profiles, method),
        use_container_width=True,
        hide_index=True,
    )

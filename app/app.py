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
REPEAT_RATE_LABEL = "Tỷ lệ khách có từ 2 đơn"


@st.cache_data(show_spinner=False)
def dashboard_data(root: str):
    return load_dashboard_data(root)


st.set_page_config(page_title="Phân khúc khách hàng", layout="wide")
st.title("Phân khúc khách hàng")
st.caption("Khám phá các nhóm khách theo lịch sử mua hàng và so sánh cách phân nhóm.")

try:
    data = dashboard_data(str(DATA_ROOT))
except DashboardDataError as error:
    st.error(str(error))
    st.info("Chạy scripts/run_segmentation.py để tạo dữ liệu cho dashboard.")
    st.stop()

profiles_tab, comparison_tab, overview = st.tabs(
    ["Phân khúc khách hàng", "So sánh mô hình", "Phạm vi dữ liệu"]
)

with profiles_tab:
    st.subheader("Khách hàng được chia như thế nào?")
    method_options = sorted(data.profiles["method"].unique(), key=method_label)
    method = st.selectbox(
        "Phương pháp phân khúc",
        options=method_options,
        format_func=method_label,
        index=method_options.index("kmeans") if "kmeans" in method_options else 0,
        key="profile_method",
    )
    profiles = data.profiles[data.profiles["method"] == method].sort_values("segment_id")
    highest_value = profiles.loc[profiles["monetary_share_pct"].idxmax()]
    st.markdown(
        f"**{highest_value['segment_name']}** chiếm "
        f"**{highest_value['customer_pct']:.2f}%** số khách và đóng góp "
        f"**{highest_value['monetary_share_pct']:.2f}%** tổng giá trị mua."
    )

    left, right = st.columns(2)
    with left:
        st.subheader("Tỷ trọng khách hàng")
        st.plotly_chart(segment_size_chart(profiles, method))
    with right:
        st.subheader("Tỷ trọng giá trị mua")
        st.plotly_chart(monetary_share_chart(profiles, method))

    st.subheader("Đặc điểm từng nhóm")
    st.caption(
        "Các cột trung vị mô tả khách điển hình của nhóm. "
        "Tỷ lệ khách có từ 2 đơn được tính trong từng nhóm, trong kỳ quan sát."
    )
    st.dataframe(
        profiles[[
            "segment_name", "customers", "customer_pct", "monetary_share_pct",
            "median_recency_days", "median_frequency_orders", "median_monetary_value",
            "repeat_customer_pct",
        ]],
        column_config={
            "segment_name": "Phân khúc",
            "customers": "Số khách",
            "customer_pct": st.column_config.NumberColumn("Tỷ trọng khách", format="%.2f%%"),
            "monetary_share_pct": st.column_config.NumberColumn("Tỷ trọng giá trị mua", format="%.2f%%"),
            "median_recency_days": "Ngày từ lần mua cuối (trung vị)",
            "median_frequency_orders": "Số đơn (trung vị)",
            "median_monetary_value": st.column_config.NumberColumn(
                "Giá trị mua (trung vị)", format="%.2f"
            ),
            "repeat_customer_pct": st.column_config.NumberColumn(REPEAT_RATE_LABEL, format="%.2f%%"),
        },
        hide_index=True,
    )

    with st.expander("Đề xuất chăm sóc khách hàng"):
        st.caption(
            "Đây là các giả thuyết cần thử với nhóm đối chứng. "
            "Hai phân khúc có hành vi tương tự có thể nhận cùng đề xuất."
        )
        hypotheses = crm_hypotheses(data.profiles, method).set_index("Phân khúc")
        segment = st.selectbox(
            "Phân khúc cần chăm sóc", options=hypotheses.index.tolist(), key=f"care_{method}"
        )
        proposal = hypotheses.loc[segment]
        st.write(proposal["Quan sát"])
        st.markdown(f"**Đề xuất thử nghiệm:** {proposal['Giả thuyết thử nghiệm']}")
        st.markdown(f"**Chỉ số theo dõi:** {proposal['KPI theo dõi']}")
        st.markdown(f"**Rủi ro:** {proposal['Rủi ro']}")

    with st.expander("Xem chi tiết RFM và phân bố khách hàng"):
        options = profiles["segment_name"].tolist()
        chosen = st.multiselect("Phân khúc hiển thị", options=options, default=options, key=method)
        if chosen:
            filtered_profiles = profiles[profiles["segment_name"].isin(chosen)]
            filtered_segments = data.segments[
                (data.segments["method"] == method) & data.segments["segment_name"].isin(chosen)
            ]
            st.plotly_chart(rfm_profile_chart(filtered_profiles, method))
            st.plotly_chart(customer_scatter(filtered_segments, method))
        else:
            st.info("Chọn ít nhất một phân khúc để xem chi tiết.")

with comparison_tab:
    st.subheader("Mức độ tách giữa các nhóm")
    st.plotly_chart(model_comparison_chart(data.comparison))
    sample_size = data.run_metadata["silhouette_sample_size"]
    st.caption(f"Silhouette đo độ tách cụm trên cùng mẫu {sample_size:,} khách. Điểm càng cao thì các cụm càng tách rõ.")

    selected = data.comparison[data.comparison["selected"]].copy()
    selected["Phương pháp"] = selected["method"].map(method_label)
    selected["smallest_segment_pct"] *= 100
    st.dataframe(
        selected[["Phương pháp", "actual_clusters", "silhouette", "median_fit_seconds", "smallest_segment_pct"]],
        column_config={
            "actual_clusters": "Số nhóm",
            "silhouette": st.column_config.NumberColumn("Silhouette", format="%.3f"),
            "median_fit_seconds": st.column_config.NumberColumn("Thời gian trung vị (giây)", format="%.3f"),
            "smallest_segment_pct": st.column_config.NumberColumn("Nhóm nhỏ nhất", format="%.3f%%"),
        },
        hide_index=True,
    )
    fallback = selected.loc[~selected["eligible_for_selection"], "Phương pháp"]
    if not fallback.empty:
        st.warning(
            f"{', '.join(fallback)} có nhóm nhỏ nhất dưới ngưỡng 1%. "
            "Khi chọn mô hình, cần xem cả Silhouette và quy mô từng nhóm."
        )

    with st.expander("Xem các cấu hình đã thử"):
        st.dataframe(
            data.comparison[["method", "config_id", "actual_clusters", "silhouette", "median_fit_seconds"]],
            column_config={
                "method": "Phương pháp",
                "config_id": "Cấu hình",
                "actual_clusters": "Số nhóm",
                "silhouette": st.column_config.NumberColumn("Silhouette", format="%.3f"),
                "median_fit_seconds": st.column_config.NumberColumn("Thời gian trung vị (giây)", format="%.3f"),
            },
            hide_index=True,
        )

with overview:
    rfm = data.rfm_summary
    clean = data.cleaning_summary
    coverage = clean["clean_rows"] / clean["raw_rows"] * 100
    first, second, third = st.columns(3)
    first.metric("Khách được phân khúc", f"{rfm['customers']:,}")
    second.metric("Đơn hàng", f"{rfm['orders']:,}")
    third.metric(REPEAT_RATE_LABEL, f"{rfm['repeat_customer_pct']:.2f}%")

    st.subheader("Dữ liệu dùng để phân tích")
    st.write(
        f"Giữ **{clean['clean_rows']:,} / {clean['raw_rows']:,} dòng giao dịch ({coverage:.2f}%)**. "
        "Phần lớn dòng bị loại do thiếu mã khách, nên kết quả chỉ mô tả tập khách xác định được."
    )
    st.write(
        f"Ngày chốt RFM là **{rfm['reference_date']} UTC**. "
        f"Tổng giá trị mua là **{float(rfm['monetary_value']):,.2f}** theo đơn vị giá của nguồn."
    )
    st.caption("R là số ngày từ lần mua cuối đến ngày chốt, F là số đơn và M là tổng giá trị mua.")

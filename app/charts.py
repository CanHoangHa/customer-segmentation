"""Plotly charts built only from persisted dashboard artifacts."""

import pandas as pd
import plotly.express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots

from app.data import method_label


COLORS = ["#2563EB", "#0F766E", "#D97706", "#7C3AED", "#DC2626", "#475569"]


def segment_size_chart(profiles: pd.DataFrame, method: str) -> go.Figure:
    frame = profiles[profiles["method"] == method].sort_values("customer_pct", ascending=False)
    figure = px.bar(
        frame,
        x="segment_name",
        y="customer_pct",
        color="segment_name",
        color_discrete_sequence=COLORS,
        labels={"segment_name": "Phân khúc", "customer_pct": "Tỷ trọng khách (%)"},
        title=f"Quy mô phân khúc theo {method_label(method)}",
    )
    figure.update_layout(showlegend=False, xaxis_title=None)
    return figure


def monetary_share_chart(profiles: pd.DataFrame, method: str) -> go.Figure:
    frame = profiles[profiles["method"] == method].sort_values(
        "monetary_share_pct", ascending=False
    )
    figure = px.bar(
        frame,
        x="segment_name",
        y="monetary_share_pct",
        color="segment_name",
        color_discrete_sequence=COLORS,
        labels={"segment_name": "Phân khúc", "monetary_share_pct": "Tỷ trọng M (%)"},
        title="Tỷ trọng giá trị mua theo phân khúc",
    )
    figure.update_layout(showlegend=False, xaxis_title=None)
    return figure


def rfm_profile_chart(profiles: pd.DataFrame, method: str) -> go.Figure:
    frame = profiles[profiles["method"] == method].sort_values("segment_id")
    figure = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=("Median R ngày", "Median F đơn", "Median M"),
    )
    for column_index, metric in enumerate(
        ("median_recency_days", "median_frequency_orders", "median_monetary_value"), start=1
    ):
        figure.add_trace(
            go.Bar(
                x=frame["segment_name"],
                y=frame[metric],
                marker_color=[COLORS[index % len(COLORS)] for index in range(len(frame))],
                showlegend=False,
                hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>",
            ),
            row=1,
            col=column_index,
        )
    figure.update_layout(title="Hồ sơ RFM gốc", height=430)
    return figure


def model_comparison_chart(comparison: pd.DataFrame) -> go.Figure:
    frame = comparison[(comparison["status"] == "ok") & comparison["silhouette"].notna()].copy()
    frame["Phương pháp"] = frame["method"].map(method_label)
    return px.scatter(
        frame,
        x="median_fit_seconds",
        y="silhouette",
        color="Phương pháp",
        symbol="selected",
        size="actual_clusters",
        hover_name="config_id",
        hover_data={
            "requested_clusters": True,
            "actual_clusters": True,
            "smallest_segment_pct": ":.3%",
            "median_fit_seconds": ":.3f",
            "silhouette": ":.3f",
        },
        labels={
            "median_fit_seconds": "Thời gian fit trung vị (giây)",
            "silhouette": "Silhouette trên mẫu cố định",
        },
        title="Chất lượng phân tách và thời gian chạy",
    )


def customer_scatter(segments: pd.DataFrame, method: str, max_points: int = 5_000) -> go.Figure:
    frame = segments[segments["method"] == method]
    if len(frame) > max_points:
        frame = frame.sample(max_points, random_state=42)
    frame = frame.drop(columns=["customer_id"], errors="ignore")
    return px.scatter(
        frame,
        x="recency_days",
        y="monetary_value",
        color="segment_name",
        color_discrete_sequence=COLORS,
        log_y=True,
        hover_data={
            "frequency_orders": True,
            "recency_days": True,
            "monetary_value": ":.2f",
        },
        labels={
            "recency_days": "R ngày",
            "monetary_value": "M theo đơn vị giá nguồn, thang log",
            "segment_name": "Phân khúc",
        },
        title=f"Phân bố R và M, mẫu cố định tối đa {max_points:,} khách",
    )

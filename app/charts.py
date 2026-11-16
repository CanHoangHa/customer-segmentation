"""Plotly charts built only from persisted dashboard artifacts."""

import pandas as pd
import plotly.express as px
from plotly import graph_objects as go
from plotly.subplots import make_subplots

from app.data import method_label


COLORS = ["#1D4ED8", "#0F766E", "#A64B08", "#6D28D9", "#B91C1C", "#475569"]


def _share_chart(profiles: pd.DataFrame, method: str, column: str) -> go.Figure:
    frame = profiles[profiles["method"] == method].sort_values("segment_id")
    figure = go.Figure(
        go.Pie(
            labels=frame["segment_name"],
            values=frame[column],
            hole=0.58,
            sort=False,
            marker_colors=COLORS,
            textinfo="percent",
            textposition="inside",
            insidetextfont_color="#FFFFFF",
            hovertemplate="%{label}<br>%{value:.2f}%<extra></extra>",
        )
    )
    figure.update_layout(
        height=330,
        margin=dict(t=12, b=12, l=16, r=16),
        legend=dict(orientation="h", y=-0.08),
        uniformtext=dict(minsize=12, mode="hide"),
    )
    return figure


def segment_size_chart(profiles: pd.DataFrame, method: str) -> go.Figure:
    return _share_chart(profiles, method, "customer_pct")


def monetary_share_chart(profiles: pd.DataFrame, method: str) -> go.Figure:
    return _share_chart(profiles, method, "monetary_share_pct")


def rfm_profile_chart(profiles: pd.DataFrame, method: str) -> go.Figure:
    frame = profiles[profiles["method"] == method].sort_values("segment_id")
    figure = make_subplots(
        rows=1,
        cols=3,
        subplot_titles=("Ngày từ lần mua cuối", "Số đơn", "Giá trị mua"),
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
    figure.update_layout(title="Trung vị theo phân khúc", height=430)
    return figure


def model_comparison_chart(comparison: pd.DataFrame) -> go.Figure:
    frame = comparison[comparison["selected"]].copy()
    frame["Phương pháp"] = frame["method"].map(method_label)
    figure = px.bar(
        frame,
        x="Phương pháp",
        y="silhouette",
        text_auto=".3f",
        labels={"silhouette": "Điểm Silhouette"},
    )
    figure.update_traces(marker_color=COLORS[0], textposition="outside", cliponaxis=False)
    figure.update_layout(height=340, xaxis_title=None, margin=dict(t=25, b=16, l=16, r=16))
    return figure


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
            "recency_days": "Ngày từ lần mua cuối",
            "frequency_orders": "Số đơn",
            "monetary_value": "Giá trị mua (thang log)",
            "segment_name": "Phân khúc",
        },
        title=f"Lần mua cuối và giá trị mua, tối đa {max_points:,} khách",
    )

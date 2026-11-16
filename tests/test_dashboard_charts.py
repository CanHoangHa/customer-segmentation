import pandas as pd

from app.charts import (
    customer_scatter,
    model_comparison_chart,
    monetary_share_chart,
    rfm_profile_chart,
    segment_size_chart,
)


def test_dashboard_charts_return_editable_plotly_figures() -> None:
    profiles = pd.DataFrame(
        {
            "method": ["kmeans", "kmeans"],
            "segment_id": ["S1", "S2"],
            "segment_name": ["K-Means S1", "K-Means S2"],
            "customer_pct": [40.0, 60.0],
            "monetary_share_pct": [70.0, 30.0],
            "median_recency_days": [20.0, 100.0],
            "median_frequency_orders": [4.0, 1.0],
            "median_monetary_value": [900.0, 100.0],
        }
    )
    segments = pd.DataFrame(
        {
            "method": ["kmeans", "kmeans"],
            "customer_id": ["private-1", "private-2"],
            "segment_name": ["K-Means S1", "K-Means S2"],
            "recency_days": [20, 100],
            "frequency_orders": [4, 1],
            "monetary_value": [900.0, 100.0],
        }
    )
    comparison = pd.DataFrame(
        {
            "status": ["ok"],
            "silhouette": [0.4],
            "method": ["kmeans"],
            "selected": [True],
            "actual_clusters": [2],
            "requested_clusters": [2],
            "smallest_segment_pct": [0.4],
            "median_fit_seconds": [0.2],
            "config_id": ["kmeans_k2"],
        }
    )
    figures = [
        segment_size_chart(profiles, "kmeans"),
        monetary_share_chart(profiles, "kmeans"),
        rfm_profile_chart(profiles, "kmeans"),
        customer_scatter(segments, "kmeans"),
        model_comparison_chart(comparison),
    ]
    assert all(figure.data for figure in figures)
    assert "private-1" not in figures[3].to_json()

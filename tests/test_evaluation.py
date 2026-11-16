import numpy as np
import pandas as pd

from src.segmentation.evaluation import (
    build_segment_profiles,
    candidate_quality,
    fixed_sample_indices,
    model_segment_rows,
    safe_silhouette,
    select_best_configs,
)
from tests.test_features import rfm_fixture


def test_fixed_sample_and_silhouette_are_reproducible() -> None:
    first = fixed_sample_indices(100, max_size=20, seed=42)
    second = fixed_sample_indices(100, max_size=20, seed=42)
    assert np.array_equal(first, second)
    features = np.column_stack([np.arange(100), np.arange(100), np.arange(100)])
    labels = np.repeat([0, 1], 50)
    assert safe_silhouette(features, labels, first) is not None


def test_selection_prefers_eligible_highest_silhouette() -> None:
    comparison = pd.DataFrame(
        [
            {
                "method": method,
                "config_id": f"{method}_bad",
                "status": "ok",
                "silhouette": 0.9,
                "eligible_for_selection": False,
                "requested_clusters": 3,
                "median_fit_seconds": 1.0,
            }
            for method in ("kmeans", "gmm", "birch")
        ]
        + [
            {
                "method": method,
                "config_id": f"{method}_good",
                "status": "ok",
                "silhouette": 0.5,
                "eligible_for_selection": True,
                "requested_clusters": 4,
                "median_fit_seconds": 2.0,
            }
            for method in ("kmeans", "gmm", "birch")
        ]
    )
    selected_table, selected = select_best_configs(comparison)
    assert selected == {method: f"{method}_good" for method in ("kmeans", "gmm", "birch")}
    assert selected_table["selected"].sum() == 3


def test_profiles_reconcile_customer_and_monetary_totals() -> None:
    customers = rfm_fixture().sort_values("customer_id").reset_index(drop=True)
    labels = np.array([0, 0, 1, 1, 2, 2])
    rows, mapping = model_segment_rows(customers, labels, "kmeans", "kmeans_k3")
    profiles = build_segment_profiles(rows)
    quality = candidate_quality(labels, minimum_segment_pct=0.1)
    assert set(mapping.values()) == {"S1", "S2", "S3"}
    assert profiles["customers"].sum() == len(customers)
    assert np.isclose(
        float(profiles["total_monetary_value"].sum()),
        float(customers["monetary_value"].sum()),
    )
    assert quality["actual_clusters"] == 3
    assert quality["eligible_for_selection"]

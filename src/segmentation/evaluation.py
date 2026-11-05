"""Comparable sampling, model selection, stable labels, and segment profiles."""

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import silhouette_score


METHOD_NAMES = {
    "rfm_threshold": "Ngưỡng RFM",
    "kmeans": "K-Means",
    "gmm": "Gaussian Mixture",
    "birch": "BIRCH",
}


def fixed_sample_indices(rows: int, max_size: int = 5_000, seed: int = 42) -> np.ndarray:
    if rows < 2:
        raise ValueError("Silhouette sampling requires at least two rows.")
    if max_size < 2:
        raise ValueError("Silhouette sample size must be at least two.")
    size = min(rows, max_size)
    if size == rows:
        return np.arange(rows, dtype="int64")
    return np.sort(np.random.default_rng(seed).choice(rows, size=size, replace=False))


def safe_silhouette(features: np.ndarray, labels: np.ndarray, indices: np.ndarray) -> float | None:
    sample_features = np.asarray(features)[indices]
    sample_labels = np.asarray(labels)[indices]
    unique = np.unique(sample_labels)
    if len(unique) < 2 or len(unique) >= len(sample_labels):
        return None
    return float(silhouette_score(sample_features, sample_labels, metric="euclidean"))


def candidate_quality(labels: np.ndarray, minimum_segment_pct: float) -> dict[str, Any]:
    counts = pd.Series(np.asarray(labels)).value_counts()
    actual = int(len(counts))
    smallest_pct = float(counts.min() / counts.sum()) if actual else 0.0
    return {
        "actual_clusters": actual,
        "smallest_segment_pct": smallest_pct,
        "eligible_for_selection": actual >= 2 and smallest_pct >= minimum_segment_pct,
    }


def select_best_configs(comparison: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    table = comparison.copy()
    table["selected"] = False
    selections: dict[str, str] = {}
    for method in ("kmeans", "gmm", "birch"):
        candidates = table[
            (table["method"] == method)
            & (table["status"] == "ok")
            & table["silhouette"].notna()
        ]
        eligible = candidates[candidates["eligible_for_selection"]]
        pool = eligible if not eligible.empty else candidates
        if pool.empty:
            raise RuntimeError(f"No valid {method} configuration is available for selection.")
        selected = pool.sort_values(
            ["silhouette", "requested_clusters", "median_fit_seconds", "config_id"],
            ascending=[False, True, True, True],
            kind="stable",
        ).iloc[0]
        config_id = str(selected["config_id"])
        selections[method] = config_id
        table.loc[table["config_id"] == config_id, "selected"] = True
    return table, selections


def remap_cluster_labels(
    customers: pd.DataFrame, labels: np.ndarray, method: str
) -> tuple[pd.Series, dict[int, str]]:
    frame = customers[["recency_days", "frequency_orders", "monetary_value"]].copy()
    frame["raw_label"] = np.asarray(labels, dtype="int32")
    ranking = (
        frame.groupby("raw_label", sort=False)
        .agg(
            median_recency_days=("recency_days", "median"),
            median_frequency_orders=("frequency_orders", "median"),
            median_monetary_value=("monetary_value", "median"),
            total_monetary_value=("monetary_value", "sum"),
        )
        .reset_index()
        .sort_values(
            [
                "total_monetary_value",
                "median_monetary_value",
                "median_frequency_orders",
                "median_recency_days",
                "raw_label",
            ],
            ascending=[False, False, False, True, True],
            kind="stable",
        )
    )
    mapping = {
        int(raw): f"S{index}"
        for index, raw in enumerate(ranking["raw_label"].tolist(), start=1)
    }
    remapped = frame["raw_label"].map(mapping).astype("string")
    remapped.name = "segment_id"
    return remapped, mapping


def model_segment_rows(
    customers: pd.DataFrame,
    labels: np.ndarray,
    method: str,
    config_id: str,
    membership_probability: np.ndarray | None = None,
) -> tuple[pd.DataFrame, dict[int, str]]:
    segment_ids, mapping = remap_cluster_labels(customers, labels, method)
    result = customers.copy()
    result["is_repeat_customer"] = result["frequency_orders"] >= 2
    result["method"] = method
    result["model_config_id"] = config_id
    result["segment_id"] = segment_ids
    method_name = METHOD_NAMES.get(method, method)
    result["segment_name"] = (method_name + " " + segment_ids).astype("string")
    if membership_probability is None:
        result["membership_probability"] = np.nan
    else:
        result["membership_probability"] = np.asarray(membership_probability, dtype="float64")
    return result[
        [
            "customer_id",
            "recency_days",
            "frequency_orders",
            "monetary_value",
            "last_purchase_at",
            "is_repeat_customer",
            "method",
            "model_config_id",
            "segment_id",
            "segment_name",
            "membership_probability",
        ]
    ], mapping


def build_segment_profiles(segments: pd.DataFrame) -> pd.DataFrame:
    required = {
        "customer_id",
        "recency_days",
        "frequency_orders",
        "monetary_value",
        "is_repeat_customer",
        "method",
        "segment_id",
        "segment_name",
    }
    missing = sorted(required.difference(segments.columns))
    if missing:
        raise ValueError(f"Segment rows are missing columns: {missing}")
    profiles = (
        segments.groupby(["method", "segment_id", "segment_name"], sort=True, observed=True)
        .agg(
            customers=("customer_id", "size"),
            median_recency_days=("recency_days", "median"),
            median_frequency_orders=("frequency_orders", "median"),
            median_monetary_value=("monetary_value", "median"),
            total_monetary_value=("monetary_value", "sum"),
            repeat_customers=("is_repeat_customer", "sum"),
        )
        .reset_index()
    )
    method_customers = profiles.groupby("method")["customers"].transform("sum")
    method_monetary = profiles.groupby("method")["total_monetary_value"].transform("sum")
    profiles["customer_pct"] = profiles["customers"] / method_customers * 100
    profiles["monetary_share_pct"] = (
        profiles["total_monetary_value"] / method_monetary * 100
    )
    profiles["repeat_customer_pct"] = (
        profiles["repeat_customers"] / profiles["customers"] * 100
    )
    return profiles[
        [
            "method",
            "segment_id",
            "segment_name",
            "customers",
            "customer_pct",
            "median_recency_days",
            "median_frequency_orders",
            "median_monetary_value",
            "total_monetary_value",
            "monetary_share_pct",
            "repeat_customers",
            "repeat_customer_pct",
        ]
    ]


def comparison_parameters(parameters: dict[str, Any]) -> str:
    return json.dumps(parameters, sort_keys=True, ensure_ascii=True)

"""Explainable threshold baseline built from ranked RFM values."""

import numpy as np
import pandas as pd

from src.segmentation.features import validate_rfm_frame


BASELINE_METHOD = "rfm_threshold"
SEGMENT_NAMES = {
    "champions": "Khách hàng nổi bật",
    "loyal": "Khách hàng trung thành",
    "high_value_at_risk": "Giá trị cao cần tái tương tác",
    "new_or_promising": "Khách hàng mới hoặc tiềm năng",
    "needs_attention": "Khách hàng cần quan tâm",
}


def quartile_score(values: pd.Series, higher_is_better: bool = True) -> pd.Series:
    """Assign 1-4 using percentile ranks while keeping equal values together."""
    numeric = pd.to_numeric(values, errors="raise")
    percentile = numeric.rank(method="average", pct=True)
    score = np.ceil(percentile * 4).clip(1, 4).astype("int8")
    if not higher_is_better:
        score = (5 - score).astype("int8")
    return score


def assign_segment_ids(scores: pd.DataFrame) -> pd.Series:
    """Apply mutually exclusive baseline rules in their documented priority order."""
    required = {"r_score", "f_score", "m_score"}
    missing = sorted(required.difference(scores.columns))
    if missing:
        raise ValueError(f"RFM score input is missing columns: {missing}")
    for name in required:
        if scores[name].isna().any() or not scores[name].between(1, 4).all():
            raise ValueError(f"{name} must contain only scores from 1 to 4.")

    champions = (scores["r_score"] >= 3) & (scores["f_score"] >= 3) & (scores["m_score"] >= 3)
    loyal = (scores["f_score"] >= 3) & (scores["r_score"] >= 2)
    high_value_at_risk = (scores["m_score"] >= 3) & (scores["r_score"] <= 2)
    new_or_promising = (scores["r_score"] >= 3) & (scores["f_score"] <= 2)
    ids = np.select(
        [champions, loyal, high_value_at_risk, new_or_promising],
        ["champions", "loyal", "high_value_at_risk", "new_or_promising"],
        default="needs_attention",
    )
    return pd.Series(ids, index=scores.index, dtype="string", name="segment_id")


def assign_rfm_baseline(frame: pd.DataFrame) -> pd.DataFrame:
    """Return one baseline segment row per customer using the final artifact schema."""
    customers = validate_rfm_frame(frame)
    scores = pd.DataFrame(index=customers.index)
    scores["r_score"] = quartile_score(customers["recency_days"], higher_is_better=False)
    scores["f_score"] = quartile_score(customers["frequency_orders"])
    scores["m_score"] = quartile_score(customers["monetary_value"])
    segment_ids = assign_segment_ids(scores)

    result = customers.copy()
    result["is_repeat_customer"] = result["frequency_orders"] >= 2
    result["method"] = BASELINE_METHOD
    result["segment_id"] = segment_ids
    result["segment_name"] = segment_ids.map(SEGMENT_NAMES).astype("string")
    result = pd.concat([result, scores], axis="columns")
    if result["segment_id"].isna().any() or result["segment_name"].isna().any():
        raise RuntimeError("Baseline failed to assign every customer to exactly one segment.")
    if result[["customer_id", "method"]].duplicated().any():
        raise RuntimeError("Baseline produced duplicate customer/method keys.")
    return result[
        [
            "customer_id",
            "recency_days",
            "frequency_orders",
            "monetary_value",
            "last_purchase_at",
            "is_repeat_customer",
            "method",
            "segment_id",
            "segment_name",
            "r_score",
            "f_score",
            "m_score",
        ]
    ]

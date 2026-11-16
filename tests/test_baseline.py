import pandas as pd

from src.segmentation.baseline import assign_rfm_baseline, assign_segment_ids, quartile_score
from tests.test_features import rfm_fixture


def test_quartile_score_keeps_tied_frequency_together() -> None:
    scores = quartile_score(pd.Series([1, 1, 1, 1, 2, 5]))
    assert scores.iloc[:4].nunique() == 1
    assert scores.between(1, 4).all()


def test_segment_precedence_and_fallback() -> None:
    scores = pd.DataFrame(
        {
            "r_score": [4, 3, 2, 4, 1],
            "f_score": [4, 4, 1, 1, 1],
            "m_score": [4, 2, 4, 1, 1],
        }
    )
    assert assign_segment_ids(scores).tolist() == [
        "champions",
        "loyal",
        "high_value_at_risk",
        "new_or_promising",
        "needs_attention",
    ]


def test_baseline_covers_every_customer_once() -> None:
    source = rfm_fixture()
    baseline = assign_rfm_baseline(source)
    assert len(baseline) == len(source)
    assert not baseline["segment_id"].isna().any()
    assert not baseline["segment_name"].isna().any()
    assert not baseline[["customer_id", "method"]].duplicated().any()
    assert baseline["method"].unique().tolist() == ["rfm_threshold"]
    assert baseline.loc[baseline["frequency_orders"] >= 2, "is_repeat_customer"].all()

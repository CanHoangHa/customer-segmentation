from decimal import Decimal

import numpy as np
import pandas as pd
import pytest

from src.segmentation.features import RFMContractError, prepare_features, validate_rfm_frame


def rfm_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "customer_id": ["300", "100", "200", "400", "500", "600"],
            "recency_days": [20, 1, 5, 40, 2, 10],
            "frequency_orders": [1, 8, 3, 1, 5, 2],
            "monetary_value": [
                Decimal("10.0000"),
                Decimal("1000.0000"),
                Decimal("200.0000"),
                Decimal("15.0000"),
                Decimal("500.0000"),
                Decimal("80.0000"),
            ],
            "last_purchase_at": pd.to_datetime(
                [
                    "2020-11-02T10:00:00Z",
                    "2020-11-21T10:00:00Z",
                    "2020-11-17T10:00:00Z",
                    "2020-10-13T10:00:00Z",
                    "2020-11-20T10:00:00Z",
                    "2020-11-12T10:00:00Z",
                ],
                utc=True,
            ),
        }
    )


def test_validate_rfm_normalizes_and_sorts() -> None:
    validated = validate_rfm_frame(rfm_fixture(), expected_rows=6)
    assert validated["customer_id"].tolist() == ["100", "200", "300", "400", "500", "600"]
    assert str(validated["recency_days"].dtype) == "int64"
    assert str(validated["frequency_orders"].dtype) == "int64"
    assert str(validated["monetary_value"].dtype) == "float64"
    assert str(validated["last_purchase_at"].dtype) == "datetime64[ns, UTC]"


@pytest.mark.parametrize(
    ("column", "value", "message"),
    [
        ("recency_days", -1, "non-negative whole days"),
        ("frequency_orders", 1.5, "positive whole order counts"),
        ("monetary_value", 0, "must be positive"),
        ("last_purchase_at", "not-a-date", "invalid or missing timestamps"),
    ],
)
def test_validate_rfm_rejects_invalid_values(column: str, value: object, message: str) -> None:
    frame = rfm_fixture()
    frame[column] = frame[column].astype("object")
    frame.loc[0, column] = value
    with pytest.raises(RFMContractError, match=message):
        validate_rfm_frame(frame)


def test_validate_rfm_rejects_duplicate_customers() -> None:
    frame = rfm_fixture()
    frame.loc[1, "customer_id"] = frame.loc[0, "customer_id"]
    with pytest.raises(RFMContractError, match="must be unique"):
        validate_rfm_frame(frame)


def test_validate_rfm_rejects_missing_columns_and_null_customer() -> None:
    with pytest.raises(RFMContractError, match="missing required columns"):
        validate_rfm_frame(rfm_fixture().drop(columns=["last_purchase_at"]))

    frame = rfm_fixture()
    frame["customer_id"] = frame["customer_id"].astype("object")
    frame.loc[0, "customer_id"] = None
    with pytest.raises(RFMContractError, match="contains null values"):
        validate_rfm_frame(frame)


def test_validate_rfm_checks_expected_customer_count() -> None:
    with pytest.raises(RFMContractError, match="expected 234,359"):
        validate_rfm_frame(rfm_fixture(), expected_rows=234_359)


def test_prepare_features_is_finite_centered_and_reproducible() -> None:
    first = prepare_features(rfm_fixture())
    second = prepare_features(rfm_fixture().sample(frac=1, random_state=7))
    assert first.metadata["feature_order"] == [
        "recency_days",
        "frequency_orders",
        "monetary_value",
    ]
    assert first.customers["customer_id"].tolist() == second.customers["customer_id"].tolist()
    assert np.isfinite(first.transformed).all()
    assert np.allclose(first.transformed.mean(axis=0), 0.0, atol=1e-12)
    assert np.allclose(first.transformed, second.transformed)

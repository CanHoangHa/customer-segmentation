"""Validate the RFM handoff and build one reproducible feature matrix."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


REQUIRED_RFM_COLUMNS = (
    "customer_id",
    "recency_days",
    "frequency_orders",
    "monetary_value",
    "last_purchase_at",
)
FEATURE_COLUMNS = ("recency_days", "frequency_orders", "monetary_value")


class RFMContractError(ValueError):
    """Raised when the RFM handoff cannot safely be used for modeling."""


@dataclass(frozen=True)
class FeatureSet:
    """Raw and transformed features kept in the same customer order."""

    customers: pd.DataFrame
    raw_features: pd.DataFrame
    transformed: np.ndarray
    scaler: StandardScaler
    metadata: dict[str, Any]


def _numeric_column(frame: pd.DataFrame, name: str) -> pd.Series:
    numeric = pd.to_numeric(frame[name], errors="coerce")
    invalid = numeric.isna() | ~np.isfinite(numeric.astype("float64"))
    if invalid.any():
        examples = frame.loc[invalid, name].head(3).tolist()
        raise RFMContractError(f"Column {name!r} has non-numeric values: {examples}")
    return numeric


def validate_rfm_frame(frame: pd.DataFrame, expected_rows: int | None = None) -> pd.DataFrame:
    """Return a sorted, normalized RFM frame or fail with a useful error."""
    if not isinstance(frame, pd.DataFrame):
        raise RFMContractError("RFM input must be a pandas DataFrame.")
    missing = [name for name in REQUIRED_RFM_COLUMNS if name not in frame.columns]
    if missing:
        raise RFMContractError(f"RFM input is missing required columns: {missing}")
    if frame.empty:
        raise RFMContractError("RFM input contains no customers.")
    if expected_rows is not None and len(frame) != expected_rows:
        raise RFMContractError(
            f"RFM input has {len(frame):,} customers; expected {expected_rows:,}."
        )

    normalized = frame.loc[:, REQUIRED_RFM_COLUMNS].copy()
    if pd.api.types.is_float_dtype(normalized["customer_id"]):
        raise RFMContractError(
            "customer_id was loaded as floating point and may have lost digits. Read it as text."
        )
    if normalized["customer_id"].isna().any():
        raise RFMContractError("customer_id contains null values.")
    normalized["customer_id"] = normalized["customer_id"].astype("string").str.strip()
    if (normalized["customer_id"] == "").any():
        raise RFMContractError("customer_id contains blank values.")
    duplicates = normalized["customer_id"].duplicated(keep=False)
    if duplicates.any():
        examples = normalized.loc[duplicates, "customer_id"].head(3).tolist()
        raise RFMContractError(f"customer_id must be unique; duplicates include {examples}")

    recency = _numeric_column(normalized, "recency_days")
    frequency = _numeric_column(normalized, "frequency_orders")
    monetary = _numeric_column(normalized, "monetary_value")
    if not np.equal(recency, np.floor(recency)).all() or (recency < 0).any():
        raise RFMContractError("recency_days must contain non-negative whole days.")
    if not np.equal(frequency, np.floor(frequency)).all() or (frequency < 1).any():
        raise RFMContractError("frequency_orders must contain positive whole order counts.")
    if (monetary <= 0).any():
        raise RFMContractError("monetary_value must be positive for every modeled customer.")

    purchase_time = pd.to_datetime(
        normalized["last_purchase_at"], errors="coerce", utc=True, format="mixed"
    )
    if purchase_time.isna().any():
        raise RFMContractError("last_purchase_at contains invalid or missing timestamps.")

    normalized["recency_days"] = recency.astype("int64")
    normalized["frequency_orders"] = frequency.astype("int64")
    normalized["monetary_value"] = monetary.astype("float64")
    normalized["last_purchase_at"] = purchase_time
    return normalized.sort_values("customer_id", kind="stable").reset_index(drop=True)


def load_rfm(path: str | Path, expected_rows: int | None = None) -> pd.DataFrame:
    """Read the Parquet handoff and apply the modeling contract."""
    source = Path(path)
    if not source.is_file():
        raise RFMContractError(f"RFM input does not exist: {source}")
    try:
        frame = pd.read_parquet(source, engine="pyarrow")
    except Exception as error:
        raise RFMContractError(f"Could not read RFM Parquet {source}: {error}") from error
    return validate_rfm_frame(frame, expected_rows=expected_rows)


def prepare_features(frame: pd.DataFrame) -> FeatureSet:
    """Apply log1p once, then standardize the shared RFM feature matrix."""
    customers = validate_rfm_frame(frame)
    raw = customers.loc[:, FEATURE_COLUMNS].astype("float64")
    logged = np.log1p(raw.to_numpy(copy=True))
    if not np.isfinite(logged).all():
        raise RFMContractError("log1p produced non-finite feature values.")

    scaler = StandardScaler()
    transformed = scaler.fit_transform(logged)
    constant_features = [
        name for name, scale in zip(FEATURE_COLUMNS, scaler.scale_, strict=True) if scale == 1.0
        and raw[name].nunique(dropna=False) == 1
    ]
    metadata: dict[str, Any] = {
        "rows": len(customers),
        "customer_order": "customer_id ascending",
        "feature_order": list(FEATURE_COLUMNS),
        "transform": "log1p",
        "scaler": "StandardScaler",
        "raw_min": {name: float(raw[name].min()) for name in FEATURE_COLUMNS},
        "raw_max": {name: float(raw[name].max()) for name in FEATURE_COLUMNS},
        "logged_mean": {
            name: float(value) for name, value in zip(FEATURE_COLUMNS, scaler.mean_, strict=True)
        },
        "logged_scale": {
            name: float(value) for name, value in zip(FEATURE_COLUMNS, scaler.scale_, strict=True)
        },
        "constant_features": constant_features,
    }
    return FeatureSet(
        customers=customers,
        raw_features=raw,
        transformed=transformed,
        scaler=scaler,
        metadata=metadata,
    )

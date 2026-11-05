"""Shared contracts and feature preparation for customer segmentation."""

from src.segmentation.baseline import assign_rfm_baseline
from src.segmentation.features import (
    FEATURE_COLUMNS,
    REQUIRED_RFM_COLUMNS,
    FeatureSet,
    RFMContractError,
    load_rfm,
    prepare_features,
    validate_rfm_frame,
)

__all__ = [
    "FEATURE_COLUMNS",
    "REQUIRED_RFM_COLUMNS",
    "FeatureSet",
    "RFMContractError",
    "assign_rfm_baseline",
    "load_rfm",
    "prepare_features",
    "validate_rfm_frame",
]

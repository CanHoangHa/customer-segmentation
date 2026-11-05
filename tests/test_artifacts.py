import json

import pandas as pd

from src.segmentation.pipeline import run_contract_pipeline
from tests.test_features import rfm_fixture


def test_contract_pipeline_writes_reusable_artifacts(tmp_path) -> None:
    source = tmp_path / "customer_rfm.parquet"
    output = tmp_path / "curated"
    reports = tmp_path / "reports"
    rfm_fixture().to_parquet(source, index=False, engine="pyarrow")

    summary = run_contract_pipeline(source, output, reports, expected_rows=6)
    saved = pd.read_parquet(output / "customer_segments.parquet", engine="pyarrow")
    metadata = json.loads((reports / "feature_metadata.json").read_text(encoding="utf-8"))
    saved_summary = json.loads((reports / "baseline_summary.json").read_text(encoding="utf-8"))

    assert summary == saved_summary
    assert len(saved) == 6
    assert not saved[["customer_id", "method"]].duplicated().any()
    assert saved["method"].unique().tolist() == ["rfm_threshold"]
    assert metadata["rows"] == 6
    assert metadata["feature_order"] == [
        "recency_days",
        "frequency_orders",
        "monetary_value",
    ]

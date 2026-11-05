import json

import numpy as np
import pandas as pd

from src.segmentation.pipeline import run_segmentation_pipeline


def synthetic_rfm(rows_per_cluster: int = 30) -> pd.DataFrame:
    random = np.random.default_rng(42)
    records = []
    reference = pd.Timestamp("2020-11-22", tz="UTC")
    centers = [(2, 8, 900), (20, 3, 250), (80, 1, 40)]
    customer = 1
    for recency, frequency, monetary in centers:
        for _ in range(rows_per_cluster):
            r_value = max(0, int(round(random.normal(recency, 1.5))))
            f_value = max(1, int(round(random.normal(frequency, 0.7))))
            m_value = max(1.0, float(random.normal(monetary, monetary * 0.08)))
            records.append(
                {
                    "customer_id": str(customer),
                    "recency_days": r_value,
                    "frequency_orders": f_value,
                    "monetary_value": m_value,
                    "last_purchase_at": reference - pd.to_timedelta(int(r_value), unit="D"),
                }
            )
            customer += 1
    return pd.DataFrame(records)


def test_full_pipeline_writes_selected_models_and_reconciled_profiles(tmp_path) -> None:
    source = tmp_path / "customer_rfm.parquet"
    output = tmp_path / "curated"
    reports = tmp_path / "reports"
    synthetic_rfm().to_parquet(source, index=False, engine="pyarrow")

    summary = run_segmentation_pipeline(
        source,
        output,
        reports,
        expected_rows=90,
        silhouette_sample_size=60,
        benchmark_repeats=1,
        minimum_segment_pct=0.01,
        k_values=(3,),
        birch_thresholds=(0.5,),
        warmup=False,
    )

    segments = pd.read_parquet(output / "customer_segments.parquet")
    profiles = pd.read_csv(reports / "segment_profiles.csv")
    comparison = pd.read_csv(reports / "model_comparison.csv")
    selection = json.loads((reports / "model_selection.json").read_text(encoding="utf-8"))
    metadata = json.loads((reports / "run_metadata.json").read_text(encoding="utf-8"))

    assert summary["methods"] == ["birch", "gmm", "kmeans", "rfm_threshold"]
    assert len(segments) == 90 * 4
    assert not segments[["customer_id", "method"]].duplicated().any()
    assert set(profiles["method"]) == set(summary["methods"])
    assert comparison["selected"].sum() == 4
    assert set(selection["selected"]) == set(summary["methods"])
    assert metadata["rows"] == 90
    assert metadata["reference_date"] == "2020-11-22"

import json

import pandas as pd

from app.data import crm_hypotheses, load_dashboard_data
from src.segmentation.pipeline import run_segmentation_pipeline
from tests.test_full_pipeline import synthetic_rfm


def dashboard_artifacts(root) -> None:
    (root / "data/processed").mkdir(parents=True)
    (root / "reports").mkdir(parents=True)
    source = root / "data/processed/customer_rfm.parquet"
    synthetic_rfm().to_parquet(source, index=False, engine="pyarrow")
    run_segmentation_pipeline(
        source,
        root / "data/curated",
        root / "reports",
        expected_rows=90,
        silhouette_sample_size=60,
        benchmark_repeats=1,
        k_values=(3,),
        birch_thresholds=(0.5,),
        warmup=False,
    )
    (root / "reports/cleaning_summary.json").write_text(
        json.dumps({"raw_rows": 100, "clean_rows": 90}), encoding="utf-8"
    )
    (root / "reports/rfm_summary.json").write_text(
        json.dumps({"reference_date": "2020-11-22"}), encoding="utf-8"
    )


def test_dashboard_loader_and_hypotheses_use_persisted_artifacts(tmp_path) -> None:
    dashboard_artifacts(tmp_path)
    data = load_dashboard_data(tmp_path)
    hypotheses = crm_hypotheses(data.profiles, "kmeans")
    assert data.segments["method"].nunique() == 4
    assert len(data.segments) == 90 * 4
    assert set(hypotheses.columns) == {
        "Phân khúc",
        "Quan sát",
        "Giả thuyết thử nghiệm",
        "KPI theo dõi",
        "Rủi ro",
    }
    assert len(hypotheses) == data.profiles[data.profiles["method"] == "kmeans"].shape[0]

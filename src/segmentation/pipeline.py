"""PR-one pipeline: validate RFM, prepare features, and write the baseline artifact."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from src.segmentation.baseline import assign_rfm_baseline
from src.segmentation.features import load_rfm, prepare_features


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_contract_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    report_dir: str | Path,
    expected_rows: int | None = None,
) -> dict[str, Any]:
    """Create the shared feature metadata and baseline rows used by later PRs."""
    source = Path(input_path)
    output = Path(output_dir)
    reports = Path(report_dir)
    output.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    rfm = load_rfm(source, expected_rows=expected_rows)
    features = prepare_features(rfm)
    baseline = assign_rfm_baseline(features.customers)

    artifact_path = output / "customer_segments.parquet"
    baseline.to_parquet(artifact_path, index=False, engine="pyarrow", compression="snappy")
    feature_metadata = {
        **features.metadata,
        "input_file": source.name,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(reports / "feature_metadata.json", feature_metadata)

    counts = baseline["segment_id"].value_counts().sort_index()
    repeat_customers = int(baseline["is_repeat_customer"].sum())
    summary: dict[str, Any] = {
        "method": "rfm_threshold",
        "customers": len(baseline),
        "output_rows": len(baseline),
        "repeat_customers": repeat_customers,
        "repeat_customer_pct": round(repeat_customers / len(baseline) * 100, 4),
        "segments": {name: int(value) for name, value in counts.items()},
        "artifact": artifact_path.as_posix(),
    }
    _write_json(reports / "baseline_summary.json", summary)
    return summary

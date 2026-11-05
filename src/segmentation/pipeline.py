"""Run the reproducible baseline and model comparison pipeline."""

from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from typing import Any

import numpy as np
import pandas as pd

from src.segmentation.baseline import assign_rfm_baseline
from src.segmentation.evaluation import (
    build_segment_profiles,
    candidate_quality,
    comparison_parameters,
    fixed_sample_indices,
    model_segment_rows,
    safe_silhouette,
    select_best_configs,
)
from src.segmentation.features import load_rfm, prepare_features
from src.segmentation.models import CandidateResult, build_candidate_specs, fit_candidate


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_commit(root: Path) -> str | None:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _reference_date(customers: pd.DataFrame) -> str:
    dates = (
        customers["last_purchase_at"].dt.normalize()
        + pd.to_timedelta(customers["recency_days"], unit="D")
    ).dt.date.unique()
    if len(dates) != 1:
        raise ValueError("RFM rows do not imply one shared reference date.")
    return dates[0].isoformat()


def _baseline_rows(baseline: pd.DataFrame) -> pd.DataFrame:
    result = baseline.copy()
    result["model_config_id"] = "rfm_threshold_5"
    result["membership_probability"] = np.nan
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
    ]


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


def run_segmentation_pipeline(
    input_path: str | Path,
    output_dir: str | Path,
    report_dir: str | Path,
    expected_rows: int | None = None,
    seed: int = 42,
    silhouette_sample_size: int = 5_000,
    benchmark_repeats: int = 3,
    minimum_segment_pct: float = 0.01,
    k_values: tuple[int, ...] = (3, 4, 5, 6),
    birch_thresholds: tuple[float, ...] = (0.3, 0.5, 0.7),
    warmup: bool = True,
) -> dict[str, Any]:
    """Fit all candidate methods, select one per method, and write dashboard artifacts."""
    source = Path(input_path)
    output = Path(output_dir)
    reports = Path(report_dir)
    output.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    rfm = load_rfm(source, expected_rows=expected_rows)
    feature_set = prepare_features(rfm)
    baseline = assign_rfm_baseline(feature_set.customers)
    sample_indices = fixed_sample_indices(
        len(feature_set.customers), max_size=silhouette_sample_size, seed=seed
    )

    baseline_labels, baseline_uniques = pd.factorize(baseline["segment_id"], sort=True)
    baseline_quality = candidate_quality(baseline_labels, minimum_segment_pct)
    comparison_rows: list[dict[str, Any]] = [
        {
            "method": "rfm_threshold",
            "config_id": "rfm_threshold_5",
            "requested_clusters": 5,
            **baseline_quality,
            "parameters": comparison_parameters(
                {"scoring": "percentile_rank_quartiles", "segments": 5}
            ),
            "silhouette": safe_silhouette(
                feature_set.transformed, baseline_labels, sample_indices
            ),
            "silhouette_sample_size": len(sample_indices),
            "fit_seconds_runs": "[]",
            "median_fit_seconds": 0.0,
            "model_metrics": comparison_parameters({"populated_segments": len(baseline_uniques)}),
            "status": "ok",
            "error": "",
            "primary_five_clusters": True,
        }
    ]
    results: dict[str, CandidateResult] = {}
    for spec in build_candidate_specs(k_values, birch_thresholds, seed=seed):
        try:
            result = fit_candidate(
                feature_set.transformed,
                spec,
                repeats=benchmark_repeats,
                warmup=warmup,
            )
            quality = candidate_quality(result.labels, minimum_segment_pct)
            comparison_rows.append(
                {
                    "method": spec.method,
                    "config_id": spec.config_id,
                    "requested_clusters": spec.requested_clusters,
                    **quality,
                    "parameters": comparison_parameters(spec.parameters),
                    "silhouette": safe_silhouette(
                        feature_set.transformed, result.labels, sample_indices
                    ),
                    "silhouette_sample_size": len(sample_indices),
                    "fit_seconds_runs": json.dumps(result.fit_seconds),
                    "median_fit_seconds": result.median_fit_seconds,
                    "model_metrics": comparison_parameters(result.metrics),
                    "status": "ok",
                    "error": "",
                    "primary_five_clusters": spec.requested_clusters == 5,
                }
            )
            results[spec.config_id] = result
        except Exception as error:
            comparison_rows.append(
                {
                    "method": spec.method,
                    "config_id": spec.config_id,
                    "requested_clusters": spec.requested_clusters,
                    "actual_clusters": 0,
                    "smallest_segment_pct": 0.0,
                    "eligible_for_selection": False,
                    "parameters": comparison_parameters(spec.parameters),
                    "silhouette": np.nan,
                    "silhouette_sample_size": len(sample_indices),
                    "fit_seconds_runs": "[]",
                    "median_fit_seconds": np.nan,
                    "model_metrics": "{}",
                    "status": "failed",
                    "error": f"{type(error).__name__}: {error}",
                    "primary_five_clusters": spec.requested_clusters == 5,
                }
            )

    comparison, selections = select_best_configs(pd.DataFrame(comparison_rows))
    comparison.loc[comparison["method"] == "rfm_threshold", "selected"] = True

    segment_frames = [_baseline_rows(baseline)]
    mappings: dict[str, dict[str, str]] = {}
    for method, config_id in selections.items():
        result = results[config_id]
        rows, mapping = model_segment_rows(
            feature_set.customers,
            result.labels,
            method,
            config_id,
            membership_probability=result.membership_probability,
        )
        segment_frames.append(rows)
        mappings[method] = {str(raw): stable for raw, stable in mapping.items()}
    segments = pd.concat(segment_frames, ignore_index=True)
    if segments[["customer_id", "method"]].duplicated().any():
        raise RuntimeError("Selected model artifacts contain duplicate customer/method keys.")
    expected_methods = 1 + len(selections)
    if len(segments) != len(rfm) * expected_methods:
        raise RuntimeError("Selected model artifacts lost or duplicated customers.")

    profiles = build_segment_profiles(segments)
    expected_total = float(feature_set.customers["monetary_value"].sum())
    for method, group in profiles.groupby("method"):
        if int(group["customers"].sum()) != len(rfm):
            raise RuntimeError(f"Profile customer total does not reconcile for {method}.")
        if not np.isclose(group["total_monetary_value"].sum(), expected_total, rtol=1e-12):
            raise RuntimeError(f"Profile monetary total does not reconcile for {method}.")

    segments.to_parquet(
        output / "customer_segments.parquet",
        index=False,
        engine="pyarrow",
        compression="snappy",
    )
    profiles.to_csv(reports / "segment_profiles.csv", index=False, encoding="utf-8-sig")
    comparison.to_csv(reports / "model_comparison.csv", index=False, encoding="utf-8-sig")

    selection_payload = {
        "criterion": (
            "Highest silhouette among configurations with at least two clusters and minimum "
            f"segment share >= {minimum_segment_pct:.2%}; fallback to any valid silhouette."
        ),
        "selected": {"rfm_threshold": "rfm_threshold_5", **selections},
        "stable_label_mappings": mappings,
    }
    _write_json(reports / "model_selection.json", selection_payload)

    root = Path(__file__).resolve().parents[2]
    metadata = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(root),
        "input_file": source.name,
        "input_sha256": _sha256(source),
        "rows": len(rfm),
        "reference_date": _reference_date(feature_set.customers),
        "seed": seed,
        "silhouette_sample_size": len(sample_indices),
        "silhouette_sample_indices_sha256": hashlib.sha256(
            sample_indices.astype("int64").tobytes()
        ).hexdigest(),
        "benchmark_repeats": benchmark_repeats,
        "warmup": warmup,
        "minimum_segment_pct": minimum_segment_pct,
        "features": feature_set.metadata,
        "environment": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "cpu_count": os.cpu_count(),
            "numpy": version("numpy"),
            "pandas": version("pandas"),
            "pyarrow": version("pyarrow"),
            "scikit_learn": version("scikit-learn"),
        },
    }
    _write_json(reports / "run_metadata.json", metadata)
    _write_json(reports / "feature_metadata.json", feature_set.metadata)

    return {
        "customers": len(rfm),
        "methods": sorted(segments["method"].unique().tolist()),
        "selected": selection_payload["selected"],
        "candidate_configurations": len(comparison),
        "failed_configurations": int((comparison["status"] == "failed").sum()),
    }

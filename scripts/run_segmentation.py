"""Validate customer RFM and create the baseline segmentation contract."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.segmentation.pipeline import run_contract_pipeline, run_segmentation_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate customer RFM, compare threshold RFM with K-Means, GMM and BIRCH, "
            "then write selected segment artifacts."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "data/processed/customer_rfm.parquet",
        help="RFM Parquet produced by scripts/run_pipeline.py.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data/curated",
        help="Directory for customer_segments.parquet.",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=ROOT / "reports",
        help="Directory for feature and baseline metadata.",
    )
    parser.add_argument(
        "--expected-rows",
        type=int,
        default=None,
        help="Optional exact customer count used as an additional handoff check.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Shared random seed.")
    parser.add_argument(
        "--silhouette-sample-size",
        type=int,
        default=5_000,
        help="Maximum size of the fixed Silhouette sample.",
    )
    parser.add_argument(
        "--benchmark-repeats",
        type=int,
        default=3,
        help="Measured fit_predict runs after one warmup.",
    )
    parser.add_argument(
        "--minimum-segment-pct",
        type=float,
        default=0.01,
        help="Minimum segment share preferred during model selection.",
    )
    parser.add_argument(
        "--baseline-only",
        action="store_true",
        help="Validate features and write only the threshold RFM baseline.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    if arguments.baseline_only:
        result = run_contract_pipeline(
            arguments.input,
            arguments.output_dir,
            arguments.report_dir,
            expected_rows=arguments.expected_rows,
        )
        print(
            f"Baseline complete: {result['customers']:,} customers, "
            f"{len(result['segments'])} populated segments."
        )
    else:
        result = run_segmentation_pipeline(
            arguments.input,
            arguments.output_dir,
            arguments.report_dir,
            expected_rows=arguments.expected_rows,
            seed=arguments.seed,
            silhouette_sample_size=arguments.silhouette_sample_size,
            benchmark_repeats=arguments.benchmark_repeats,
            minimum_segment_pct=arguments.minimum_segment_pct,
        )
        print(
            f"Segmentation complete: {result['customers']:,} customers, "
            f"{len(result['methods'])} methods, "
            f"{result['failed_configurations']} failed configurations."
        )

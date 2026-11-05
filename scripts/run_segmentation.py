"""Validate customer RFM and create the baseline segmentation contract."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.segmentation.pipeline import run_contract_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate customer RFM, prepare shared features, and write the RFM baseline."
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
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
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

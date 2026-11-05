"""Build model-ready RFM without a Spark worker on constrained Windows runners."""

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.portable_rfm import build_portable_rfm


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compatibility runner that mirrors the accepted Spark cleaning and RFM rules."
    )
    parser.add_argument("--input", type=Path, default=ROOT / "data/raw/kz.csv")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data/processed")
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--skip-report-check", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    result = build_portable_rfm(
        arguments.input,
        arguments.output_dir,
        arguments.report_dir,
        verify_committed_reports=not arguments.skip_report_check,
    )
    print(
        f"Portable RFM complete: {result['clean_rows']:,} valid rows, "
        f"{result['customers']:,} customers, reference date {result['reference_date']}."
    )

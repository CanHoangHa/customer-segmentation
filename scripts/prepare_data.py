"""Run purchase cleaning from the repository root."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.prepare_data import prepare_data, start_spark


if __name__ == "__main__":
    spark = start_spark()
    try:
        clean, report = prepare_data(
            spark, ROOT / "data/raw/kz.csv", ROOT / "data/interim/purchases_normalized.csv",
            ROOT / "data/processed", ROOT / "reports",
        )
        print(f"Accepted: {report['clean_rows']:,}; rejected: {report['quarantine_rows']:,}")
        clean.unpersist()
    finally:
        spark.stop()

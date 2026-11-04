"""Build RFM from the cleaned Parquet file."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.prepare_data import start_spark
from src.rfm import save_rfm


if __name__ == "__main__":
    spark = start_spark()
    try:
        purchases = spark.read.parquet(str(ROOT / "data/processed/purchases_clean.parquet"))
        report = save_rfm(purchases, ROOT / "data/processed", ROOT / "reports")
        print(f"Customers: {report['customers']:,}; reference date: {report['reference_date']}")
    finally:
        spark.stop()

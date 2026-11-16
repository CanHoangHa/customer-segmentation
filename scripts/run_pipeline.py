"""Clean purchases, build RFM, and check three customer examples."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.prepare_data import prepare_data, start_spark
from src.rfm import check_rfm, save_rfm


if __name__ == "__main__":
    spark = start_spark()
    try:
        clean, cleaning = prepare_data(
            spark, ROOT / "data/raw/kz.csv", ROOT / "data/processed", ROOT / "reports",
        )
        print(f"Accepted: {cleaning['clean_rows']:,}; rejected: {cleaning['quarantine_rows']:,}")
        rfm = save_rfm(clean, ROOT / "data/processed", ROOT / "reports")
        print(f"Customers: {rfm['customers']:,}; reference date: {rfm['reference_date']}")
        checks = check_rfm(spark, clean, ROOT / "data/processed", ROOT / "reports")
        print(f"RFM checks passed for {len(checks)} customers.")
        clean.unpersist()
    finally:
        spark.stop()

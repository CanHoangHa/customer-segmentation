"""Build one RFM record per customer from valid purchases."""

from datetime import date, timedelta
import json

from pyspark.sql import functions as F

from src.prepare_data import write_parquet


def build_rfm(purchases, reference_date=None):
    latest_date = purchases.agg(F.max(F.to_date("event_time"))).first()[0]
    if latest_date is None:
        raise ValueError("RFM requires at least one valid purchase.")
    if reference_date is None:
        reference_date = (latest_date + timedelta(days=1)).isoformat()
    if date.fromisoformat(reference_date) <= latest_date:
        raise ValueError("The reference date must be after the latest purchase date.")

    rfm = purchases.groupBy("customer_id").agg(
        F.max("event_time").alias("last_purchase_at"),
        F.countDistinct("order_id").alias("frequency_orders"),
        F.sum("price").alias("monetary_value"),
    )
    rfm = rfm.withColumn(
        "recency_days", F.datediff(F.lit(reference_date).cast("date"), F.to_date("last_purchase_at"))
    )
    return rfm.select(
        "customer_id", "recency_days", "frequency_orders", "monetary_value", "last_purchase_at"
    ), reference_date


def save_rfm(purchases, output_dir, report_dir):
    rfm, reference_date = build_rfm(purchases)
    rfm = rfm.cache()
    totals = rfm.agg(
        F.count("customer_id").alias("customers"),
        F.sum((F.col("frequency_orders") >= 2).cast("long")).alias("repeat_customers"),
        F.sum("frequency_orders").alias("orders"),
        F.sum("monetary_value").alias("monetary_value"),
    ).first()
    purchase_total = purchases.agg(F.sum("price")).first()[0]
    if totals["monetary_value"] != purchase_total:
        raise ValueError("The RFM monetary total does not match valid purchases.")
    write_parquet(rfm, output_dir / "customer_rfm.parquet")

    # Keep a comparison dataset using only the originally complete rows.
    original_rfm, _ = build_rfm(purchases.filter("row_status = 'full_width'"), reference_date)
    write_parquet(original_rfm, output_dir / "customer_rfm_original_rows.parquet")

    report = {
        "reference_date": reference_date,
        "timezone": "UTC",
        "customers": totals["customers"],
        "orders": totals["orders"],
        "repeat_customers": totals["repeat_customers"],
        "repeat_customer_pct": round(totals["repeat_customers"] / totals["customers"] * 100, 4),
        "monetary_value": str(totals["monetary_value"]),
        "monetary_reconciles": True,
        "money_unit": "Source price units; not accounting revenue or profit.",
    }
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "rfm_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    rfm.unpersist()
    return report

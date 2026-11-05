"""Build one RFM record per customer from valid purchases."""

import csv
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


def check_rfm(spark, purchases, output_dir, report_dir):
    """Calculate RFM independently for three customers using their clean lines."""
    saved = spark.read.parquet(str(output_dir / "customer_rfm.parquet"))
    candidates = (
        saved.orderBy(F.desc("frequency_orders"), "customer_id").select("customer_id").take(1)
        + saved.filter("frequency_orders = 1").orderBy("customer_id").select("customer_id").take(1)
        + purchases.filter("row_status = 'repaired_6_fields'").orderBy("source_record").select("customer_id").take(1)
        + saved.orderBy("customer_id").select("customer_id").take(3)
    )
    customer_ids = list(dict.fromkeys(row.customer_id for row in candidates))[:3]
    summary = json.loads((report_dir / "rfm_summary.json").read_text(encoding="utf-8"))
    reference_date = date.fromisoformat(summary["reference_date"])
    purchase_lines = purchases.filter(F.col("customer_id").isin(customer_ids)).select(
        "customer_id", "order_id", F.to_date("event_time").alias("purchase_date"), "price"
    ).collect()

    results = []
    for row in saved.filter(F.col("customer_id").isin(customer_ids)).orderBy("customer_id").collect():
        lines = [line for line in purchase_lines if line.customer_id == row.customer_id]
        recency = (reference_date - max(line.purchase_date for line in lines)).days
        frequency = len({line.order_id for line in lines})
        monetary = sum(line.price for line in lines)
        results.append({
            "customer_id": row.customer_id,
            "manual_R": recency, "saved_R": row.recency_days,
            "manual_F": frequency, "saved_F": row.frequency_orders,
            "manual_M": str(monetary), "saved_M": str(row.monetary_value),
            "matched": (recency, frequency, monetary) == (row.recency_days, row.frequency_orders, row.monetary_value),
        })

    with (report_dir / "rfm_hand_check.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(results[0]))
        writer.writeheader()
        writer.writerows(results)
    if not all(row["matched"] for row in results):
        raise ValueError("An independent RFM calculation does not match the saved result.")
    return results

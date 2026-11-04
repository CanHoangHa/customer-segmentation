"""Compare three saved RFM records with calculations from the original CSV."""

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
import csv
import json
import re

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


def check_rfm():
    rfm = pd.read_parquet(ROOT / "data/processed/customer_rfm.parquet")
    repaired = pd.read_parquet(
        ROOT / "data/processed/purchases_clean.parquet",
        columns=["customer_id"], filters=[("row_status", "=", "repaired_6_fields")],
    )
    candidates = (
        rfm.sort_values("frequency_orders", ascending=False)["customer_id"].head(1).tolist()
        + rfm.loc[rfm["frequency_orders"] == 1, "customer_id"].head(1).tolist()
        + repaired["customer_id"].head(1).tolist()
        + rfm["customer_id"].head(3).tolist()
    )
    customer_ids = list(dict.fromkeys(candidates))[:3]
    manual = {customer: {"orders": set(), "dates": [], "money": Decimal("0")} for customer in customer_ids}
    reference_date = date.fromisoformat(json.loads((ROOT / "reports/rfm_summary.json").read_text())["reference_date"])

    with (ROOT / "data/raw/kz.csv").open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream)
        next(reader)
        for values in reader:
            values = [value.strip() for value in values]
            if len(values) == 8:
                event, order, price, customer = values[0], values[1], values[6], values[7]
            elif len(values) == 6 and values[3] == "" and re.fullmatch(r"-?\d+(\.\d+)?", values[4]) and (values[5] == "" or values[5].isdigit()):
                event, order, price, customer = values[0], values[1], values[4], values[5]
            else:
                continue
            if customer not in manual or not order.isdigit() or not re.fullmatch(r"-?\d+(\.\d{1,4})?", price):
                continue
            try:
                purchase_date = datetime.strptime(event, "%Y-%m-%d %H:%M:%S UTC").date()
            except ValueError:
                continue
            if purchase_date.year != 2020 or Decimal(price) <= 0:
                continue
            manual[customer]["orders"].add(order)
            manual[customer]["dates"].append(purchase_date)
            manual[customer]["money"] += Decimal(price)

    records = []
    for customer in customer_ids:
        saved = rfm.loc[rfm["customer_id"] == customer].iloc[0]
        expected = manual[customer]
        recency = (reference_date - max(expected["dates"])).days
        frequency = len(expected["orders"])
        matched = (recency == saved["recency_days"] and frequency == saved["frequency_orders"]
                   and expected["money"] == saved["monetary_value"])
        records.append({"customer_id": customer, "manual_R": recency, "saved_R": saved["recency_days"],
                        "manual_F": frequency, "saved_F": saved["frequency_orders"],
                        "manual_M": str(expected["money"]), "saved_M": str(saved["monetary_value"]),
                        "matched": matched})
    pd.DataFrame(records).to_csv(ROOT / "reports/rfm_hand_check.csv", index=False, encoding="utf-8-sig")
    if not all(record["matched"] for record in records):
        raise ValueError("A manual RFM calculation does not match the saved result.")
    print(f"Manual RFM checks passed for {len(records)} customers.")


if __name__ == "__main__":
    check_rfm()

"""Streaming compatibility runner for environments where a PySpark worker cannot start.

The project remains PySpark-first. This module mirrors the accepted row rules so model and
dashboard work can proceed on constrained Windows runners, and verifies its totals against the
committed Spark reports when requested.
"""

from collections import Counter
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import re
from typing import Iterator

import pyarrow as pa
import pyarrow.parquet as pq

from src.prepare_data import COLUMNS


ID_PATTERN = re.compile(r"^[0-9]+$")
PRICE_PATTERN = re.compile(r"^-?[0-9]+(?:\.[0-9]{1,4})?$")


def _align(fields: list[str]) -> tuple[str, list[str | None] | None]:
    values = [value.strip() for value in fields]
    if len(values) == 8:
        return "full_width", [value or None for value in values]
    if (
        len(values) == 6
        and values[3] == ""
        and PRICE_PATTERN.fullmatch(values[4])
        and (values[5] == "" or ID_PATTERN.fullmatch(values[5]))
    ):
        repaired = values[:3] + [None, None, None, values[4] or None, values[5] or None]
        return "repaired_6_fields", repaired
    return "unmatched_structure", None


def _rows(source: Path) -> Iterator[tuple[int, int, str, list[str | None] | None]]:
    with source.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, None)
        if header != COLUMNS:
            raise ValueError("The input columns do not match the dataset schema.")
        for source_record, fields in enumerate(reader, start=1):
            status, aligned = _align(fields)
            yield source_record, len(fields), status, aligned


def find_conflicting_orders(source: Path) -> tuple[set[str], Counter]:
    owners: dict[str, str] = {}
    conflicts: set[str] = set()
    structure = Counter()
    for _, field_count, status, aligned in _rows(source):
        structure[field_count] += 1
        if aligned is None:
            continue
        order_id, customer_id = aligned[1], aligned[7]
        if not order_id or not customer_id:
            continue
        if not ID_PATTERN.fullmatch(order_id) or not ID_PATTERN.fullmatch(customer_id):
            continue
        previous = owners.setdefault(order_id, customer_id)
        if previous != customer_id:
            conflicts.add(order_id)
    return conflicts, structure


def _validate(
    status: str,
    aligned: list[str | None] | None,
    conflicts: set[str],
    year: int,
) -> tuple[str | None, datetime | None, Decimal | None]:
    if status == "unmatched_structure" or aligned is None:
        return "unmatched_structure", None, None
    event_raw, order_id, _, _, _, _, price_raw, customer_id = aligned
    if order_id is None:
        return "missing_order_id", None, None
    if not ID_PATTERN.fullmatch(order_id):
        return "invalid_order_id", None, None
    if customer_id is None:
        return "missing_customer_id", None, None
    if not ID_PATTERN.fullmatch(customer_id):
        return "invalid_customer_id", None, None
    try:
        event_time = datetime.strptime(event_raw or "", "%Y-%m-%d %H:%M:%S UTC").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        return "invalid_date", None, None
    if event_time.year != year:
        return "date_outside_scope", event_time, None
    if price_raw is None or not PRICE_PATTERN.fullmatch(price_raw):
        return "invalid_price", event_time, None
    price = Decimal(price_raw).quantize(Decimal("0.0001"))
    if price <= 0:
        return "nonpositive_price", event_time, price
    if order_id in conflicts:
        return "conflicting_order", event_time, price
    return None, event_time, price


def _clean_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("source_record", pa.int64()),
            pa.field("row_status", pa.string()),
            pa.field("event_time", pa.timestamp("us", tz="UTC")),
            pa.field("order_id", pa.string()),
            pa.field("product_id", pa.string()),
            pa.field("category_id", pa.string()),
            pa.field("category_code", pa.string()),
            pa.field("brand", pa.string()),
            pa.field("price", pa.decimal128(20, 4)),
            pa.field("customer_id", pa.string()),
        ]
    )


def _rfm_schema() -> pa.Schema:
    return pa.schema(
        [
            pa.field("customer_id", pa.string()),
            pa.field("recency_days", pa.int32()),
            pa.field("frequency_orders", pa.int64()),
            pa.field("monetary_value", pa.decimal128(30, 4)),
            pa.field("last_purchase_at", pa.timestamp("us", tz="UTC")),
        ]
    )


def _write_rfm(path: Path, states: dict[str, dict], reference_date) -> dict:
    schema = _rfm_schema()
    customers = 0
    repeat_customers = 0
    orders = 0
    monetary = Decimal("0.0000")
    batch: list[dict] = []
    with pq.ParquetWriter(path, schema, compression="snappy") as writer:
        for customer_id in sorted(states):
            state = states[customer_id]
            frequency = len(state["orders"])
            record = {
                "customer_id": customer_id,
                "recency_days": (reference_date - state["last_purchase"].date()).days,
                "frequency_orders": frequency,
                "monetary_value": state["monetary"],
                "last_purchase_at": state["last_purchase"],
            }
            batch.append(record)
            customers += 1
            repeat_customers += int(frequency >= 2)
            orders += frequency
            monetary += state["monetary"]
            if len(batch) >= 25_000:
                writer.write_table(pa.Table.from_pylist(batch, schema=schema))
                batch.clear()
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, schema=schema))
    return {
        "customers": customers,
        "orders": orders,
        "repeat_customers": repeat_customers,
        "repeat_customer_pct": round(repeat_customers / customers * 100, 4),
        "monetary_value": str(monetary),
    }


def _add_state(states: dict[str, dict], customer: str, order: str, event: datetime, price: Decimal):
    state = states.setdefault(
        customer,
        {"last_purchase": event, "orders": set(), "monetary": Decimal("0.0000")},
    )
    state["last_purchase"] = max(state["last_purchase"], event)
    state["orders"].add(order)
    state["monetary"] += price


def build_portable_rfm(
    source: str | Path,
    output_dir: str | Path,
    report_dir: str | Path,
    year: int = 2020,
    verify_committed_reports: bool = True,
) -> dict:
    source_path = Path(source)
    output = Path(output_dir)
    reports = Path(report_dir)
    output.mkdir(parents=True, exist_ok=True)
    reports.mkdir(parents=True, exist_ok=True)

    conflicts, structure = find_conflicting_orders(source_path)
    states: dict[str, dict] = {}
    original_states: dict[str, dict] = {}
    reasons = Counter()
    repaired_count = 0
    latest = None
    clean_batch: list[dict] = []
    clean_path = output / "purchases_clean.parquet"
    schema = _clean_schema()
    with pq.ParquetWriter(clean_path, schema, compression="snappy") as writer:
        for source_record, _, status, aligned in _rows(source_path):
            reason, event_time, price = _validate(status, aligned, conflicts, year)
            reasons[reason or "accepted"] += 1
            if reason is not None:
                continue
            assert aligned is not None and event_time is not None and price is not None
            order_id = aligned[1]
            customer_id = aligned[7]
            assert order_id is not None and customer_id is not None
            record = {
                "source_record": source_record,
                "row_status": status,
                "event_time": event_time,
                "order_id": order_id,
                "product_id": aligned[2],
                "category_id": aligned[3],
                "category_code": aligned[4],
                "brand": aligned[5],
                "price": price,
                "customer_id": customer_id,
            }
            clean_batch.append(record)
            if len(clean_batch) >= 25_000:
                writer.write_table(pa.Table.from_pylist(clean_batch, schema=schema))
                clean_batch.clear()
            _add_state(states, customer_id, order_id, event_time, price)
            if status == "full_width":
                _add_state(original_states, customer_id, order_id, event_time, price)
            repaired_count += int(status == "repaired_6_fields")
            latest = event_time if latest is None else max(latest, event_time)
        if clean_batch:
            writer.write_table(pa.Table.from_pylist(clean_batch, schema=schema))

    if latest is None:
        raise ValueError("No valid purchases were available for RFM.")
    reference_date = latest.date() + timedelta(days=1)
    rfm = _write_rfm(output / "customer_rfm.parquet", states, reference_date)
    _write_rfm(output / "customer_rfm_original_rows.parquet", original_states, reference_date)
    raw_rows = sum(reasons.values())
    summary = {
        "source_file": source_path.name,
        "year": year,
        "raw_rows": raw_rows,
        "clean_rows": reasons["accepted"],
        "quarantine_rows": raw_rows - reasons["accepted"],
        "accepted_repaired_rows": repaired_count,
        "rows_by_primary_reason": dict(reasons),
        "conflicting_orders": len(conflicts),
        "row_structure": {str(key): value for key, value in sorted(structure.items())},
        "reference_date": reference_date.isoformat(),
        **rfm,
        "runner": "portable_python_compatibility",
    }

    if verify_committed_reports:
        cleaning_expected = json.loads(
            (reports / "cleaning_summary.json").read_text(encoding="utf-8")
        )
        rfm_expected = json.loads((reports / "rfm_summary.json").read_text(encoding="utf-8"))
        checks = {
            "raw_rows": cleaning_expected["raw_rows"],
            "clean_rows": cleaning_expected["clean_rows"],
            "quarantine_rows": cleaning_expected["quarantine_rows"],
            "accepted_repaired_rows": cleaning_expected["accepted_repaired_rows"],
            "customers": rfm_expected["customers"],
            "orders": rfm_expected["orders"],
            "repeat_customers": rfm_expected["repeat_customers"],
            "monetary_value": rfm_expected["monetary_value"],
            "reference_date": rfm_expected["reference_date"],
        }
        mismatches = {
            key: {"expected": expected, "actual": summary[key]}
            for key, expected in checks.items()
            if str(summary[key]) != str(expected)
        }
        if mismatches:
            raise ValueError(f"Portable output does not match committed Spark reports: {mismatches}")
        summary["matched_committed_spark_reports"] = True

    (reports / "portable_run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary

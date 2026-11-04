import csv
from decimal import Decimal

import pyarrow.parquet as pq
import pytest

from src.prepare_data import COLUMNS, align_record, clean_purchases, normalize_csv, read_normalized, start_spark, validate_purchases, write_parquet
from src.rfm import build_rfm


@pytest.fixture(scope="session")
def spark():
    session = start_spark()
    yield session
    session.stop()


def test_short_row_repair():
    values, status = align_record(["2020-11-21 10:00:00 UTC", "101", "1", "", "20.00", "1515915625453675584"])
    assert status == "repaired_6_fields"
    assert values[3:6] == ["", "", ""]
    assert values[6:] == ["20.00", "1515915625453675584"]
    values, status = align_record(["2020-11-21 10:00:00 UTC", "101", "1", "", "20", ""])
    assert status == "repaired_6_fields"
    assert values[-1] == ""
    for fourth, price, customer in [("unexpected", "20", "123"), ("", "unknown", "123"), ("", "20", "not-an-id")]:
        _, status = align_record(["2020-11-21 10:00:00 UTC", "101", "1", fourth, price, customer])
        assert status == "unmatched_structure"


def test_validation_and_parquet_round_trip(spark, tmp_path):
    customer = "1515915625453675584"
    rows = [
        ["2020-11-20 10:00:00 UTC", "100", "1", "", "", "", "10.00", customer],
        ["2020-11-20 10:00:00 UTC", "100", "1", "", "", "", "10.00", customer],
        ["2020-11-21 10:00:00 UTC", "101", "1", "", "20.00", customer],
        ["2020-11-21 10:00:00 UTC", "102", "1", "", "", "", "10", ""],
        ["1970-01-01 00:00:00 UTC", "103", "1", "", "", "", "10", customer],
        ["2020-11-21 10:00:00 UTC", "104", "1", "", "", "", "0", customer],
        ["2020-11-21 10:00:00 UTC", "900", "1", "", "", "", "10", customer],
        ["2020-11-21 10:00:00 UTC", "900", "1", "", "", "", "10", "200"],
        ["2020-11-21 10:00:00 UTC", "105", "1", "not-empty", "10", customer],
    ]
    source = tmp_path / "source.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    original_bytes = source.read_bytes()
    normalized = tmp_path / "normalized.csv"
    normalize_csv(source, normalized)
    validated = validate_purchases(read_normalized(spark, normalized)).cache()
    clean = clean_purchases(validated)
    assert clean.count() == 3
    assert validated.filter("rejection_reason is not null").count() == 6
    reasons = {row.rejection_reason: row["count"] for row in validated.groupBy("rejection_reason").count().collect()}
    assert reasons["conflicting_order"] == 2
    assert reasons["missing_customer_id"] == 1
    assert reasons["unmatched_structure"] == 1
    output = tmp_path / "clean.parquet"
    write_parquet(clean, output, batch_size=2)
    saved = pq.read_table(output)
    assert saved.num_rows == 3
    assert sum(saved.column("price").to_pylist()) == Decimal("40.0000")
    assert set(saved.column("customer_id").to_pylist()) == {customer}
    assert saved.column("event_time").to_pylist()[0].utcoffset().total_seconds() == 0
    assert source.read_bytes() == original_bytes
    validated.unpersist()


def test_rfm_matches_hand_calculation(spark, tmp_path):
    rows = [
        ["2020-11-20 10:00:00 UTC", "100", "1", "", "", "", "10.00", "101"],
        ["2020-11-20 10:00:00 UTC", "100", "2", "", "", "", "5.00", "101"],
        ["2020-11-20 10:00:00 UTC", "100", "1", "", "", "", "10.00", "101"],
        ["2020-11-21 10:00:00 UTC", "101", "1", "", "20.00", "101"],
        ["2020-11-19 10:00:00 UTC", "102", "1", "", "", "", "8.50", "202"],
    ]
    source = tmp_path / "source.csv"
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    normalized = tmp_path / "normalized.csv"
    normalize_csv(source, normalized)
    clean = clean_purchases(validate_purchases(read_normalized(spark, normalized)))
    rfm, reference_date = build_rfm(clean)
    actual = {row.customer_id: row for row in rfm.collect()}
    assert reference_date == "2020-11-22"
    assert (actual["101"].recency_days, actual["101"].frequency_orders, actual["101"].monetary_value) == (1, 2, Decimal("45.0000"))
    assert (actual["202"].recency_days, actual["202"].frequency_orders, actual["202"].monetary_value) == (3, 1, Decimal("8.5000"))

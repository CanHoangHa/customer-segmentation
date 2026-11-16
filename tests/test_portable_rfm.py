import csv
import json

import pandas as pd

from src.portable_rfm import build_portable_rfm
from src.prepare_data import COLUMNS


def test_portable_rfm_applies_primary_rules_and_writes_model_input(tmp_path) -> None:
    source = tmp_path / "kz.csv"
    customer = "1515915625453675584"
    rows = [
        ["2020-11-20 10:00:00 UTC", "100", "1", "", "", "", "10.00", customer],
        ["2020-11-20 10:00:00 UTC", "100", "2", "", "", "", "5.00", customer],
        ["2020-11-21 10:00:00 UTC", "101", "1", "", "20.00", customer],
        ["2020-11-21 10:00:00 UTC", "102", "1", "", "10", ""],
        ["2020-11-21 10:00:00 UTC", "103", "1", "", "", "", "0", customer],
        ["2020-11-21 10:00:00 UTC", "900", "1", "", "", "", "10", customer],
        ["2020-11-21 10:00:00 UTC", "900", "1", "", "", "", "10", "200"],
    ]
    with source.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    output = tmp_path / "processed"
    reports = tmp_path / "reports"
    result = build_portable_rfm(
        source, output, reports, verify_committed_reports=False
    )
    rfm = pd.read_parquet(output / "customer_rfm.parquet")
    clean = pd.read_parquet(output / "purchases_clean.parquet")
    saved = json.loads((reports / "portable_run_summary.json").read_text(encoding="utf-8"))

    assert result == saved
    assert result["clean_rows"] == 3
    assert result["quarantine_rows"] == 4
    assert result["accepted_repaired_rows"] == 1
    assert result["conflicting_orders"] == 1
    assert len(clean) == 3
    assert len(rfm) == 1
    assert rfm.iloc[0]["recency_days"] == 1
    assert rfm.iloc[0]["frequency_orders"] == 2
    assert str(rfm.iloc[0]["monetary_value"]) == "35.0000"

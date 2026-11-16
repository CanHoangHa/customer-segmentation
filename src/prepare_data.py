"""Align CSV fields, validate purchases, and export Parquet files."""

import csv
import json
import os
import sys

import pyarrow as pa
import pyarrow.parquet as pq
from pyspark.sql import SparkSession, functions as F, types as T


COLUMNS = [
    "event_time", "order_id", "product_id", "category_id",
    "category_code", "brand", "price", "user_id",
]


def start_spark():
    """Use the active Python environment and UTC for date calculations."""
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    if os.name == "nt":
        # Use TCP for Java pipes when Windows Unix sockets are unavailable.
        options = os.environ.get("SPARK_SUBMIT_OPTS", "")
        if "jdk.net.unixdomain.tmpdir" not in options:
            os.environ["SPARK_SUBMIT_OPTS"] = options + " -Djdk.net.unixdomain.tmpdir=NUL"
    spark = (
        SparkSession.builder.master("local[2]")
        .appName("CustomerSegmentationData")
        .config("spark.driver.memory", "2g")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.legacy.timeParserPolicy", "CORRECTED")
        .config("spark.sql.shuffle.partitions", "4")
        .config("spark.ui.enabled", "false")
        .config("spark.ui.showConsoleProgress", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def read_source(spark, path):
    """Read the single-line CSV records without padding short rows."""
    source = path.resolve().as_uri()
    header = spark.read.text(source).first()
    if header is None or next(csv.reader([header.value.lstrip("\ufeff")]), []) != COLUMNS:
        raise ValueError("The input columns do not match the dataset schema.")

    def parse_partition(records):
        for line, number in records:
            if number > 0:
                yield number, next(csv.reader([line], strict=True), [])

    records = spark.sparkContext.textFile(source).zipWithIndex().mapPartitions(parse_partition)
    return spark.createDataFrame(records, "source_record long, fields array<string>").withColumn(
        "field_count", F.size("fields")
    )


def short_row_pattern():
    fields = F.transform("fields", lambda value: F.trim(value))
    return (
        (F.col("field_count") == 6)
        & (fields[3] == "")
        & fields[4].rlike(r"^-?[0-9]+(\.[0-9]+)?$")
        & fields[5].rlike(r"^([0-9]+)?$")
    )


def align_purchases(raw):
    fields = F.col("fields")
    status = (
        F.when(F.col("field_count") == 8, "full_width")
        .when(short_row_pattern(), "repaired_6_fields")
        .otherwise("unmatched_structure")
    )
    repaired = F.concat(F.slice(fields, 1, 3), F.array(F.lit(None), F.lit(None), F.lit(None)),
                        F.slice(fields, 5, 2))
    frame = raw.withColumn("row_status", status).withColumn(
        "unmatched_values", F.when(F.col("row_status") == "unmatched_structure", F.to_json(fields))
    )
    aligned = (
        F.when(F.col("row_status") == "full_width", fields)
        .when(F.col("row_status") == "repaired_6_fields", repaired)
    )
    frame = frame.withColumn("aligned", aligned)
    columns = []
    for index, name in enumerate(COLUMNS):
        value = F.trim(F.col("aligned")[index])
        columns.append(F.when(value != "", value).alias(name))
    return frame.select("source_record", "field_count", "row_status", "unmatched_values", *columns)


def missing_counts(frame, names):
    return frame.agg(*[
        F.count(F.when(F.col(name).isNull(), 1)).alias(name) for name in names
    ]).first()


def validate_purchases(frame, year=2020):
    """Assign one primary rejection reason so row counts reconcile."""
    frame = frame.withColumnRenamed("event_time", "event_time_raw").withColumnRenamed("price", "price_raw")
    frame = frame.withColumn(
        "event_time", F.try_to_timestamp("event_time_raw", F.lit("yyyy-MM-dd HH:mm:ss 'UTC'"))
    ).withColumn("price", F.expr("try_cast(price_raw as decimal(20, 4))"))

    valid_order = F.col("order_id").rlike(r"^[0-9]+$")
    valid_customer = F.col("user_id").rlike(r"^[0-9]+$")
    conflicts = (
        frame.filter(valid_order & valid_customer).groupBy("order_id")
        .agg(F.countDistinct("user_id").alias("customer_count"))
        .filter("customer_count > 1")
        .select("order_id").withColumn("order_conflict", F.lit(True))
    )
    frame = frame.join(conflicts, "order_id", "left")
    valid_price_format = F.col("price_raw").rlike(r"^-?[0-9]+(\.[0-9]{1,4})?$")
    reason = (
        F.when(F.col("row_status") == "unmatched_structure", "unmatched_structure")
        .when(F.col("order_id").isNull(), "missing_order_id")
        .when(~valid_order, "invalid_order_id")
        .when(F.col("user_id").isNull(), "missing_customer_id")
        .when(~valid_customer, "invalid_customer_id")
        .when(F.col("event_time").isNull(), "invalid_date")
        .when(F.year("event_time") != year, "date_outside_scope")
        .when(F.col("price").isNull() | ~valid_price_format, "invalid_price")
        .when(F.col("price") <= 0, "nonpositive_price")
        .when(F.col("order_conflict"), "conflicting_order")
        .otherwise(F.lit(None).cast("string"))
    )
    return frame.withColumn("rejection_reason", reason).drop("order_conflict")


def clean_purchases(validated):
    return validated.filter("rejection_reason is null").select(
        "source_record", "row_status", "event_time", "order_id", "product_id",
        "category_id", "category_code", "brand", "price",
        F.col("user_id").alias("customer_id"),
    )


def write_parquet(frame, path, batch_size=25000):
    """Write bounded batches, including on Windows without Hadoop binaries."""
    path.parent.mkdir(parents=True, exist_ok=True)
    arrow_fields = []
    timestamps = []
    for field in frame.schema:
        data_type = field.dataType
        if isinstance(data_type, T.DecimalType):
            arrow_type = pa.decimal128(data_type.precision, data_type.scale)
        elif isinstance(data_type, T.TimestampType):
            arrow_type = pa.timestamp("us", tz="UTC")
            timestamps.append(field.name)
        else:
            arrow_type = {"string": pa.string(), "bigint": pa.int64(), "int": pa.int32()}[data_type.simpleString()]
        arrow_fields.append(pa.field(field.name, arrow_type))
    schema = pa.schema(arrow_fields)

    # Transfer timestamps as explicit UTC text to avoid local timezone changes.
    export = frame
    for name in timestamps:
        export = export.withColumn(name, F.date_format(name, "yyyy-MM-dd'T'HH:mm:ss.SSSSSS'Z'"))
    from datetime import datetime
    temporary = path.with_suffix(".parquet.tmp")
    with pq.ParquetWriter(temporary, schema, compression="snappy") as writer:
        batch = []
        for row in export.toLocalIterator():
            record = row.asDict()
            for name in timestamps:
                if record[name] is not None:
                    record[name] = datetime.fromisoformat(record[name].replace("Z", "+00:00"))
            batch.append(record)
            if len(batch) >= batch_size:
                writer.write_table(pa.Table.from_pylist(batch, schema=schema))
                batch.clear()
        if batch:
            writer.write_table(pa.Table.from_pylist(batch, schema=schema))
    temporary.replace(path)


def prepare_data(spark, source, output_dir, report_dir, year=2020):
    aligned = align_purchases(read_source(spark, source)).cache()
    validated = validate_purchases(aligned, year).cache()
    reason_counts = {row["rejection_reason"] or "accepted": row["count"]
                     for row in validated.groupBy("rejection_reason").count().collect()}
    clean = clean_purchases(validated).cache()
    rejected = validated.filter("rejection_reason is not null")
    raw_count = sum(reason_counts.values())
    clean_count = clean.count()
    if clean_count == 0:
        raise ValueError("No purchases passed validation. Review the data quality report.")
    assert clean_count + sum(value for key, value in reason_counts.items() if key != "accepted") == raw_count

    quality = []
    for label, table, names in [
        ("before_validation", aligned, COLUMNS),
        ("after_validation", clean, ["event_time", "order_id", "product_id", "category_id", "category_code", "brand", "price", "customer_id"]),
    ]:
        total = raw_count if label == "before_validation" else clean_count
        missing = missing_counts(table, names)
        for name in names:
            quality.append({"stage": label, "column": name, "rows": total,
                            "missing_count": missing[name], "missing_pct": round(missing[name] / total * 100, 4)})

    report_dir.mkdir(parents=True, exist_ok=True)
    with (report_dir / "cleaning_quality.csv").open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(quality[0]))
        writer.writeheader()
        writer.writerows(quality)
    repaired_count = clean.filter("row_status = 'repaired_6_fields'").count()
    report = {"source_file": source.name, "year": year, "raw_rows": raw_count,
              "clean_rows": clean_count, "quarantine_rows": raw_count - clean_count,
              "accepted_repaired_rows": repaired_count, "rows_by_primary_reason": reason_counts,
              "duplicate_policy": "Keep repeated rows; source has no unique line identifier.",
              "money_unit": "Source price units; currency is not verified."}
    write_parquet(clean, output_dir / "purchases_clean.parquet")
    write_parquet(rejected, output_dir.parent / "quarantine" / "purchases_rejected.parquet")
    (report_dir / "cleaning_summary.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    validated.unpersist()
    aligned.unpersist()
    return clean, report

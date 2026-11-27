# Databricks notebook source
from datetime import datetime, timezone

S = "workspace.lantern"
RUN_ID = spark.table(f"{S}.bronze_records").select("_run_id").first()[0]
RUN_TS = datetime.now(timezone.utc)

def dup_rows(table, keys):
    """Extra copies beyond the first for each key; GROUP BY treats NULLs as equal."""
    return f"""SELECT coalesce(sum(c - 1), 0), (SELECT count(*) FROM {S}.{table})
               FROM (SELECT count(*) AS c FROM {S}.{table} GROUP BY {keys} HAVING count(*) > 1)"""

# (check, dimension, table, SQL returning [failed_rows, total_rows], max allowed failure rate)
CHECKS = [
    ("records_have_page_and_bbox", "completeness", "bronze_records",
     f"SELECT sum(CASE WHEN page IS NULL OR bbox IS NULL OR size(bbox) <> 4 THEN 1 ELSE 0 END), count(*) FROM {S}.bronze_records", 0.0),
    ("line_items_have_value", "completeness", "silver_line_items",
     f"SELECT sum(CASE WHEN extracted_value IS NULL THEN 1 ELSE 0 END), count(*) FROM {S}.silver_line_items", 0.01),
    ("reconciliation_matches_xbrl", "accuracy", "gold_reconciliation",
     f"SELECT sum(CASE WHEN recon_status NOT IN ('MATCH','MATCH_SIGN') THEN 1 ELSE 0 END), count(*) FROM {S}.gold_reconciliation", 0.01),
    ("xbrl_fact_key_unique", "uniqueness", "silver_xbrl_facts",
     dup_rows("silver_xbrl_facts", "stem, concept, dims, unit, period_start, period_end"), 0.0),
    ("line_item_key_unique", "uniqueness", "silver_line_items",
     dup_rows("silver_line_items", "stem, extraction_path, statement, label, occurrence, fiscal_year"), 0.0),
    ("fiscal_year_in_range", "validity", "silver_line_items",
     f"SELECT sum(CASE WHEN fiscal_year NOT BETWEEN 2015 AND year(current_date()) THEN 1 ELSE 0 END), count(*) FROM {S}.silver_line_items", 0.0),
    # A 10-K is due within 60 days of fiscal year end, so data older than 365 + 60 days is stale
    ("latest_filing_fresh", "freshness", "silver_filings",
     f"SELECT CASE WHEN datediff(current_date(), max(period_of_report)) > 425 THEN 1 ELSE 0 END, 1 FROM {S}.silver_filings", 0.0),
    ("ingested_within_24h", "freshness", "bronze_records",
     f"SELECT CASE WHEN max(_ingested_at) < current_timestamp() - INTERVAL 24 HOURS THEN 1 ELSE 0 END, 1 FROM {S}.bronze_records", 0.0),
]

rows = []
for name, dim, table, sql, max_rate in CHECKS:
    failed, total = spark.sql(sql).first()
    failed, total = int(failed or 0), int(total or 0)
    rate = failed / total if total else 0.0
    rows.append((RUN_ID, RUN_TS, name, dim, table, failed, total, round(rate, 4), rate <= max_rate))

results = spark.createDataFrame(rows,
    "run_id string, run_ts timestamp, check_name string, dimension string, table_name string, "
    "failed_rows long, total_rows long, failure_rate double, passed boolean")

# Append, so results build up across runs and quality can be tracked over time
results.write.mode("append").saveAsTable(f"{S}.dq_results")
display(results)
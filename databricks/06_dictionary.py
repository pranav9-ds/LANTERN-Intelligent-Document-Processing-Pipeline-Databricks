# Databricks notebook source
S = "workspace.lantern"

TABLES = {
    "bronze_records":      "Raw LANTERN JSONL export, one row per parsed block, with lineage columns",
    "bronze_xbrl_facts":   "Raw XBRL numeric facts extracted by Arelle (CSV as loaded)",
    "bronze_comparison":   "Raw LANTERN statement line items with their mapped XBRL concepts",
    "bronze_manifest":     "Raw filing manifest: one row per rendered 10-K",
    "silver_xbrl_facts":   "Typed XBRL facts; the official reference values",
    "silver_line_items":   "Typed statement line items extracted from the PDFs by both extraction paths",
    "silver_filings":      "One row per filing with a standardized 10-digit CIK",
    "gold_reconciliation": "Every extracted line item reconciled to XBRL, with tolerance and status",
    "dq_results":          "Data-quality check results, appended on every run",
}

COLUMNS = {
    "silver_line_items": {
        "extraction_path": "traditional (pdfplumber + Camelot) or docling",
        "extracted_value": "Value read from the PDF table, normalized to full units",
        "concept":         "Mapped US-GAAP XBRL concept",
        "lantern_status":  "LANTERN's original Python reconciliation verdict, kept for cross-checking",
    },
    "gold_reconciliation": {
        "xbrl_value":   "Official value from the filing's XBRL",
        "tolerance":    "Allowed difference: 0.5 x 10^(-decimals), from XBRL rounding",
        "recon_status": "MATCH, MATCH_SIGN, BREAK, XBRL_MISSING, UNMAPPED or PDF_MISSING",
    },
    "dq_results": {
        "dimension":    "completeness, accuracy, uniqueness, validity or freshness",
        "failure_rate": "failed_rows / total_rows",
        "passed":       "True if failure_rate is within the check's threshold",
    },
}

def q(text):
    """Escape apostrophes so the text is safe inside a SQL string."""
    return text.replace("'", "\\'")

for t, c in TABLES.items():
    spark.sql(f"COMMENT ON TABLE {S}.{t} IS '{q(c)}'")
for t, cols in COLUMNS.items():
    for col, c in cols.items():
        spark.sql(f"COMMENT ON COLUMN {S}.{t}.{col} IS '{q(c)}'")
print("comments added")

# COMMAND ----------

S = "workspace.lantern"

def q(text):
    """Escape apostrophes so the text is safe inside a SQL string."""
    return text.replace("'", "\\'")

# 1. Describe the gold KPI and financials columns
KPI_COLS = {
    "gold_kpis": {
        "gross_margin_pct":     "Gross profit / revenue x 100",
        "operating_margin_pct": "Operating income / revenue x 100",
        "net_margin_pct":       "Net income / revenue x 100",
        "free_cash_flow":       "Operating cash flow - capital expenditure, in USD",
        "revenue_growth_pct":   "Year-over-year change in revenue, in percent",
    },
    "gold_financials": {
        "revenue":             "Total net sales (us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax), USD",
        "gross_profit":        "us-gaap:GrossProfit, USD",
        "operating_income":    "us-gaap:OperatingIncomeLoss, USD",
        "net_income":          "us-gaap:NetIncomeLoss, USD",
        "operating_cash_flow": "us-gaap:NetCashProvidedByUsedInOperatingActivities, USD",
        "capex":               "us-gaap:PaymentsToAcquirePropertyPlantAndEquipment, USD (absolute value)",
    },
}
for t, cols in KPI_COLS.items():
    for col, c in cols.items():
        spark.sql(f"COMMENT ON COLUMN {S}.{t}.{col} IS '{q(c)}'")
print("KPI comments added")

# 2. Build the Markdown data dictionary from Unity Catalog
tables = spark.sql("""SELECT table_name, table_type, comment FROM workspace.information_schema.tables
                      WHERE table_schema = 'lantern' ORDER BY table_name""").collect()
cols = spark.sql("""SELECT table_name, column_name, data_type, comment FROM workspace.information_schema.columns
                    WHERE table_schema = 'lantern' AND column_name NOT LIKE '\\_%'
                    ORDER BY table_name, ordinal_position""").collect()

md = ["# LANTERN lakehouse data dictionary\n",
      "Generated from Unity Catalog (`workspace.lantern`); do not edit by hand.\n"]
for t in tables:
    md.append(f"## {t.table_name} ({t.table_type.lower()})\n\n{t.comment or ''}\n")
    md.append("| Column | Type | Description |\n|---|---|---|")
    md += [f"| {c.column_name} | {c.data_type} | {c.comment or ''} |" for c in cols if c.table_name == t.table_name]
    md.append("")
text = "\n".join(md)

# 3. Save it to the Volume so you can download it, and print it
dbutils.fs.put("/Volumes/workspace/lantern/raw/data_dictionary.md", text, overwrite=True)
print(text)
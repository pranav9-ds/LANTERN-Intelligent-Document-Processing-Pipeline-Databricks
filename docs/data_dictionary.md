# LANTERN lakehouse data dictionary

Generated from Unity Catalog (`workspace.lantern`); do not edit by hand.

## bronze_comparison (managed)

Raw LANTERN statement line items with their mapped XBRL concepts

| Column | Type | Description |
|---|---|---|
| stem | STRING |  |
| path | STRING |  |
| page | STRING |  |
| statement | STRING |  |
| label | STRING |  |
| occurrence | STRING |  |
| year | STRING |  |
| value | STRING |  |
| concept | STRING |  |
| dims | STRING |  |
| map_method | STRING |  |
| period_end | STRING |  |
| xbrl_value | STRING |  |
| diff | STRING |  |
| status | STRING |  |

## bronze_manifest (managed)

Raw filing manifest: one row per rendered 10-K

| Column | Type | Description |
|---|---|---|
| stem | STRING |  |
| accession | STRING |  |
| cik | STRING |  |
| ticker | STRING |  |
| form | STRING |  |
| period | STRING |  |
| company | STRING |  |
| source_file | STRING |  |
| renderer | STRING |  |
| renderer_version | STRING |  |
| page_format | STRING |  |

## bronze_records (managed)

Raw LANTERN JSONL export, one row per parsed block, with lineage columns

| Column | Type | Description |
|---|---|---|
| bbox | ARRAY |  |
| block_id | STRING |  |
| block_type | STRING |  |
| cik | STRING |  |
| company | STRING |  |
| detector | STRING |  |
| detector_score | DOUBLE |  |
| doc_id | STRING |  |
| extractor | STRING |  |
| extractor_version | STRING |  |
| figure_path | STRING |  |
| fiscal_period | STRING |  |
| fiscal_year | LONG |  |
| form | STRING |  |
| ocr | BOOLEAN |  |
| ocr_conf | DOUBLE |  |
| origin | STRING |  |
| page | LONG |  |
| schema | STRING |  |
| section | STRING |  |
| sha256 | STRING |  |
| source_path | STRING |  |
| table | STRUCT |  |
| text | STRING |  |
| ticker | STRING |  |
| units | STRING |  |

## bronze_xbrl_facts (managed)

Raw XBRL numeric facts extracted by Arelle (CSV as loaded)

| Column | Type | Description |
|---|---|---|
| stem | STRING |  |
| concept | STRING |  |
| value | STRING |  |
| unit | STRING |  |
| decimals | STRING |  |
| instant | STRING |  |
| start | STRING |  |
| end | STRING |  |
| dims | STRING |  |

## dq_results (managed)

Data-quality check results, appended on every run

| Column | Type | Description |
|---|---|---|
| run_id | STRING |  |
| run_ts | TIMESTAMP |  |
| check_name | STRING |  |
| dimension | STRING | completeness, accuracy, uniqueness, validity or freshness |
| table_name | STRING |  |
| failed_rows | LONG |  |
| total_rows | LONG |  |
| failure_rate | DOUBLE | failed_rows / total_rows |
| passed | BOOLEAN | True if failure_rate is within the check's threshold |

## gold_financials (view)

One row per fiscal year of XBRL-reconciled statement totals (traditional path, matched lines only)

| Column | Type | Description |
|---|---|---|
| fiscal_year | INT |  |
| revenue | DOUBLE | Total net sales (us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax), USD |
| gross_profit | DOUBLE | us-gaap:GrossProfit, USD |
| operating_income | DOUBLE | us-gaap:OperatingIncomeLoss, USD |
| net_income | DOUBLE | us-gaap:NetIncomeLoss, USD |
| operating_cash_flow | DOUBLE | us-gaap:NetCashProvidedByUsedInOperatingActivities, USD |
| capex | DOUBLE | us-gaap:PaymentsToAcquirePropertyPlantAndEquipment, USD (absolute value) |

## gold_kpis (view)

Standard KPI definitions; every metric is calculated only here

| Column | Type | Description |
|---|---|---|
| fiscal_year | INT |  |
| gross_margin_pct | DOUBLE | Gross profit / revenue x 100 |
| operating_margin_pct | DOUBLE | Operating income / revenue x 100 |
| net_margin_pct | DOUBLE | Net income / revenue x 100 |
| free_cash_flow | DOUBLE | Operating cash flow - capital expenditure, in USD |
| revenue_growth_pct | DOUBLE | Year-over-year change in revenue, in percent |

## gold_reconciliation (managed)

Every extracted line item reconciled to XBRL, with tolerance and status

| Column | Type | Description |
|---|---|---|
| stem | STRING |  |
| extraction_path | STRING |  |
| page | INT |  |
| statement | STRING |  |
| label | STRING |  |
| occurrence | INT |  |
| fiscal_year | INT |  |
| extracted_value | DOUBLE |  |
| concept | STRING |  |
| dims | STRING |  |
| map_method | STRING |  |
| period_end | DATE |  |
| lantern_status | STRING |  |
| xbrl_value | DOUBLE | Official value from the filing's XBRL |
| unit | STRING |  |
| decimals | INT |  |
| tolerance | DOUBLE | Allowed difference: 0.5 x 10^(-decimals), from XBRL rounding |
| recon_status | STRING | MATCH, MATCH_SIGN, BREAK, XBRL_MISSING, UNMAPPED or PDF_MISSING |

## silver_filings (managed)

One row per filing with a standardized 10-digit CIK

| Column | Type | Description |
|---|---|---|
| stem | STRING |  |
| accession | STRING |  |
| cik | STRING |  |
| ticker | STRING |  |
| form | STRING |  |
| company | STRING |  |
| period_of_report | DATE |  |
| renderer | STRING |  |

## silver_line_items (managed)

Typed statement line items extracted from the PDFs by both extraction paths

| Column | Type | Description |
|---|---|---|
| stem | STRING |  |
| extraction_path | STRING | traditional (pdfplumber + Camelot) or docling |
| page | INT |  |
| statement | STRING |  |
| label | STRING |  |
| occurrence | INT |  |
| fiscal_year | INT |  |
| extracted_value | DOUBLE | Value read from the PDF table, normalized to full units |
| concept | STRING | Mapped US-GAAP XBRL concept |
| dims | STRING |  |
| map_method | STRING |  |
| period_end | DATE |  |
| lantern_status | STRING | LANTERN's original Python reconciliation verdict, kept for cross-checking |

## silver_xbrl_facts (managed)

Typed XBRL facts; the official reference values

| Column | Type | Description |
|---|---|---|
| stem | STRING |  |
| concept | STRING |  |
| xbrl_value | DOUBLE |  |
| unit | STRING |  |
| decimals | INT |  |
| is_instant | BOOLEAN |  |
| period_start | DATE |  |
| period_end | DATE |  |
| dims | STRING |  |

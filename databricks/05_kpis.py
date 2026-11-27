# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW workspace.lantern.gold_financials
# MAGIC COMMENT 'One row per fiscal year of XBRL-reconciled statement totals (traditional path, matched lines only)'
# MAGIC AS
# MAGIC WITH v AS (
# MAGIC   SELECT fiscal_year, concept, abs(extracted_value) AS value,
# MAGIC          -- the same year appears in both filings; take it from the newest filing
# MAGIC          row_number() OVER (PARTITION BY fiscal_year, concept ORDER BY stem DESC) AS rn
# MAGIC   FROM workspace.lantern.gold_reconciliation
# MAGIC   WHERE extraction_path = 'traditional'
# MAGIC     AND recon_status IN ('MATCH', 'MATCH_SIGN')
# MAGIC     AND dims = '{}'
# MAGIC )
# MAGIC SELECT fiscal_year,
# MAGIC   max(CASE WHEN concept = 'us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax' THEN value END) AS revenue,
# MAGIC   max(CASE WHEN concept = 'us-gaap:GrossProfit'                                         THEN value END) AS gross_profit,
# MAGIC   max(CASE WHEN concept = 'us-gaap:OperatingIncomeLoss'                                 THEN value END) AS operating_income,
# MAGIC   max(CASE WHEN concept = 'us-gaap:NetIncomeLoss'                                       THEN value END) AS net_income,
# MAGIC   max(CASE WHEN concept = 'us-gaap:NetCashProvidedByUsedInOperatingActivities'          THEN value END) AS operating_cash_flow,
# MAGIC   max(CASE WHEN concept = 'us-gaap:PaymentsToAcquirePropertyPlantAndEquipment'          THEN value END) AS capex
# MAGIC FROM v WHERE rn = 1
# MAGIC GROUP BY fiscal_year;

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE OR REPLACE VIEW workspace.lantern.gold_kpis
# MAGIC COMMENT 'Standard KPI definitions; every metric is calculated only here'
# MAGIC AS
# MAGIC SELECT fiscal_year,
# MAGIC   round(100 * gross_profit     / revenue, 2) AS gross_margin_pct,      -- gross profit / revenue
# MAGIC   round(100 * operating_income / revenue, 2) AS operating_margin_pct,  -- operating income / revenue
# MAGIC   round(100 * net_income       / revenue, 2) AS net_margin_pct,        -- net income / revenue
# MAGIC   operating_cash_flow - capex                AS free_cash_flow,        -- operating cash flow - capital expenditure
# MAGIC   round(100 * (revenue / lag(revenue) OVER (ORDER BY fiscal_year) - 1), 2) AS revenue_growth_pct  -- year-over-year growth
# MAGIC FROM workspace.lantern.gold_financials;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT f.*, k.* EXCEPT (fiscal_year)
# MAGIC FROM workspace.lantern.gold_financials f
# MAGIC JOIN workspace.lantern.gold_kpis k USING (fiscal_year)
# MAGIC ORDER BY fiscal_year;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT DISTINCT statement, label, concept FROM workspace.lantern.gold_reconciliation
# MAGIC WHERE extraction_path = 'traditional' AND dims = '{}' ORDER BY statement;
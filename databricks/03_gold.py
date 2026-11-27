# Databricks notebook source
# MAGIC %sql
# MAGIC CREATE OR REPLACE TABLE workspace.lantern.gold_reconciliation AS
# MAGIC WITH annual_facts AS (
# MAGIC   SELECT * FROM workspace.lantern.silver_xbrl_facts
# MAGIC   WHERE is_instant OR datediff(period_end, period_start) BETWEEN 350 AND 380
# MAGIC ),
# MAGIC joined AS (
# MAGIC   SELECT i.*, f.xbrl_value, f.unit, f.decimals,
# MAGIC          CASE WHEN f.decimals IS NULL THEN 0.5 ELSE 0.5 * power(10, -f.decimals) END AS tolerance
# MAGIC   FROM workspace.lantern.silver_line_items i
# MAGIC   LEFT JOIN annual_facts f
# MAGIC     ON  i.stem = f.stem AND i.concept = f.concept
# MAGIC     AND i.dims = f.dims AND i.period_end = f.period_end
# MAGIC )
# MAGIC SELECT *,
# MAGIC   CASE
# MAGIC     WHEN extracted_value IS NULL THEN 'PDF_MISSING'
# MAGIC     WHEN concept IS NULL         THEN 'UNMAPPED'
# MAGIC     WHEN xbrl_value IS NULL      THEN 'XBRL_MISSING'
# MAGIC     WHEN abs(extracted_value - xbrl_value) <= tolerance THEN 'MATCH'
# MAGIC     WHEN abs(abs(extracted_value) - abs(xbrl_value)) <= tolerance THEN 'MATCH_SIGN'
# MAGIC     ELSE 'BREAK'
# MAGIC   END AS recon_status
# MAGIC FROM joined;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(*) FROM workspace.lantern.gold_reconciliation;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT extraction_path, statement,
# MAGIC        count(*) AS line_items,
# MAGIC        sum(CASE WHEN recon_status IN ('MATCH','MATCH_SIGN') THEN 1 ELSE 0 END) AS matched,
# MAGIC        round(100 * avg(CASE WHEN recon_status IN ('MATCH','MATCH_SIGN') THEN 1 ELSE 0 END), 2) AS match_rate_pct,
# MAGIC        sum(CASE WHEN recon_status = 'BREAK' THEN 1 ELSE 0 END) AS breaks,
# MAGIC        round(100 * avg(CASE WHEN (recon_status IN ('MATCH','MATCH_SIGN'))
# MAGIC                               = (lantern_status IN ('match','match_negated')) THEN 1 ELSE 0 END), 2) AS agrees_with_lantern_pct
# MAGIC FROM workspace.lantern.gold_reconciliation
# MAGIC GROUP BY ROLLUP(extraction_path, statement)
# MAGIC ORDER BY extraction_path NULLS LAST, statement NULLS LAST;
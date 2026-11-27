# Databricks notebook source
from pyspark.sql import functions as F

S = "workspace.lantern"

def save(df, name):
    df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(f"{S}.{name}")
    print(f"{name}: {spark.table(f'{S}.{name}').count()} rows")

# 1. XBRL facts: the official reference values
facts = (spark.table(f"{S}.bronze_xbrl_facts")
    .select("stem", "concept",
            F.col("value").cast("double").alias("xbrl_value"),
            F.lower("unit").alias("unit"),
            F.expr("try_cast(decimals AS INT)").alias("decimals"),   # 'INF' becomes NULL
            (F.col("instant") == "True").alias("is_instant"),
            F.to_date("start").alias("period_start"),
            F.to_date("end").alias("period_end"),
            F.coalesce("dims", F.lit("{}")).alias("dims"),
            "_source_file", "_run_id")
    # the same fact can appear several times in iXBRL; keep one copy
    .dropDuplicates(["stem", "concept", "dims", "unit", "period_start", "period_end", "xbrl_value"]))
save(facts, "silver_xbrl_facts")

# 2. Extracted statement line items, from LANTERN's table extractors
items = (spark.table(f"{S}.bronze_comparison")
    .select("stem",
            F.col("path").alias("extraction_path"),          # traditional or docling
            F.col("page").cast("int").alias("page"),
            "statement", "label",
            F.col("occurrence").cast("int").alias("occurrence"),
            F.col("year").cast("int").alias("fiscal_year"),
            F.col("value").cast("double").alias("extracted_value"),
            "concept",
            F.coalesce("dims", F.lit("{}")).alias("dims"),
            "map_method",
            F.to_date("period_end").alias("period_end"),
            F.col("status").alias("lantern_status"),         # LANTERN's own verdict, kept for cross-checking
            "_source_file", "_run_id"))
save(items, "silver_line_items")

# 3. Filing manifest: one row per filing
manifest = (spark.table(f"{S}.bronze_manifest")
    .select("stem", "accession",
            F.lpad("cik", 10, "0").alias("cik"),
            "ticker", "form", "company",
            F.to_date("period", "yyyyMMdd").alias("period_of_report"),
            "renderer", "_source_file", "_run_id"))
save(manifest, "silver_filings")

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT stem, concept, dims, unit, period_start, period_end,
# MAGIC        count(*) AS copies, collect_set(xbrl_value) AS values
# MAGIC FROM workspace.lantern.silver_xbrl_facts
# MAGIC GROUP BY ALL
# MAGIC HAVING count(*) > 1;

# COMMAND ----------

# MAGIC %sql
# MAGIC SELECT count(*) FROM workspace.lantern.silver_line_items
# MAGIC WHERE concept = 'us-gaap:UnrecognizedTaxBenefits';

# COMMAND ----------


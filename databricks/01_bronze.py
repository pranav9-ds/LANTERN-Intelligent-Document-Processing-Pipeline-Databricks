# Databricks notebook source
# Inspect the raw LANTERN outputs before designing the tables
base = "/Volumes/workspace/lantern/raw/"

records = spark.read.json(base + "*.jsonl")
records.printSchema()

for f in ["facts.csv", "comparison.csv", "manifest.csv"]:
    df = spark.read.option("header", True).csv(base + f)
    print(f, df.columns)

# COMMAND ----------

from pyspark.sql import functions as F
import uuid

SCHEMA = "workspace.lantern"
RAW = "/Volumes/workspace/lantern/raw/"
RUN_ID = str(uuid.uuid4())          # one id per pipeline run, for lineage

def with_lineage(df):
    """Add lineage columns: source file, load time and run id."""
    return (df.withColumn("_source_file", F.col("_metadata.file_path"))
              .withColumn("_ingested_at", F.current_timestamp())
              .withColumn("_run_id", F.lit(RUN_ID)))

def write_bronze(df, name):
    (df.write.mode("overwrite")
       .option("overwriteSchema", "true")
       .saveAsTable(f"{SCHEMA}.{name}"))
    print(f"{name}: {spark.table(f'{SCHEMA}.{name}').count()} rows")

# JSONL records from LANTERN's export stage (one row per block)
write_bronze(with_lineage(spark.read.json(RAW + "*.jsonl")), "bronze_records")

# CSVs kept as raw strings in bronze; typing happens in silver
for file, name in [("facts.csv", "bronze_xbrl_facts"),
                   ("comparison.csv", "bronze_comparison"),
                   ("manifest.csv", "bronze_manifest")]:
    df = spark.read.option("header", True).option("escape", '"').csv(RAW + file)
    write_bronze(with_lineage(df), name)

print("run_id:", RUN_ID)

# COMMAND ----------

spark.sql(f"""
  SELECT block_id, page, table.columns, table.row_kinds,
         slice(table.rows, 1, 3) AS rows, slice(table.raw_cells, 1, 3) AS raw_cells,
         table.scale
  FROM {SCHEMA}.bronze_records
  WHERE block_type = 'Table' AND table.source_csv IS NOT NULL
  LIMIT 1
""").show(truncate=False, vertical=True)

spark.table(f"{SCHEMA}.bronze_xbrl_facts").drop("_source_file", "_ingested_at", "_run_id").show(3, truncate=False)
spark.table(f"{SCHEMA}.bronze_comparison").drop("_source_file", "_ingested_at", "_run_id").show(3, truncate=False)

# COMMAND ----------

spark.table("workspace.lantern.bronze_xbrl_facts").select("dims").distinct().show(3, truncate=False)

# COMMAND ----------


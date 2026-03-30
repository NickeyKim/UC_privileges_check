# Databricks notebook source
# MAGIC %sql
# MAGIC -- example: store it in users.nakhoe_kim schema
# MAGIC -- please change them if you use your own schema
# MAGIC CREATE SCHEMA IF NOT EXISTS users.nakhoe_kim;
# MAGIC
# MAGIC CREATE TABLE IF NOT EXISTS users.nakhoe_kim.uc_grants_snapshot (
# MAGIC   -- snapshot meta
# MAGIC   snapshot_date      DATE        NOT NULL COMMENT 'Snapshot partition date (UTC)',
# MAGIC   snapshot_ts        TIMESTAMP   NOT NULL COMMENT 'Snapshot timestamp',
# MAGIC
# MAGIC   -- run/environment meta (this is optional)
# MAGIC   env                STRING      NOT NULL COMMENT 'Environment label: DEV/STG/PRD etc.',
# MAGIC   workspace_id       STRING      COMMENT 'Databricks workspace id (optional)',
# MAGIC   source_job_run_id  STRING      COMMENT 'Job run id / pipeline run id (optional)',
# MAGIC   collector          STRING      COMMENT 'Collector identity (SPN/user) (optional)',
# MAGIC
# MAGIC   -- object identification
# MAGIC   object_type        STRING      NOT NULL COMMENT 'CATALOG|SCHEMA|TABLE|VIEW|VOLUME|FUNCTION',
# MAGIC   object_catalog     STRING      COMMENT 'Catalog name (nullable for some types)',
# MAGIC   object_schema      STRING      COMMENT 'Schema name (nullable for catalog-level)',
# MAGIC   object_name        STRING      COMMENT 'Object name only (table/view/volume/function) if applicable',
# MAGIC   object_full_name   STRING      NOT NULL COMMENT 'Fully-qualified name, e.g. `cat`.`sch`.`obj` or `cat`',
# MAGIC
# MAGIC   -- Privilege(Grant)
# MAGIC   principal          STRING      NOT NULL COMMENT 'Grantee: user/group/service principal',
# MAGIC   privilege          STRING      NOT NULL COMMENT 'Privilege type (e.g., SELECT, USE_SCHEMA, OWN, MODIFY, ...)',
# MAGIC
# MAGIC   -- Original information of SHOW GRANTS (this is optional)
# MAGIC   raw_object_type    STRING      COMMENT 'Raw object type from SHOW GRANTS (optional)',
# MAGIC   raw_object_key     STRING      COMMENT 'Raw object key from SHOW GRANTS (optional)'
# MAGIC )
# MAGIC USING DELTA
# MAGIC PARTITIONED BY (snapshot_date)
# MAGIC COMMENT 'Unity Catalog GRANTS snapshot table for drift detection (append-only recommended)'
# MAGIC TBLPROPERTIES (
# MAGIC   delta.autoOptimize.optimizeWrite = true,
# MAGIC   delta.autoOptimize.autoCompact   = true,
# MAGIC   delta.dataSkippingNumIndexedCols = 32
# MAGIC );
# MAGIC

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO users.nakhoe_kim.uc_grants_snapshot
# MAGIC WITH base AS (
# MAGIC   -- CATALOG
# MAGIC   SELECT
# MAGIC     'CATALOG' AS object_type,
# MAGIC     catalog_name AS object_catalog,
# MAGIC     NULL AS object_schema,
# MAGIC     NULL AS object_name,
# MAGIC     concat('`', catalog_name, '`') AS object_full_name,
# MAGIC     grantee AS principal,
# MAGIC     privilege_type AS privilege
# MAGIC   FROM system.information_schema.catalog_privileges
# MAGIC
# MAGIC   UNION ALL
# MAGIC   -- SCHEMA
# MAGIC   SELECT
# MAGIC     'SCHEMA',
# MAGIC     catalog_name,
# MAGIC     schema_name,
# MAGIC     NULL,
# MAGIC     concat('`', catalog_name, '`.`', schema_name, '`') AS object_full_name,
# MAGIC     grantee,
# MAGIC     privilege_type
# MAGIC   FROM system.information_schema.schema_privileges
# MAGIC
# MAGIC   UNION ALL
# MAGIC   -- TABLE
# MAGIC   SELECT
# MAGIC     'TABLE',
# MAGIC     table_catalog,
# MAGIC     table_schema,
# MAGIC     table_name,
# MAGIC     concat('`', table_catalog, '`.`', table_schema, '`.`', table_name, '`') AS object_full_name,
# MAGIC     grantee,
# MAGIC     privilege_type
# MAGIC   FROM system.information_schema.table_privileges
# MAGIC
# MAGIC   UNION ALL
# MAGIC   -- VOLUME
# MAGIC   SELECT
# MAGIC     'VOLUME',
# MAGIC     volume_catalog,
# MAGIC     volume_schema,
# MAGIC     volume_name,
# MAGIC     concat('`', volume_catalog, '`.`', volume_schema, '`.`', volume_name, '`') AS object_full_name,
# MAGIC     grantee,
# MAGIC     privilege_type
# MAGIC   FROM system.information_schema.volume_privileges
# MAGIC
# MAGIC )
# MAGIC
# MAGIC SELECT
# MAGIC   current_date()      AS snapshot_date,
# MAGIC   current_timestamp() AS snapshot_ts,
# MAGIC   'e2-demo-dev'            AS env,
# MAGIC   '1444828305810485'   AS workspace_id,
# MAGIC   'daily_job_id'     AS source_job_run_id,
# MAGIC   'admin'      AS collector,
# MAGIC
# MAGIC   object_type,
# MAGIC   object_catalog,
# MAGIC   object_schema,
# MAGIC   object_name,
# MAGIC   object_full_name,
# MAGIC   principal,
# MAGIC   privilege,
# MAGIC
# MAGIC   NULL AS raw_object_type,
# MAGIC   NULL AS raw_object_key
# MAGIC FROM base
# MAGIC WHERE object_catalog NOT LIKE "samples" and object_catalog NOT LIKE "system" and object_catalog NOT LIKE "__databricks_internal%"
# MAGIC and object_schema NOT LIKE "information_schema"
# MAGIC ORDER BY object_type, object_catalog, object_schema, object_name;
# MAGIC
# Databricks notebook source
# MAGIC %sql
# MAGIC -- example: store it in users.nakhoe_kim schema
# MAGIC -- please change them if you use your own schema
# MAGIC CREATE TABLE IF NOT EXISTS users.nakhoe_kim.uc_grants_drift (
# MAGIC   drift_date       DATE      NOT NULL,
# MAGIC   drift_ts         TIMESTAMP NOT NULL,
# MAGIC   env              STRING    NOT NULL,
# MAGIC   workspace_id     STRING,
# MAGIC
# MAGIC   change_type      STRING    NOT NULL COMMENT 'ADDED|REMOVED',
# MAGIC
# MAGIC   object_type      STRING    NOT NULL,
# MAGIC   object_full_name STRING    NOT NULL,
# MAGIC   principal        STRING    NOT NULL,
# MAGIC   privilege        STRING    NOT NULL,
# MAGIC
# MAGIC   -- for tracking/operation
# MAGIC   source_snapshot_date DATE  NOT NULL,
# MAGIC   prev_snapshot_date   DATE  NOT NULL,
# MAGIC   source_job_run_id    STRING
# MAGIC )
# MAGIC USING DELTA
# MAGIC PARTITIONED BY (drift_date)
# MAGIC TBLPROPERTIES (
# MAGIC   delta.autoOptimize.optimizeWrite = true,
# MAGIC   delta.autoOptimize.autoCompact   = true
# MAGIC );

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO users.nakhoe_kim.uc_grants_drift
# MAGIC SELECT
# MAGIC   current_date()                           AS drift_date,
# MAGIC   current_timestamp()                      AS drift_ts,
# MAGIC   t.env,
# MAGIC   t.workspace_id,
# MAGIC   'ADDED'                                  AS change_type,
# MAGIC   t.object_type,
# MAGIC   t.object_full_name,
# MAGIC   t.principal,
# MAGIC   t.privilege,
# MAGIC   t.snapshot_date                          AS source_snapshot_date,
# MAGIC   date_sub(t.snapshot_date, 1)             AS prev_snapshot_date,
# MAGIC   t.source_job_run_id
# MAGIC FROM users.nakhoe_kim..uc_grants_snapshot t
# MAGIC LEFT ANTI JOIN users.nakhoe_kim.uc_grants_snapshot y
# MAGIC   ON y.snapshot_date      = date_sub(t.snapshot_date, 1)
# MAGIC  AND y.env                = t.env
# MAGIC  AND coalesce(y.workspace_id,'') = coalesce(t.workspace_id,'')
# MAGIC  AND y.object_type        = t.object_type
# MAGIC  AND y.object_full_name   = t.object_full_name
# MAGIC  AND y.principal          = t.principal
# MAGIC  AND y.privilege          = t.privilege
# MAGIC WHERE t.snapshot_date = current_date();

# COMMAND ----------

# MAGIC %sql
# MAGIC INSERT INTO users.nakhoe_kim.uc_grants_drift
# MAGIC SELECT
# MAGIC   current_date()                           AS drift_date,
# MAGIC   current_timestamp()                      AS drift_ts,
# MAGIC   y.env,
# MAGIC   y.workspace_id,
# MAGIC   'REMOVED'                                AS change_type,
# MAGIC   y.object_type,
# MAGIC   y.object_full_name,
# MAGIC   y.principal,
# MAGIC   y.privilege,
# MAGIC   current_date()                           AS source_snapshot_date,
# MAGIC   y.snapshot_date                          AS prev_snapshot_date,
# MAGIC   y.source_job_run_id
# MAGIC FROM users.nakhoe_kim.uc_grants_snapshot y
# MAGIC LEFT ANTI JOIN users.nakhoe_kim.uc_grants_snapshot t
# MAGIC   ON t.snapshot_date      = current_date()
# MAGIC  AND t.env                = y.env
# MAGIC  AND coalesce(t.workspace_id,'') = coalesce(y.workspace_id,'')
# MAGIC  AND t.object_type        = y.object_type
# MAGIC  AND t.object_full_name   = y.object_full_name
# MAGIC  AND t.principal          = y.principal
# MAGIC  AND t.privilege          = y.privilege
# MAGIC WHERE y.snapshot_date = date_sub(current_date(), 1);
# MAGIC
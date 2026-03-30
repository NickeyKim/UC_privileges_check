# UC Privileges Check

A Databricks Asset Bundle project that takes daily snapshots of Unity Catalog grants and automatically detects privilege drift compared to the previous day.

> **[Korean version (한국어)](README_ko.md)**

## Overview

This solution collects privileges granted to Unity Catalog objects (Catalog, Schema, Table, Volume) on a daily basis, stores them in a Delta table, and compares them against the previous day's snapshot to automatically detect **ADDED** or **REMOVED** privileges.

## Architecture

```
system.information_schema
  ├── catalog_privileges
  ├── schema_privileges          ┌─────────────────────────┐
  ├── table_privileges    ──────▶│  uc_grants_snapshot     │──┐
  └── volume_privileges          │  (Daily append-only)    │  │  Compare
                                 └─────────────────────────┘  │  today vs yesterday
                                                              ▼
                                 ┌─────────────────────────┐
                                 │  uc_grants_drift        │
                                 │  (ADDED / REMOVED)      │
                                 └─────────────────────────┘
```

## Job Pipeline

A two-step sequential pipeline orchestrated as a Databricks Workflow.

| Task | Notebook | Description |
|------|----------|-------------|
| **Task 1** | `01. CREATE UC_GRANT_SNAPSHOT TABLE` | Creates the `uc_grants_snapshot` table and collects current privileges from 4 `information_schema` views (catalog/schema/table/volume) via INSERT |
| **Task 2** | `02. SELECT AND CREATE TABLES of ALL PRIVILEGES` | Creates the `uc_grants_drift` table and compares today's snapshot with the previous day's using `LEFT ANTI JOIN` to INSERT ADDED/REMOVED changes |

## Table Schemas

### `uc_grants_snapshot` (Privilege Snapshot)

| Column | Type | Description |
|--------|------|-------------|
| `snapshot_date` | DATE | Snapshot partition date (UTC) |
| `snapshot_ts` | TIMESTAMP | Snapshot timestamp |
| `env` | STRING | Environment label (DEV/STG/PRD) |
| `workspace_id` | STRING | Databricks Workspace ID |
| `object_type` | STRING | Object type (CATALOG, SCHEMA, TABLE, VOLUME) |
| `object_full_name` | STRING | Fully-qualified object name (e.g., `` `cat`.`sch`.`tbl` ``) |
| `principal` | STRING | Grantee (user/group/service principal) |
| `privilege` | STRING | Privilege type (SELECT, USE_SCHEMA, OWN, MODIFY, etc.) |

### `uc_grants_drift` (Privilege Drift Detection)

| Column | Type | Description |
|--------|------|-------------|
| `drift_date` | DATE | Drift detection date |
| `change_type` | STRING | Change type: `ADDED` or `REMOVED` |
| `object_type` | STRING | Object type |
| `object_full_name` | STRING | Fully-qualified object name |
| `principal` | STRING | Grantee |
| `privilege` | STRING | Privilege type |
| `source_snapshot_date` | DATE | Reference snapshot date |
| `prev_snapshot_date` | DATE | Previous day's snapshot date |

## Dashboard

A **Lakeview dashboard** (`UC Privileges Changes Dashboard`) is included and deployed as part of the bundle. It visualizes:

- Today's ADDED / REMOVED privilege counts
- Detailed drift summary (change type, environment, object, principal, privilege)
- Historical privilege change trends

The dashboard definition is stored at `src/uc_privileges_changes_dashboard.lvdash.json` and configured in `resources/uc_privileges_changes_dashboard.yml`.

## Project Structure

```
uc_privileges_check/
├── databricks.yml                          # DAB bundle config (dev/prod targets)
├── resources/
│   ├── dmp_dev_serverless_change_uc_privileges.job.yml      # Job definition (schedule, tasks)
│   └── uc_privileges_changes_dashboard.yml                  # Lakeview dashboard resource
├── src/
│   ├── 01. CREATE UC_GRANT_SNAPSHOT TABLE.py                # Snapshot collection notebook
│   ├── 02. SELECT AND CREATE TABLES of ALL PRIVILEGES from the catalog.py  # Drift detection notebook
│   └── uc_privileges_changes_dashboard.lvdash.json          # Lakeview dashboard definition
└── scratch/
    └── exploration.ipynb                   # Exploration notebook
```

## Getting Started

### Prerequisites

- [Databricks CLI](https://docs.databricks.com/dev-tools/cli/databricks-cli.html) v0.18+
- A Databricks Workspace with Unity Catalog enabled
- Read access to `system.information_schema.*_privileges` views

### Configuration

1. Set up Databricks CLI authentication:
   ```bash
   databricks configure
   ```

2. Update the workspace host in `databricks.yml` to match your environment:
   ```yaml
   workspace:
     host: https://<your-workspace>.cloud.databricks.com
   ```

3. Update the schema/table names in the notebooks to match your environment:
   - `users.nakhoe_kim` -> your schema name
   - Update `env` and `workspace_id` values

### Deploy & Run

```bash
# Deploy to development
databricks bundle deploy --target dev

# Run the job
databricks bundle run dmp_dev_serverless_change_uc_privileges --target dev

# Deploy to production
databricks bundle deploy --target prod
```

## Schedule

The job is configured to run **daily at 9:00 AM (KST)** by default.
- Cron: `16 0 9 * * ?` (Asia/Seoul)
- The schedule is automatically PAUSED in development mode.

## Drift Detection Logic

- **ADDED**: Privileges that exist in today's snapshot but not in yesterday's
- **REMOVED**: Privileges that existed in yesterday's snapshot but not in today's

Comparison key: `env` + `workspace_id` + `object_type` + `object_full_name` + `principal` + `privilege`

## Notes

- The snapshot table is recommended to be operated in **append-only** mode.
- The `samples`, `system`, and `__databricks_internal` catalogs, as well as `information_schema` schemas, are excluded from collection.
- Tested on Databricks Serverless Notebooks.

# 51 Canonical Futures Tick Database

## Issue

- GitHub issue: [#51](https://github.com/tgrytnes/TradeResearch/issues/51)
- Branch: `feat/51-canonical-futures-tick-database`
- Status: in progress

## Goal

Select and set up the canonical SQL-backed market-data store so TradeResearch can ingest and query long-horizon futures tick data with durable traceability.

## Scope

- In scope:
  - local ClickHouse provisioning for the raw market-data layer
  - initial canonical schema for futures contracts and raw tick or quote events
  - representative sample data and a reproducible smoke-test script
  - ADR documentation for storage and source-of-truth boundaries
  - runbook and README updates for local setup
- Out of scope:
  - full 13-year historical backfill
  - cleaning rules, roll logic, and feature generation
  - PostgreSQL application-store implementation
  - UI or run-tracking integration

## Implementation Summary

- Added a local ClickHouse Docker Compose setup for the canonical raw market-data layer.
- Defined the first ClickHouse schema for contract metadata and append-only futures tick events with contract-specific truth and ingest provenance.
- Added sample CSV data and a smoke-test script that provisions ClickHouse, applies the schema, loads sample data, and verifies range and instrument-filtered queries.
- Recorded the storage decision in a dedicated ADR and added a runbook for local setup.
- Key files involved:
  - [../../infra/clickhouse/docker-compose.yml](../../infra/clickhouse/docker-compose.yml)
  - [../../infra/clickhouse/sql/001_market_data.sql](../../infra/clickhouse/sql/001_market_data.sql)
  - [../../infra/clickhouse/samples/futures_contracts_sample.csv](../../infra/clickhouse/samples/futures_contracts_sample.csv)
  - [../../infra/clickhouse/samples/futures_ticks_sample.csv](../../infra/clickhouse/samples/futures_ticks_sample.csv)
  - [../../scripts/verify_clickhouse_smoke.sh](../../scripts/verify_clickhouse_smoke.sh)
  - [../architecture/adr-001-storage-and-source-of-truth.md](../architecture/adr-001-storage-and-source-of-truth.md)
  - [../runbooks/clickhouse-local-setup.md](../runbooks/clickhouse-local-setup.md)

## Tests

- Unit: not applicable yet
- Integration:
  - `./scripts/verify_clickhouse_smoke.sh`
- E2E: not applicable yet
- Manual verification:
  - start local ClickHouse with Docker Compose
  - load sample contracts and ticks
  - confirm date-range and symbol-filtered queries succeed

## Debugging Notes

- Symptoms observed:
  - Epic 2 had no concrete database setup or reproducible market-data verification path
- Root cause:
  - storage selection and source-of-truth boundaries had not yet been materialized into repo artifacts
- Failure modes to watch:
  - future stories may overload the raw tick table with derived features instead of creating downstream layers
  - ingest pipelines may drift if provider-specific parsing is not normalized before insert
  - continuous contract logic may accidentally replace contract-specific raw truth

## Documentation Updated

- Docs changed:
  - [../../README.md](../../README.md)
  - [../README.md](../README.md)
  - [../runbooks/clickhouse-local-setup.md](../runbooks/clickhouse-local-setup.md)
  - [./51-canonical-futures-tick-database.md](./51-canonical-futures-tick-database.md)
- Runbooks changed:
  - [../runbooks/clickhouse-local-setup.md](../runbooks/clickhouse-local-setup.md)
- Architecture notes changed:
  - [../architecture/01-research-platform-architecture.md](../architecture/01-research-platform-architecture.md)
  - [../architecture/adr-001-storage-and-source-of-truth.md](../architecture/adr-001-storage-and-source-of-truth.md)

## Follow-ups

- Remaining risks:
  - no provider-specific ingest parser is implemented yet
  - no archive automation exists yet for cold Parquet exports
- Deferred work:
  - roll handling and canonical session boundaries
  - data quality diagnostics and anomaly checks
  - PostgreSQL application-store implementation
- New issues to open:
  - ingest story for provider-to-canonical tick normalization
  - data quality and diagnostics story for Epic 2
  - PostgreSQL metadata store story under Epic 1 or Epic 7

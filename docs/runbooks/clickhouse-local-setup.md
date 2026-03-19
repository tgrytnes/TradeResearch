# ClickHouse Local Setup

This runbook documents the local market-data setup introduced for issue [#51](https://github.com/tgrytnes/TradeResearch/issues/51).

## Purpose

Provide a reproducible local or dev environment for the canonical raw futures tick store used by Epic 2.

## Files

- [../../infra/clickhouse/docker-compose.yml](../../infra/clickhouse/docker-compose.yml)
- [../../infra/clickhouse/sql/001_market_data.sql](../../infra/clickhouse/sql/001_market_data.sql)
- [../../infra/clickhouse/samples/futures_contracts_sample.csv](../../infra/clickhouse/samples/futures_contracts_sample.csv)
- [../../infra/clickhouse/samples/futures_ticks_sample.csv](../../infra/clickhouse/samples/futures_ticks_sample.csv)
- [../../scripts/verify_clickhouse_smoke.sh](../../scripts/verify_clickhouse_smoke.sh)

## Quick Start

Start ClickHouse:

```bash
docker compose -f infra/clickhouse/docker-compose.yml up -d
```

Run the reproducible smoke test:

```bash
./scripts/verify_clickhouse_smoke.sh
```

Keep the database running after the smoke test:

```bash
KEEP_RUNNING=1 ./scripts/verify_clickhouse_smoke.sh
```

Stop and remove the local environment:

```bash
docker compose -f infra/clickhouse/docker-compose.yml down -v
```

## Canonical Raw Model

The local setup establishes two tables:

- `market_data.futures_contracts`
- `market_data.futures_ticks`

Design rules:

- raw truth is contract-specific, not continuous-series-adjusted
- timestamps are stored in UTC using `DateTime64(6)`
- partitioning is monthly by `trading_day`
- the primary sort key favors instrument and date-range research queries
- source-file provenance is stored on every raw event row

## What This Does Not Do Yet

- full 13-year backfill
- cold archive automation to Parquet or object storage
- continuous-contract views
- roll logic, cleaning rules, or representation-ready derived tables
- workspace metadata storage in PostgreSQL

Those follow-on decisions remain part of later Epic 2 and Epic 3 work.

# ADR-001 Storage and Source-of-Truth

- Status: accepted
- Date: 2026-03-19
- Related issues: [#2](https://github.com/tgrytnes/TradeResearch/issues/2), [#51](https://github.com/tgrytnes/TradeResearch/issues/51)

## Context

TradeResearch needs a durable market-data foundation for long-horizon futures tick research. The expected workload is append-heavy historical ingest plus analytical scans by instrument, contract, and date range. The repository also needs a clear source-of-truth split so raw market events, application metadata, and artifacts do not blur together.

The initial target is roughly 13 years of futures tick data. Depending on the event scope, that implies billions of rows over time:

- trades only: large but manageable on a single analytical node
- trades plus top-of-book quotes: materially larger
- full depth or order-book updates: another order of magnitude beyond that

## Decision

TradeResearch adopts a split storage model:

1. ClickHouse is the canonical SQL-backed store for raw futures tick and quote events.
2. Raw market truth is contract-specific and timestamped in UTC.
3. Continuous contracts, bars, derived features, and research representations are downstream products, not raw truth.
4. Source-file provenance must be stored on every ingest row so prepared outputs remain traceable.
5. Workspace metadata, research definitions, runs, and findings should live in a separate relational application store later, expected to be PostgreSQL.
6. Parquet remains a preferred interchange and archive format for cold storage and local analytics, but it is not the canonical shared market database.

## Canonical Raw Layout

The initial raw market schema uses:

- `market_data.futures_contracts` for contract metadata
- `market_data.futures_ticks` for append-only trade and quote events

Physical layout rules:

- partition by month using `toYYYYMM(trading_day)`
- order by `(root_symbol, contract_id, trading_day, ts_exchange, sequence)`
- store timestamps as `DateTime64(6, 'UTC')`
- keep provider, source file, and ingest-run lineage on each event row

## Alternatives Considered

## PostgreSQL or TimescaleDB as the primary raw store

Rejected as the default for Epic 2. This option is simpler operationally and remains viable for smaller datasets, but the dominant workload here is large-scale analytical scans across long horizons rather than OLTP-style relational transactions.

## DuckDB or Parquet-only storage

Rejected as the canonical shared store. DuckDB and Parquet are strong complements for local research and archives, but a file-only approach is weaker as the single durable system of record for repeatable ingest, lineage, and multi-step preparation workflows.

## Consequences

Positive:

- aligns the raw market layer with append-heavy analytical workloads
- keeps market truth separate from application and UI concerns
- preserves a clean path to later PostgreSQL-backed metadata and workflow features
- leaves Parquet available for interchange and cold-storage workflows
- allows continuous futures series to be materialized as derived products with explicit roll schedules rather than hidden vendor transformations

Negative:

- introduces a second database technology into the architecture
- requires Docker or equivalent local runtime support
- pushes relational workflow metadata into later implementation work

## Follow-up Implications

- Epic 2 follow-on stories should define ingestion, roll handling, cleaning rules, and data quality diagnostics against the ClickHouse raw layer.
- Epic 3 should treat derived market-state representations as downstream from the raw contract-specific truth.
- A later story should formalize the PostgreSQL application store for workspace entities, runs, and findings.

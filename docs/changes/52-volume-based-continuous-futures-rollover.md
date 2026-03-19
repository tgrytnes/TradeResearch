# 52 Volume-Based Continuous Futures Rollover

## Issue

- GitHub issue: [#52](https://github.com/tgrytnes/TradeResearch/issues/52)
- Branch: `feat/52-volume-based-rollover-backadjust`
- Status: in progress

## Goal

Build a volume-based continuous futures chain with arithmetic back-adjustment while preserving raw contract-specific ticks as the market-data source of truth.

## Scope

- In scope:
  - Sierra Chart raw tick import for contract-specific futures CSV files
  - roll policy configuration for `FDAX`
  - roll schedule generation with walk-forward logic and hard cutoff handling
  - derived continuous tick series with raw stitched and adjusted prices
  - synthetic overlap verification and real-data import diagnostics
- Out of scope:
  - live trading roll execution
  - commission and slippage modeling
  - weighted or ratio-adjusted continuous series variants
  - exchange-calendar completeness for all futures products

## Implementation Summary

- Added a policy configuration for `FDAX` rollover rules.
- Extended the ClickHouse schema to preserve Sierra Chart source fields and to store roll schedules plus continuous-series output.
- Added a Sierra Chart importer that loads raw contract ticks into ClickHouse with deterministic contract metadata and provenance.
- Added a continuous-series builder that:
  - enforces expected adjacent cycle months
  - uses session volume confirmation for roll selection
  - applies a cash-settled hard cutoff
  - computes arithmetic back-adjustments
- Added verification assets for both synthetic overlapping contracts and the real March-only FDAX files supplied by the user.
- Key files involved:
  - [../../config/futures_roll_policies.json](../../config/futures_roll_policies.json)
  - [../../infra/clickhouse/sql/002_continuous_futures.sql](../../infra/clickhouse/sql/002_continuous_futures.sql)
  - [../../scripts/import_sierra_chart_ticks.py](../../scripts/import_sierra_chart_ticks.py)
  - [../../scripts/build_continuous_futures.py](../../scripts/build_continuous_futures.py)
  - [../../scripts/verify_continuous_contracts.py](../../scripts/verify_continuous_contracts.py)
  - [../runbooks/continuous-futures-rollover.md](../runbooks/continuous-futures-rollover.md)

## Tests

- Unit: policy and contract parsing covered indirectly through scripted verification
- Integration:
  - `./scripts/verify_continuous_contracts.sh`
- E2E: not applicable yet
- Manual verification:
  - compare original CSV row ranges and volumes to imported ClickHouse results
  - inspect roll schedule rows for synthetic quarterly contracts
  - confirm adjusted synthetic roll prices align across roll boundaries
  - confirm real March-only contracts are rejected as an invalid quarterly chain

## Debugging Notes

- Symptoms observed:
  - the provided FDAX source directory contains only `H` contracts, which is insufficient for a valid quarterly front-contract chain
- Root cause:
  - intermediate quarterly contracts such as `M`, `U`, and `Z` are absent from the source path
- Failure modes to watch:
  - silently skipping missing cycle months would create a false continuous series
  - using non-overlapping contracts for roll spreads would fabricate adjustments
  - provider files that aggregate multiple prints per row must preserve source fields instead of pretending to be pure one-trade ticks

## Documentation Updated

- Docs changed:
  - [../../README.md](../../README.md)
  - [../runbooks/continuous-futures-rollover.md](../runbooks/continuous-futures-rollover.md)
  - [./52-volume-based-continuous-futures-rollover.md](./52-volume-based-continuous-futures-rollover.md)
- Runbooks changed:
  - [../runbooks/continuous-futures-rollover.md](../runbooks/continuous-futures-rollover.md)
- Architecture notes changed:
  - [../architecture/adr-001-storage-and-source-of-truth.md](../architecture/adr-001-storage-and-source-of-truth.md)

## Follow-ups

- Remaining risks:
  - exact exchange-calendar rules are still simplified for non-FDAX products
  - settlement fallback currently uses session-close rather than official settlement prices
- Deferred work:
  - full-quarter real-data verification once adjacent contracts are available
  - support for alternative continuous-series variants
- New issues to open:
  - vendor-settlement import story for roll pricing
  - exchange-calendar and notice-date policy story for deliverable contracts

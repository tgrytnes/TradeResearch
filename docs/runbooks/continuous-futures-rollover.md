# Continuous Futures Rollover

This runbook documents the rollover and back-adjustment workflow introduced for issue [#52](https://github.com/tgrytnes/TradeResearch/issues/52).

## Purpose

Build a derived continuous futures series from raw contract-specific futures ticks without changing the raw source-of-truth tables.

## Files

- [../../config/futures_roll_policies.json](../../config/futures_roll_policies.json)
- [../../infra/clickhouse/sql/002_continuous_futures.sql](../../infra/clickhouse/sql/002_continuous_futures.sql)
- [../../scripts/import_sierra_chart_ticks.py](../../scripts/import_sierra_chart_ticks.py)
- [../../scripts/build_continuous_futures.py](../../scripts/build_continuous_futures.py)
- [../../scripts/verify_continuous_contracts.sh](../../scripts/verify_continuous_contracts.sh)

## Policy Model

Current rules for `FDAX`:

- cycle months: `H`, `M`, `U`, `Z`
- settlement type: cash-settled
- primary roll trigger: next contract volume exceeds current contract volume for 2 consecutive sessions
- hard cutoff: no later than 1 day before last trading day
- representative roll price: session close fallback
- adjustment method: arithmetic back-adjustment

## Workflow

1. Import contract-specific Sierra Chart files into `market_data.futures_contracts` and `market_data.futures_ticks`.
2. Build a roll schedule into `market_data.futures_roll_schedule`.
3. Materialize the derived stitched and back-adjusted tick series into `market_data.continuous_futures_ticks`.

The continuous table stores both:

- `raw_trade_price` for the unadjusted stitched lead-contract series
- `adjusted_trade_price` for the arithmetic back-adjusted research series

## Verification

Run the full verification suite:

```bash
./scripts/verify_continuous_contracts.sh
```

What it does:

- imports 3 synthetic quarterly contracts with overlapping volume profiles
- verifies the roll schedule and adjusted-price continuity
- imports `FDAXH21`, `FDAXH22`, and `FDAXH23` from the provided Sierra Chart directory
- confirms the raw import matches the source files
- confirms the continuous builder refuses to generate a false quarterly chain from March-only contracts

## Important Limitation

The provided real-data directory currently contains only March contracts. That is enough to verify:

- raw source inspection
- contract import
- chain-validation diagnostics

It is not enough to verify a valid quarterly front-contract continuous series. For that, the source directory also needs the adjacent quarterly contracts such as `FDAXM21`, `FDAXU21`, and `FDAXZ21`.

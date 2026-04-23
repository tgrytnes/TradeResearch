# Change Record: Validate Futures Tick Data Quality

## Summary
Implemented a durable tick-data quality validation layer for imported futures data.

## Changes
- Added `market_data.futures_tick_diagnostics` table to persist quality findings.
- Implemented anomaly detection for:
    - Abnormal price jumps
    - Invalid trade volume (zero or negative)
    - Duplicate timestamps
    - Out-of-order timestamps
    - Impossible price relationships (Bid > Ask)
    - Session gaps (low activity)
- Added synthetic anomaly generation and validation tests in `scripts/test_tick_quality.py`.

## Verification
- Unit tests with synthetic samples pass.
- Diagnostics correctly populate in the `futures_tick_diagnostics` table.
- Validated via `scripts/validate.sh`.

## Limitations
- Thresholds for price jumps and session gaps are currently hardcoded for sample data; these should be refined per instrument in future iterations.

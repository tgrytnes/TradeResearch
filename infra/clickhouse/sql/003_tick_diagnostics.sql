CREATE TABLE IF NOT EXISTS market_data.futures_tick_diagnostics
(
    root_symbol LowCardinality(String),
    contract_code LowCardinality(String),
    contract_id UInt32,
    trading_day Date,
    ts_start DateTime64(6, 'UTC'),
    ts_end Nullable(DateTime64(6, 'UTC')),
    check_name LowCardinality(String),
    severity Enum8('info' = 1, 'warning' = 2, 'critical' = 3),
    evidence String,
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (root_symbol, contract_id, trading_day, ts_start);

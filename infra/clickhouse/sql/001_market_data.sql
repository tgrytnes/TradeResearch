CREATE DATABASE IF NOT EXISTS market_data;

CREATE TABLE IF NOT EXISTS market_data.futures_contracts
(
    contract_id UInt32,
    root_symbol LowCardinality(String),
    contract_code LowCardinality(String),
    exchange LowCardinality(String),
    expiry_date Date,
    first_trade_date Nullable(Date),
    last_trade_date Nullable(Date),
    tick_size Decimal(18, 4),
    point_value Decimal(18, 2),
    currency LowCardinality(String),
    timezone LowCardinality(String),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (root_symbol, expiry_date, contract_id);

CREATE TABLE IF NOT EXISTS market_data.futures_ticks
(
    root_symbol LowCardinality(String),
    contract_code LowCardinality(String),
    contract_id UInt32,
    exchange LowCardinality(String),
    provider LowCardinality(String),
    ts_exchange DateTime64(6, 'UTC'),
    ts_received Nullable(DateTime64(6, 'UTC')),
    trading_day Date,
    sequence UInt64,
    event_type Enum8('trade' = 1, 'quote' = 2),
    trade_price Nullable(Decimal(18, 4)),
    trade_size Nullable(UInt32),
    bid_price Nullable(Decimal(18, 4)),
    bid_size Nullable(UInt32),
    ask_price Nullable(Decimal(18, 4)),
    ask_size Nullable(UInt32),
    source_file String,
    source_row_number UInt64,
    ingest_run_id UUID,
    ingested_at DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trading_day)
ORDER BY (root_symbol, contract_id, trading_day, ts_exchange, sequence)
SETTINGS index_granularity = 8192;

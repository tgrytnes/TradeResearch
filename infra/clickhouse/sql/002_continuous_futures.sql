ALTER TABLE market_data.futures_contracts
    ADD COLUMN IF NOT EXISTS first_notice_date Nullable(Date) AFTER last_trade_date;

ALTER TABLE market_data.futures_contracts
    ADD COLUMN IF NOT EXISTS settlement_type Enum8('cash_settled' = 1, 'deliverable' = 2) DEFAULT 'cash_settled' AFTER first_notice_date;

ALTER TABLE market_data.futures_contracts
    ADD COLUMN IF NOT EXISTS source_path String DEFAULT '' AFTER timezone;

ALTER TABLE market_data.futures_ticks
    ADD COLUMN IF NOT EXISTS source_open Nullable(Decimal(18, 4)) AFTER event_type;

ALTER TABLE market_data.futures_ticks
    ADD COLUMN IF NOT EXISTS source_high Nullable(Decimal(18, 4)) AFTER source_open;

ALTER TABLE market_data.futures_ticks
    ADD COLUMN IF NOT EXISTS source_low Nullable(Decimal(18, 4)) AFTER source_high;

ALTER TABLE market_data.futures_ticks
    ADD COLUMN IF NOT EXISTS source_last Nullable(Decimal(18, 4)) AFTER source_low;

ALTER TABLE market_data.futures_ticks
    ADD COLUMN IF NOT EXISTS source_number_of_trades Nullable(UInt32) AFTER source_last;

ALTER TABLE market_data.futures_ticks
    ADD COLUMN IF NOT EXISTS source_bid_volume Nullable(UInt32) AFTER source_number_of_trades;

ALTER TABLE market_data.futures_ticks
    ADD COLUMN IF NOT EXISTS source_ask_volume Nullable(UInt32) AFTER source_bid_volume;

CREATE TABLE IF NOT EXISTS market_data.futures_roll_schedule
(
    chain_symbol LowCardinality(String),
    root_symbol LowCardinality(String),
    old_contract_code LowCardinality(String),
    new_contract_code LowCardinality(String),
    old_contract_id UInt32,
    new_contract_id UInt32,
    trigger_date Date,
    effective_trading_day Date,
    effective_ts DateTime64(6, 'UTC'),
    trigger_reason LowCardinality(String),
    old_daily_volume UInt64,
    new_daily_volume UInt64,
    consecutive_sessions UInt8,
    representative_old_price Decimal(18, 4),
    representative_new_price Decimal(18, 4),
    adjustment_amount Decimal(18, 4),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
ORDER BY (root_symbol, chain_symbol, trigger_date, old_contract_code, new_contract_code);

CREATE TABLE IF NOT EXISTS market_data.continuous_futures_ticks
(
    chain_symbol LowCardinality(String),
    root_symbol LowCardinality(String),
    source_contract_code LowCardinality(String),
    source_contract_id UInt32,
    exchange LowCardinality(String),
    provider LowCardinality(String),
    ts_exchange DateTime64(6, 'UTC'),
    trading_day Date,
    sequence UInt64,
    raw_trade_price Nullable(Decimal(18, 4)),
    adjusted_trade_price Nullable(Decimal(18, 4)),
    trade_size Nullable(UInt32),
    source_file String,
    source_row_number UInt64,
    cumulative_adjustment Decimal(18, 4),
    segment_number UInt32,
    reference_contract_code LowCardinality(String),
    created_at DateTime DEFAULT now()
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(trading_day)
ORDER BY (root_symbol, chain_symbol, trading_day, ts_exchange, sequence);

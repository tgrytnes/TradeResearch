-- 1. Invalid Volume
INSERT INTO market_data.futures_tick_diagnostics (root_symbol, contract_code, contract_id, trading_day, ts_start, ts_end, check_name, severity, evidence)
SELECT
    root_symbol, contract_code, contract_id, trading_day, ts_exchange, NULL,
    'invalid_volume', 'warning',
    concat('Trade size is ', toString(trade_size))
FROM market_data.futures_ticks
WHERE event_type = 'trade' AND (trade_size <= 0 OR trade_size IS NULL);

-- 2. Impossible Price Relationship (Bid > Ask)
INSERT INTO market_data.futures_tick_diagnostics (root_symbol, contract_code, contract_id, trading_day, ts_start, ts_end, check_name, severity, evidence)
SELECT
    root_symbol, contract_code, contract_id, trading_day, ts_exchange, NULL,
    'impossible_price_relationship', 'critical',
    concat('Bid price (', toString(bid_price), ') > Ask price (', toString(ask_price), ')')
FROM market_data.futures_ticks
WHERE bid_price > ask_price;

-- 3. Duplicate Timestamps
INSERT INTO market_data.futures_tick_diagnostics (root_symbol, contract_code, contract_id, trading_day, ts_start, ts_end, check_name, severity, evidence)
SELECT
    root_symbol, contract_code, contract_id, trading_day, ts_exchange, NULL,
    'duplicate_timestamp', 'warning',
    'Duplicate timestamp detected'
FROM (
    SELECT root_symbol, contract_code, contract_id, trading_day, ts_exchange, count() as cnt
    FROM market_data.futures_ticks
    GROUP BY root_symbol, contract_code, contract_id, trading_day, ts_exchange
    HAVING cnt > 1
);

-- 4. Out-of-Order Timestamps
INSERT INTO market_data.futures_tick_diagnostics (root_symbol, contract_code, contract_id, trading_day, ts_start, ts_end, check_name, severity, evidence)
SELECT
    root_symbol, contract_code, contract_id, trading_day, ts_exchange, NULL,
    'out_of_order_timestamp', 'warning',
    concat('Timestamp ', toString(ts_exchange), ' is out of order relative to sequence ', toString(sequence))
FROM (
    SELECT *,
           any(ts_exchange) OVER (PARTITION BY contract_id ORDER BY sequence ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_ts
    FROM market_data.futures_ticks
)
WHERE ts_exchange < prev_ts;

-- 5. Abnormal Price Jump
-- Using a threshold of 10.0 for this sample (tick size 0.25)
INSERT INTO market_data.futures_tick_diagnostics (root_symbol, contract_code, contract_id, trading_day, ts_start, ts_end, check_name, severity, evidence)
SELECT
    root_symbol, contract_code, contract_id, trading_day, ts_exchange, NULL,
    'abnormal_price_jump', 'critical',
    concat('Price jump from ', toString(prev_price), ' to ', toString(trade_price))
FROM (
    SELECT *,
           any(trade_price) OVER (PARTITION BY contract_id ORDER BY sequence ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_price
    FROM market_data.futures_ticks
    WHERE event_type = 'trade'
)
WHERE abs(trade_price - prev_price) > 10.0;

-- 6. Session Gap
-- Using a threshold of 15 minutes (900 seconds)
INSERT INTO market_data.futures_tick_diagnostics (root_symbol, contract_code, contract_id, trading_day, ts_start, ts_end, check_name, severity, evidence)
SELECT
    root_symbol, contract_code, contract_id, trading_day, ts_exchange, NULL,
    'session_gap', 'warning',
    concat('Gap of ', toString(dateDiff('second', prev_ts, ts_exchange)), ' seconds detected')
FROM (
    SELECT *,
           any(ts_exchange) OVER (PARTITION BY contract_id ORDER BY sequence ROWS BETWEEN 1 PRECEDING AND 1 PRECEDING) as prev_ts
    FROM market_data.futures_ticks
)
WHERE dateDiff('second', prev_ts, ts_exchange) > 900;

import csv
from datetime import datetime, timedelta

def generate_anomalous_ticks():
    # Contract: ESZ24 (S&P 500 Dec 2024)
    # Tick size: 0.25
    root_symbol = "ES"
    contract_code = "ESZ24"
    exchange = "CME"
    provider = "SIERRA"

    start_ts = datetime(2024, 12, 1, 10, 0, 0)

    # Header: root_symbol, contract_code, contract_id, exchange, provider, ts_exchange, trading_day, sequence, event_type, trade_price, trade_size, bid_price, bid_size, ask_price, ask_size
    header = ["root_symbol", "contract_code", "contract_id", "exchange", "provider", "ts_exchange", "trading_day", "sequence", "event_type", "trade_price", "trade_size", "bid_price", "bid_size", "ask_price", "ask_size"]

    rows = []

    # 1. Normal ticks (baseline)
    for i in range(10):
        ts = start_ts + timedelta(seconds=i)
        rows.append([root_symbol, contract_code, 101, exchange, provider, ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', i, 'trade', 5000.00 + (i * 0.25), 1, 5000.00 + (i * 0.25), 1, 5000.25 + (i * 0.25), 1])

    # 2. Abnormal Price Jump (Price jumps from 5002.25 to 5100.00 in one tick)
    jump_ts = start_ts + timedelta(seconds=11)
    rows.append([root_symbol, contract_code, 101, exchange, provider, jump_ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', 11, 'trade', 5100.00, 1, 5099.75, 1, 5100.25, 1])

    # 3. Zero/Negative Volume (Trade size 0)
    vol_ts = start_ts + timedelta(seconds=12)
    rows.append([root_symbol, contract_code, 101, exchange, provider, vol_ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', 12, 'trade', 5100.25, 0, 5100.00, 1, 5100.50, 1])

    # 4. Duplicate/Out-of-order Timestamps
    # Duplicate TS
    dup_ts = start_ts + timedelta(seconds=13)
    rows.append([root_symbol, contract_code, 101, exchange, provider, dup_ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', 13, 'trade', 5100.50, 1, 5100.25, 1, 5100.75, 1])
    rows.append([root_symbol, contract_code, 101, exchange, provider, dup_ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', 14, 'trade', 5100.75, 1, 5100.50, 1, 5101.00, 1])

    # Out of order TS
    ooo_ts = start_ts + timedelta(seconds=12) # Earlier than previous
    rows.append([root_symbol, contract_code, 101, exchange, provider, ooo_ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', 15, 'trade', 5101.00, 1, 5100.75, 1, 5101.25, 1])

    # 5. Malformed OHLC/Impossible Price Relationships (Bid > Ask)
    mal_ts = start_ts + timedelta(seconds=14)
    rows.append([root_symbol, contract_code, 101, exchange, provider, mal_ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', 16, 'quote', None, None, 5102.00, 1, 5101.00, 1])

    # 6. Low Activity Session (Gap in time)
    # Jump from 10:00:14 to 10:30:00
    gap_ts = start_ts + timedelta(minutes=30)
    rows.append([root_symbol, contract_code, 101, exchange, provider, gap_ts.strftime('%Y-%m-%d %H:%M:%S.%f'), '2024-12-01', 17, 'trade', 5102.25, 1, 5102.00, 1, 5102.50, 1])

    return header, rows

if __name__ == "__main__":
    header, rows = generate_anomalous_ticks()
    with open("infra/clickhouse/samples/futures_ticks_anomalies.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print("Generated infra/clickhouse/samples/futures_ticks_anomalies.csv")

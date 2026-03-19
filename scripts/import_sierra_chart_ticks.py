#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
import uuid
from zoneinfo import ZoneInfo

from clickhouse_http import insert_json_rows, query_scalar
from futures_contracts import contract_id_for, load_roll_policy, parse_contract_filename, third_friday


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import Sierra Chart CSV ticks into ClickHouse.")
    parser.add_argument("--config", default="config/futures_roll_policies.json")
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--batch-size", type=int, default=5000)
    return parser.parse_args()


def decimal_or_none(value: str) -> float | None:
    if value == "" or value is None:
        return None
    return float(value)


def int_or_none(value: str) -> int | None:
    if value == "" or value is None:
        return None
    return int(value)


def format_ts(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")


def parse_source_datetime(date_value: str, time_value: str, local_timezone: ZoneInfo) -> datetime:
    timestamp = f"{date_value} {time_value}"
    for fmt in ("%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S"):
        try:
            return datetime.strptime(timestamp, fmt).replace(tzinfo=local_timezone)
        except ValueError:
            continue
    raise ValueError(f"Unsupported Sierra Chart timestamp: {timestamp}")


def ensure_contract_not_imported(contract_code: str) -> None:
    existing = query_scalar(
        f"SELECT count() FROM market_data.futures_contracts WHERE contract_code = '{contract_code}'"
    )
    if existing != "0":
        raise RuntimeError(f"Contract {contract_code} is already imported")


def import_file(file_path: Path, config_path: str, batch_size: int) -> dict:
    parsed = parse_contract_filename(file_path)
    policy = load_roll_policy(config_path, parsed.root_symbol)
    ensure_contract_not_imported(parsed.contract_code)

    timezone_name = policy["timezone"]
    local_timezone = ZoneInfo(timezone_name)
    ingest_run_id = str(uuid.uuid4())
    row_count = 0
    total_volume = 0
    first_trade_day = None
    last_trade_day = None
    first_source_timestamp = None
    last_source_timestamp = None
    batch: list[dict] = []

    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_dt = parse_source_datetime(row["Date"], row["Time"], local_timezone)
            ts_exchange = source_dt.astimezone(timezone.utc)
            trading_day = source_dt.date()
            row_count += 1
            total_volume += int(row["Volume"])
            first_trade_day = trading_day if first_trade_day is None else min(first_trade_day, trading_day)
            last_trade_day = trading_day if last_trade_day is None else max(last_trade_day, trading_day)
            first_source_timestamp = (
                source_dt if first_source_timestamp is None else min(first_source_timestamp, source_dt)
            )
            last_source_timestamp = (
                source_dt if last_source_timestamp is None else max(last_source_timestamp, source_dt)
            )

            batch.append(
                {
                    "root_symbol": parsed.root_symbol,
                    "contract_code": parsed.contract_code,
                    "contract_id": contract_id_for(parsed),
                    "exchange": parsed.exchange,
                    "provider": "sierra_chart",
                    "ts_exchange": format_ts(ts_exchange),
                    "ts_received": None,
                    "trading_day": trading_day.isoformat(),
                    "sequence": row_count,
                    "event_type": "trade",
                    "source_open": decimal_or_none(row["Open"]),
                    "source_high": decimal_or_none(row["High"]),
                    "source_low": decimal_or_none(row["Low"]),
                    "source_last": decimal_or_none(row["Last"]),
                    "source_number_of_trades": int_or_none(row["NumberOfTrades"]),
                    "source_bid_volume": int_or_none(row["BidVolume"]),
                    "source_ask_volume": int_or_none(row["AskVolume"]),
                    "trade_price": decimal_or_none(row["Last"]),
                    "trade_size": int_or_none(row["Volume"]),
                    "bid_price": None,
                    "bid_size": None,
                    "ask_price": None,
                    "ask_size": None,
                    "source_file": file_path.name,
                    "source_row_number": row_count,
                    "ingest_run_id": ingest_run_id,
                }
            )

            if len(batch) >= batch_size:
                insert_json_rows("market_data.futures_ticks", batch)
                batch.clear()

    if batch:
        insert_json_rows("market_data.futures_ticks", batch)

    if row_count == 0:
        raise RuntimeError(f"No rows found in {file_path}")

    expiry_date = third_friday(parsed.year, parsed.month)
    insert_json_rows(
        "market_data.futures_contracts",
        [
            {
                "contract_id": contract_id_for(parsed),
                "root_symbol": parsed.root_symbol,
                "contract_code": parsed.contract_code,
                "exchange": parsed.exchange,
                "expiry_date": expiry_date.isoformat(),
                "first_trade_date": first_trade_day.isoformat(),
                "last_trade_date": last_trade_day.isoformat(),
                "first_notice_date": None,
                "tick_size": policy["tick_size"],
                "point_value": policy["point_value"],
                "currency": policy["currency"],
                "timezone": timezone_name,
                "settlement_type": policy["settlement_type"],
                "source_path": str(file_path),
            }
        ],
    )

    return {
        "contract_code": parsed.contract_code,
        "rows": row_count,
        "total_volume": total_volume,
        "first_trade_day": first_trade_day.isoformat(),
        "last_trade_day": last_trade_day.isoformat(),
        "first_source_timestamp": first_source_timestamp.isoformat(),
        "last_source_timestamp": last_source_timestamp.isoformat(),
    }


def main() -> None:
    args = parse_args()
    summaries = []
    for file_name in args.files:
        summary = import_file(Path(file_name), args.config, args.batch_size)
        summaries.append(summary)

    for summary in summaries:
        print(
            f"Imported {summary['contract_code']}: rows={summary['rows']} "
            f"volume={summary['total_volume']} "
            f"range={summary['first_trade_day']}..{summary['last_trade_day']}"
        )


if __name__ == "__main__":
    main()

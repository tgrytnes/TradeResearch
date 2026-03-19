#!/usr/bin/env python3

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

from clickhouse_http import execute, insert_json_rows, query_json_rows
from futures_contracts import load_roll_policy, next_cycle_contract_code


@dataclass
class RollDecision:
    old_contract_code: str
    new_contract_code: str
    old_contract_id: int
    new_contract_id: int
    trigger_date: date
    effective_trading_day: date
    effective_ts: str
    trigger_reason: str
    old_daily_volume: int
    new_daily_volume: int
    consecutive_sessions: int
    representative_old_price: Decimal
    representative_new_price: Decimal
    adjustment_amount: Decimal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build volume-based continuous futures series.")
    parser.add_argument("--config", default="config/futures_roll_policies.json")
    parser.add_argument("--root-symbol", required=True)
    parser.add_argument("--chain-symbol", default=None)
    parser.add_argument("--contract-codes", nargs="*")
    parser.add_argument("--replace-output", action="store_true")
    return parser.parse_args()


def to_decimal(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"))


def to_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def fetch_contracts(root_symbol: str, contract_codes: list[str] | None) -> list[dict]:
    where = [f"root_symbol = '{root_symbol}'"]
    if contract_codes:
        code_list = ", ".join(f"'{code}'" for code in contract_codes)
        where.append(f"contract_code IN ({code_list})")
    return query_json_rows(
        f"""
        SELECT
            contract_id,
            root_symbol,
            contract_code,
            exchange,
            expiry_date,
            first_trade_date,
            last_trade_date,
            first_notice_date,
            settlement_type
        FROM market_data.futures_contracts
        WHERE {' AND '.join(where)}
        ORDER BY expiry_date
        """
    )


def fetch_daily_stats(root_symbol: str, contract_codes: list[str]) -> dict[str, dict[date, dict]]:
    code_list = ", ".join(f"'{code}'" for code in contract_codes)
    rows = query_json_rows(
        f"""
        SELECT
            contract_code,
            trading_day,
            sum(coalesce(trade_size, 0)) AS daily_volume,
            argMax(trade_price, ts_exchange) AS session_close
        FROM market_data.futures_ticks
        WHERE root_symbol = '{root_symbol}'
          AND event_type = 'trade'
          AND contract_code IN ({code_list})
        GROUP BY contract_code, trading_day
        ORDER BY contract_code, trading_day
        """
    )
    stats: dict[str, dict[date, dict]] = {}
    for row in rows:
        contract_code = row["contract_code"]
        trading_day = to_date(row["trading_day"])
        stats.setdefault(contract_code, {})[trading_day] = {
            "daily_volume": int(row["daily_volume"]),
            "session_close": to_decimal(row["session_close"]),
        }
    return stats


def fetch_min_timestamp(contract_code: str, trading_day: date) -> str:
    rows = query_json_rows(
        f"""
        SELECT min(ts_exchange) AS effective_ts
        FROM market_data.futures_ticks
        WHERE contract_code = '{contract_code}'
          AND trading_day = toDate('{trading_day.isoformat()}')
        """
    )
    effective_ts = rows[0]["effective_ts"]
    if effective_ts is None:
        raise RuntimeError(f"Missing effective timestamp for {contract_code} on {trading_day.isoformat()}")
    return effective_ts


def latest_allowed_roll_day(contract: dict, stats: dict[date, dict], policy: dict) -> date:
    if contract["settlement_type"] == "deliverable":
        if contract["first_notice_date"] is None:
            raise RuntimeError(f"Missing first_notice_date for deliverable contract {contract['contract_code']}")
        cutoff_target = to_date(contract["first_notice_date"])
    else:
        cutoff_target = to_date(contract["last_trade_date"])

    latest = cutoff_target - timedelta(days=policy["hard_cutoff_days_before_last_trade"])
    eligible_days = [day for day in stats if day <= latest]
    if not eligible_days:
        raise RuntimeError(
            f"No eligible roll days for {contract['contract_code']} before hard cutoff {latest.isoformat()}"
        )
    return max(eligible_days)


def build_roll_schedule(contracts: list[dict], daily_stats: dict[str, dict[date, dict]], policy: dict) -> list[RollDecision]:
    if len(contracts) < 2:
        raise RuntimeError("Need at least two contracts to build a continuous series")

    by_code = {contract["contract_code"]: contract for contract in contracts}
    schedules: list[RollDecision] = []
    for index, current in enumerate(contracts[:-1]):
        expected_next = next_cycle_contract_code(current["contract_code"], policy["cycle_months"])
        if expected_next not in by_code:
            raise RuntimeError(
                f"Expected next cycle contract {expected_next} after {current['contract_code']}, "
                "but it is not imported"
            )

        next_contract = by_code[expected_next]
        current_stats = daily_stats.get(current["contract_code"], {})
        next_stats = daily_stats.get(next_contract["contract_code"], {})
        latest_roll_day = latest_allowed_roll_day(current, current_stats, policy)
        common_days = sorted(day for day in current_stats if day in next_stats and day <= latest_roll_day)
        if not common_days:
            raise RuntimeError(
                f"No overlapping trade days between {current['contract_code']} and {next_contract['contract_code']} "
                f"before hard cutoff {latest_roll_day.isoformat()}"
            )

        trigger_date = None
        trigger_reason = "hard_cutoff"
        consecutive = 0
        for day in common_days:
            if next_stats[day]["daily_volume"] > current_stats[day]["daily_volume"]:
                consecutive += 1
            else:
                consecutive = 0
            if consecutive >= policy["confirmation_sessions"]:
                trigger_date = day
                trigger_reason = "volume_confirmation"
                break

        if trigger_date is None:
            trigger_date = common_days[-1]
            consecutive = 0

        next_days = sorted(day for day in next_stats if day > trigger_date)
        if not next_days:
            raise RuntimeError(
                f"No effective trading day after trigger date {trigger_date.isoformat()} for {next_contract['contract_code']}"
            )
        effective_day = next_days[0]
        effective_ts = fetch_min_timestamp(next_contract["contract_code"], effective_day)
        old_close = current_stats[trigger_date]["session_close"]
        new_close = next_stats[trigger_date]["session_close"]
        adjustment_amount = (new_close - old_close).quantize(Decimal("0.0001"))

        schedules.append(
            RollDecision(
                old_contract_code=current["contract_code"],
                new_contract_code=next_contract["contract_code"],
                old_contract_id=int(current["contract_id"]),
                new_contract_id=int(next_contract["contract_id"]),
                trigger_date=trigger_date,
                effective_trading_day=effective_day,
                effective_ts=effective_ts,
                trigger_reason=trigger_reason,
                old_daily_volume=int(current_stats[trigger_date]["daily_volume"]),
                new_daily_volume=int(next_stats[trigger_date]["daily_volume"]),
                consecutive_sessions=consecutive,
                representative_old_price=old_close,
                representative_new_price=new_close,
                adjustment_amount=adjustment_amount,
            )
        )

    return schedules


def cumulative_adjustments(contracts: list[dict], schedules: list[RollDecision]) -> dict[str, Decimal]:
    latest_contract_code = contracts[-1]["contract_code"]
    cumulative_by_contract = {latest_contract_code: Decimal("0.0000")}
    schedule_by_old = {schedule.old_contract_code: schedule for schedule in schedules}

    for contract in reversed(contracts[:-1]):
        schedule = schedule_by_old[contract["contract_code"]]
        cumulative_by_contract[contract["contract_code"]] = (
            schedule.adjustment_amount + cumulative_by_contract[schedule.new_contract_code]
        ).quantize(Decimal("0.0001"))
    return cumulative_by_contract


def insert_roll_schedule(root_symbol: str, chain_symbol: str, schedules: list[RollDecision]) -> None:
    rows = [
        {
            "chain_symbol": chain_symbol,
            "root_symbol": root_symbol,
            "old_contract_code": schedule.old_contract_code,
            "new_contract_code": schedule.new_contract_code,
            "old_contract_id": schedule.old_contract_id,
            "new_contract_id": schedule.new_contract_id,
            "trigger_date": schedule.trigger_date.isoformat(),
            "effective_trading_day": schedule.effective_trading_day.isoformat(),
            "effective_ts": schedule.effective_ts,
            "trigger_reason": schedule.trigger_reason,
            "old_daily_volume": schedule.old_daily_volume,
            "new_daily_volume": schedule.new_daily_volume,
            "consecutive_sessions": schedule.consecutive_sessions,
            "representative_old_price": float(schedule.representative_old_price),
            "representative_new_price": float(schedule.representative_new_price),
            "adjustment_amount": float(schedule.adjustment_amount),
        }
        for schedule in schedules
    ]
    insert_json_rows("market_data.futures_roll_schedule", rows)


def insert_continuous_ticks(
    contracts: list[dict],
    schedules: list[RollDecision],
    cumulative_by_contract: dict[str, Decimal],
    root_symbol: str,
    chain_symbol: str,
) -> None:
    schedule_by_old = {schedule.old_contract_code: schedule for schedule in schedules}
    reference_contract_code = contracts[-1]["contract_code"]

    for index, contract in enumerate(contracts):
        contract_code = contract["contract_code"]
        start_day = (
            to_date(contract["first_trade_date"])
            if index == 0
            else schedule_by_old[contracts[index - 1]["contract_code"]].effective_trading_day
        )
        end_day = (
            schedule_by_old[contract_code].effective_trading_day
            if contract_code in schedule_by_old
            else None
        )
        adjustment = cumulative_by_contract[contract_code]
        end_clause = ""
        if end_day is not None:
            end_clause = f"AND trading_day < toDate('{end_day.isoformat()}')"
        execute(
            f"""
            INSERT INTO market_data.continuous_futures_ticks
            (
                chain_symbol,
                root_symbol,
                source_contract_code,
                source_contract_id,
                exchange,
                provider,
                ts_exchange,
                trading_day,
                sequence,
                raw_trade_price,
                adjusted_trade_price,
                trade_size,
                source_file,
                source_row_number,
                cumulative_adjustment,
                segment_number,
                reference_contract_code
            )
            SELECT
                '{chain_symbol}' AS chain_symbol,
                root_symbol,
                contract_code AS source_contract_code,
                contract_id AS source_contract_id,
                exchange,
                provider,
                ts_exchange,
                trading_day,
                sequence,
                trade_price AS raw_trade_price,
                if(isNull(trade_price), NULL, trade_price + toDecimal64('{adjustment}', 4)) AS adjusted_trade_price,
                trade_size,
                source_file,
                source_row_number,
                toDecimal64('{adjustment}', 4) AS cumulative_adjustment,
                {index + 1} AS segment_number,
                '{reference_contract_code}' AS reference_contract_code
            FROM market_data.futures_ticks
            WHERE root_symbol = '{root_symbol}'
              AND event_type = 'trade'
              AND contract_code = '{contract_code}'
              AND trading_day >= toDate('{start_day.isoformat()}')
              {end_clause}
            """
        )


def main() -> None:
    args = parse_args()
    chain_symbol = args.chain_symbol or f"{args.root_symbol}_CONT_BACKADJ"
    policy = load_roll_policy(args.config, args.root_symbol)
    contracts = fetch_contracts(args.root_symbol, args.contract_codes)
    daily_stats = fetch_daily_stats(args.root_symbol, [contract["contract_code"] for contract in contracts])

    if args.replace_output:
        execute("TRUNCATE TABLE market_data.futures_roll_schedule")
        execute("TRUNCATE TABLE market_data.continuous_futures_ticks")

    schedules = build_roll_schedule(contracts, daily_stats, policy)
    cumulative_by_contract = cumulative_adjustments(contracts, schedules)
    insert_roll_schedule(args.root_symbol, chain_symbol, schedules)
    insert_continuous_ticks(contracts, schedules, cumulative_by_contract, args.root_symbol, chain_symbol)

    for schedule in schedules:
        print(
            f"{schedule.old_contract_code}->{schedule.new_contract_code} "
            f"trigger={schedule.trigger_date.isoformat()} "
            f"effective={schedule.effective_trading_day.isoformat()} "
            f"reason={schedule.trigger_reason} "
            f"adjustment={schedule.adjustment_amount}"
        )


if __name__ == "__main__":
    main()

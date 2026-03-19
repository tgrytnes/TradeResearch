#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
import time
from pathlib import Path

from clickhouse_http import query_json_rows
from futures_contracts import load_roll_policy, next_cycle_contract_code, parse_contract_filename


ROOT_DIR = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT_DIR / "infra/clickhouse/docker-compose.yml"
SCHEMA_FILES = [
    ROOT_DIR / "infra/clickhouse/sql/001_market_data.sql",
    ROOT_DIR / "infra/clickhouse/sql/002_continuous_futures.sql",
]
SYNTHETIC_FILES = [
    ROOT_DIR / "infra/clickhouse/samples/continuous/FDAXH24-EUREX.csv",
    ROOT_DIR / "infra/clickhouse/samples/continuous/FDAXM24-EUREX.csv",
    ROOT_DIR / "infra/clickhouse/samples/continuous/FDAXU24-EUREX.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify continuous futures rollover implementation.")
    parser.add_argument(
        "--real-source-dir",
        default="/Users/thomasfey-grytnes/Library/Mobile Documents/com~apple~CloudDocs/Trading/Sierra Chart - FDAX/csv",
    )
    parser.add_argument("--keep-running", action="store_true")
    return parser.parse_args()


def run(command: list[str], *, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=ROOT_DIR,
        input=input_text,
        text=True,
        capture_output=True,
        check=check,
    )


def compose(*args: str, input_text: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return run(["docker", "compose", "-f", str(COMPOSE_FILE), *args], input_text=input_text, check=check)


def wait_for_clickhouse() -> None:
    for _ in range(30):
        result = compose("exec", "-T", "clickhouse", "clickhouse-client", "--query", "SELECT 1", check=False)
        if result.returncode == 0:
            return
        time.sleep(2)
    raise RuntimeError("ClickHouse did not become ready in time")


def wait_for_database(database_name: str) -> None:
    for _ in range(10):
        result = compose(
            "exec",
            "-T",
            "clickhouse",
            "clickhouse-client",
            "--query",
            f"EXISTS DATABASE {database_name}",
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip() == "1":
            return
        time.sleep(1)
    raise RuntimeError(f"Database {database_name} did not become visible in time")


def reset_schema() -> None:
    compose("exec", "-T", "clickhouse", "clickhouse-client", "--query", "DROP DATABASE IF EXISTS market_data")
    run(
        [
            "python3",
            "scripts/apply_clickhouse_sql.py",
            "--files",
            *(str(schema_file) for schema_file in SCHEMA_FILES),
        ]
    )
    wait_for_database("market_data")


def source_summary(file_path: Path) -> dict:
    row_count = 0
    total_volume = 0
    first_row = None
    last_row = None
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            row_count += 1
            total_volume += int(row["Volume"])
            if first_row is None:
                first_row = row
            last_row = row
    if row_count == 0 or first_row is None or last_row is None:
        raise RuntimeError(f"No rows in {file_path}")
    return {
        "file": file_path.name,
        "rows": row_count,
        "first_date": first_row["Date"],
        "first_time": first_row["Time"],
        "last_date": last_row["Date"],
        "last_time": last_row["Time"],
        "total_volume": total_volume,
    }


def print_source_summaries(label: str, summaries: list[dict]) -> None:
    print(label)
    for summary in summaries:
        print(
            f"  {summary['file']}: rows={summary['rows']} "
            f"range={summary['first_date']} {summary['first_time']} -> {summary['last_date']} {summary['last_time']} "
            f"volume={summary['total_volume']}"
        )


def verify_synthetic() -> None:
    print("Synthetic verification")
    summaries = [source_summary(path) for path in SYNTHETIC_FILES]
    print_source_summaries("Original synthetic files", summaries)

    synthetic_import = run(
        ["python3", "scripts/import_sierra_chart_ticks.py", "--files", *(str(path) for path in SYNTHETIC_FILES)],
        check=False,
    )
    if synthetic_import.returncode != 0:
        raise RuntimeError((synthetic_import.stderr or synthetic_import.stdout).strip())

    synthetic_build = run(
        [
            "python3",
            "scripts/build_continuous_futures.py",
            "--root-symbol",
            "FDAX",
            "--contract-codes",
            "FDAXH24",
            "FDAXM24",
            "FDAXU24",
            "--replace-output",
        ],
        check=False,
    )
    if synthetic_build.returncode != 0:
        raise RuntimeError((synthetic_build.stderr or synthetic_build.stdout).strip())

    imported = query_json_rows(
        """
        SELECT
            contract_code,
            count() AS imported_rows,
            min(trading_day) AS min_day,
            max(trading_day) AS max_day,
            sum(trade_size) AS imported_volume
        FROM market_data.futures_ticks
        GROUP BY contract_code
        ORDER BY contract_code
        """
    )
    print("Imported synthetic rows")
    for row in imported:
        print(
            f"  {row['contract_code']}: rows={row['imported_rows']} "
            f"range={row['min_day']}..{row['max_day']} volume={row['imported_volume']}"
        )

    schedules = query_json_rows(
        """
        SELECT
            old_contract_code,
            new_contract_code,
            trigger_date,
            effective_trading_day,
            trigger_reason,
            representative_old_price,
            representative_new_price,
            adjustment_amount
        FROM market_data.futures_roll_schedule
        ORDER BY trigger_date
        """
    )
    if len(schedules) != 2:
        raise RuntimeError(f"Expected 2 synthetic roll schedule rows, got {len(schedules)}")

    contract_adjustments = {
        row["source_contract_code"]: row["cumulative_adjustment"]
        for row in query_json_rows(
            """
            SELECT source_contract_code, any(cumulative_adjustment) AS cumulative_adjustment
            FROM market_data.continuous_futures_ticks
            GROUP BY source_contract_code
            """
        )
    }

    for schedule in schedules:
        old_adjusted = round(
            float(schedule["representative_old_price"]) + float(contract_adjustments[schedule["old_contract_code"]]),
            4,
        )
        new_adjusted = round(
            float(schedule["representative_new_price"]) + float(contract_adjustments[schedule["new_contract_code"]]),
            4,
        )
        if old_adjusted != new_adjusted:
            raise RuntimeError(
                f"Adjusted prices do not match across roll {schedule['old_contract_code']}->{schedule['new_contract_code']}: "
                f"{old_adjusted} vs {new_adjusted}"
            )

    print("Synthetic continuous schedule")
    for schedule in schedules:
        print(
            f"  {schedule['old_contract_code']}->{schedule['new_contract_code']} "
            f"trigger={schedule['trigger_date']} effective={schedule['effective_trading_day']} "
            f"reason={schedule['trigger_reason']} adjustment={schedule['adjustment_amount']}"
        )


def discover_real_files(real_source_dir: Path) -> tuple[list[Path], str | None]:
    policy = load_roll_policy(ROOT_DIR / "config/futures_roll_policies.json", "FDAX")
    available_paths = sorted(real_source_dir.glob("FDAX*-EUREX.csv"))
    if len(available_paths) < 3:
        raise RuntimeError(f"Need at least 3 FDAX files in {real_source_dir}")

    contracts = sorted(
        (parse_contract_filename(path) for path in available_paths),
        key=lambda contract: (contract.year, contract.month),
    )
    by_code = {contract.contract_code: real_source_dir / f"{contract.contract_code}-EUREX.csv" for contract in contracts}

    for contract in contracts:
        next_one = next_cycle_contract_code(contract.contract_code, policy["cycle_months"])
        next_two = next_cycle_contract_code(next_one, policy["cycle_months"])
        if next_one in by_code and next_two in by_code:
            return [by_code[contract.contract_code], by_code[next_one], by_code[next_two]], None

    fallback = [by_code[contract.contract_code] for contract in contracts[-3:]]
    diagnostic = (
        "No adjacent quarterly FDAX chain is available yet. "
        f"Newest files are {[path.name for path in fallback]}."
    )
    return fallback, diagnostic


def verify_real(real_source_dir: Path) -> None:
    print("Real FDAX verification")
    selected_files, discovery_diagnostic = discover_real_files(real_source_dir)
    if discovery_diagnostic is not None:
        print(f"  {discovery_diagnostic}")

    summaries = [source_summary(path) for path in selected_files]
    print_source_summaries("Original real files", summaries)

    real_import = run(
        ["python3", "scripts/import_sierra_chart_ticks.py", "--files", *(str(path) for path in selected_files)],
        check=False,
    )
    if real_import.returncode != 0:
        raise RuntimeError((real_import.stderr or real_import.stdout).strip())

    imported = query_json_rows(
        """
        SELECT
            contract_code,
            count() AS imported_rows,
            min(trading_day) AS min_day,
            max(trading_day) AS max_day,
            sum(trade_size) AS imported_volume
        FROM market_data.futures_ticks
        GROUP BY contract_code
        ORDER BY contract_code
        """
    )
    print("Imported real rows")
    for row in imported:
        print(
            f"  {row['contract_code']}: rows={row['imported_rows']} "
            f"range={row['min_day']}..{row['max_day']} volume={row['imported_volume']}"
        )

    selected_codes = [parse_contract_filename(path).contract_code for path in selected_files]
    build = run(
        [
            "python3",
            "scripts/build_continuous_futures.py",
            "--root-symbol",
            "FDAX",
            "--contract-codes",
            *selected_codes,
            "--replace-output",
        ],
        check=False,
    )
    if discovery_diagnostic is None:
        if build.returncode != 0:
            raise RuntimeError((build.stderr or build.stdout).strip())
        schedules = query_json_rows(
            """
            SELECT
                old_contract_code,
                new_contract_code,
                trigger_date,
                effective_trading_day,
                trigger_reason,
                adjustment_amount
            FROM market_data.futures_roll_schedule
            ORDER BY trigger_date
            """
        )
        print("Real continuous schedule")
        for schedule in schedules:
            print(
                f"  {schedule['old_contract_code']}->{schedule['new_contract_code']} "
                f"trigger={schedule['trigger_date']} effective={schedule['effective_trading_day']} "
                f"reason={schedule['trigger_reason']} adjustment={schedule['adjustment_amount']}"
            )
        return

    if build.returncode == 0:
        raise RuntimeError(
            "Expected real-data continuous build to fail while no adjacent quarterly chain is available"
        )

    error_text = (build.stderr or build.stdout).strip()
    print("Continuous build diagnostic")
    print(f"  {error_text}")
    if "Expected next cycle contract" not in error_text:
        raise RuntimeError(f"Unexpected real-data failure: {error_text}")


def main() -> None:
    args = parse_args()
    try:
        compose("up", "-d")
        wait_for_clickhouse()

        reset_schema()
        verify_synthetic()

        reset_schema()
        verify_real(Path(args.real_source_dir))
    finally:
        if not args.keep_running:
            compose("down", "-v", check=False)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)

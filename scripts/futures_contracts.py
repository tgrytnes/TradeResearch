#!/usr/bin/env python3

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import json
import re
from pathlib import Path


MONTH_CODE_TO_MONTH = {
    "F": 1,
    "G": 2,
    "H": 3,
    "J": 4,
    "K": 5,
    "M": 6,
    "N": 7,
    "Q": 8,
    "U": 9,
    "V": 10,
    "X": 11,
    "Z": 12,
}

MONTH_TO_MONTH_CODE = {value: key for key, value in MONTH_CODE_TO_MONTH.items()}
CONTRACT_FILE_RE = re.compile(
    r"^(?P<root>[A-Z]+)(?P<month_code>[FGHJKMNQUVXZ])(?P<year>\d{2})-(?P<exchange>[A-Z0-9]+)\.csv$"
)


@dataclass(frozen=True)
class ParsedContract:
    root_symbol: str
    contract_code: str
    month_code: str
    month: int
    year: int
    exchange: str


def parse_contract_filename(file_path: str | Path) -> ParsedContract:
    match = CONTRACT_FILE_RE.match(Path(file_path).name)
    if not match:
        raise ValueError(f"Unsupported contract filename: {file_path}")

    root_symbol = match.group("root")
    month_code = match.group("month_code")
    year = 2000 + int(match.group("year"))
    exchange = match.group("exchange")
    contract_code = f"{root_symbol}{month_code}{match.group('year')}"
    return ParsedContract(
        root_symbol=root_symbol,
        contract_code=contract_code,
        month_code=month_code,
        month=MONTH_CODE_TO_MONTH[month_code],
        year=year,
        exchange=exchange,
    )


def contract_id_for(parsed_contract: ParsedContract) -> int:
    return parsed_contract.year * 100 + parsed_contract.month


def third_friday(year: int, month: int) -> date:
    current = date(year, month, 1)
    while current.weekday() != 4:
        current += timedelta(days=1)
    return current + timedelta(days=14)


def next_cycle_contract_code(current_code: str, cycle_months: list[int]) -> str:
    parsed = parse_contract_filename(f"{current_code}-EUREX.csv")
    remaining_months = [month for month in cycle_months if month > parsed.month]
    if remaining_months:
        next_month = remaining_months[0]
        next_year = parsed.year
    else:
        next_month = cycle_months[0]
        next_year = parsed.year + 1

    next_code = MONTH_TO_MONTH_CODE[next_month]
    short_year = str(next_year % 100).zfill(2)
    return f"{parsed.root_symbol}{next_code}{short_year}"


def load_roll_policy(config_path: str | Path, root_symbol: str) -> dict:
    with Path(config_path).open("r", encoding="utf-8") as handle:
        config = json.load(handle)
    if root_symbol not in config:
        raise KeyError(f"Missing roll policy for {root_symbol}")
    return config[root_symbol]

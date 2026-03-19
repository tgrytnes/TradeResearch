#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Iterable


CLICKHOUSE_URL = os.environ.get("CLICKHOUSE_URL", "http://127.0.0.1:8123/")
CLICKHOUSE_DATABASE = os.environ.get("CLICKHOUSE_DATABASE", "market_data")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "traderesearch")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "traderesearch")


def _request(query: str, data: bytes | None = None) -> str:
    params = {
        "database": CLICKHOUSE_DATABASE,
        "user": CLICKHOUSE_USER,
        "password": CLICKHOUSE_PASSWORD,
        "query": query,
    }
    request = urllib.request.Request(
        f"{CLICKHOUSE_URL}?{urllib.parse.urlencode(params)}",
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ClickHouse HTTP {error.code}: {body}") from error


def execute(query: str) -> str:
    return _request(query.rstrip().rstrip(";"))


def query_json_rows(query: str) -> list[dict]:
    payload = _request(f"{query.rstrip().rstrip(';')} FORMAT JSONEachRow")
    if not payload.strip():
        return []
    return [json.loads(line) for line in payload.splitlines() if line.strip()]


def query_scalar(query: str) -> str:
    return _request(query.rstrip().rstrip(";")).strip()


def insert_json_rows(table: str, rows: Iterable[dict]) -> None:
    lines = [json.dumps(row, ensure_ascii=True, separators=(",", ":")) for row in rows]
    if not lines:
        return
    payload = ("\n".join(lines) + "\n").encode("utf-8")
    _request(f"INSERT INTO {table} FORMAT JSONEachRow", data=payload)

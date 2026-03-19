#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess


ROOT_DIR = Path(__file__).resolve().parent.parent
COMPOSE_FILE = ROOT_DIR / "infra/clickhouse/docker-compose.yml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply ClickHouse SQL files statement by statement.")
    parser.add_argument("--files", nargs="+", required=True)
    return parser.parse_args()


def split_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    current: list[str] = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        current.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(current).rstrip().rstrip(";"))
            current = []
    if current:
        statements.append("\n".join(current).rstrip().rstrip(";"))
    return [statement for statement in statements if statement.strip()]


def apply_statement(statement: str) -> None:
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "exec",
            "-T",
            "clickhouse",
            "clickhouse-client",
            "--query",
            statement,
        ],
        cwd=ROOT_DIR,
        check=True,
    )


def main() -> None:
    args = parse_args()
    for file_name in args.files:
        sql_path = Path(file_name)
        for statement in split_statements(sql_path.read_text(encoding="utf-8")):
            apply_statement(statement)


if __name__ == "__main__":
    main()

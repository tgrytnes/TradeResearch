#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/infra/clickhouse/docker-compose.yml"
SCHEMA_FILE="$ROOT_DIR/infra/clickhouse/sql/001_market_data.sql"
CONTRACTS_FILE="$ROOT_DIR/infra/clickhouse/samples/futures_contracts_sample.csv"
TICKS_FILE="$ROOT_DIR/infra/clickhouse/samples/futures_ticks_sample.csv"
SERVICE_NAME="clickhouse"
KEEP_RUNNING="${KEEP_RUNNING:-0}"

cleanup() {
  if [[ "$KEEP_RUNNING" != "1" ]]; then
    docker compose -f "$COMPOSE_FILE" down -v >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT

docker compose -f "$COMPOSE_FILE" up -d >/dev/null

for attempt in $(seq 1 30); do
  if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
    clickhouse-client --query "SELECT 1" >/dev/null 2>&1; then
    break
  fi

  if [[ "$attempt" -eq 30 ]]; then
    echo "ClickHouse did not become ready in time" >&2
    exit 1
  fi

  sleep 2
done

docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
  clickhouse-client --query "DROP DATABASE IF EXISTS market_data"

docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
  clickhouse-client --multiquery < "$SCHEMA_FILE"

docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
  clickhouse-client --query "
    INSERT INTO market_data.futures_contracts
    (contract_id, root_symbol, contract_code, exchange, expiry_date, first_trade_date,
     last_trade_date, tick_size, point_value, currency, timezone)
    FORMAT CSVWithNames
  " < "$CONTRACTS_FILE"

docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
  clickhouse-client --query "
    INSERT INTO market_data.futures_ticks
    (root_symbol, contract_code, contract_id, exchange, provider, ts_exchange, ts_received,
     trading_day, sequence, event_type, trade_price, trade_size, bid_price, bid_size,
     ask_price, ask_size, source_file, source_row_number, ingest_run_id)
    FORMAT CSVWithNames
  " < "$TICKS_FILE"

contract_count="$(
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
    clickhouse-client --query "SELECT count() FROM market_data.futures_contracts"
)"

tick_count="$(
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
    clickhouse-client --query "SELECT count() FROM market_data.futures_ticks"
)"

range_count="$(
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
    clickhouse-client --query "
      SELECT count()
      FROM market_data.futures_ticks
      WHERE root_symbol = 'FDAX'
        AND trading_day BETWEEN toDate('2024-03-18') AND toDate('2024-03-19')
    "
)"

trade_count="$(
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
    clickhouse-client --query "
      SELECT count()
      FROM market_data.futures_ticks
      WHERE root_symbol = 'FDAX'
        AND trading_day = toDate('2024-03-19')
        AND event_type = 'trade'
    "
)"

latest_trade="$(
  docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" \
    clickhouse-client --query "
      SELECT trade_price
      FROM market_data.futures_ticks
      WHERE root_symbol = 'FDAX'
        AND event_type = 'trade'
      ORDER BY ts_exchange DESC
      LIMIT 1
    "
)"

if [[ "$contract_count" != "2" ]]; then
  echo "Expected 2 contracts, got $contract_count" >&2
  exit 1
fi

if [[ "$tick_count" != "5" ]]; then
  echo "Expected 5 ticks, got $tick_count" >&2
  exit 1
fi

if [[ "$range_count" != "5" ]]; then
  echo "Expected 5 FDAX ticks in date range, got $range_count" >&2
  exit 1
fi

if [[ "$trade_count" != "1" ]]; then
  echo "Expected 1 FDAX trade on 2024-03-19, got $trade_count" >&2
  exit 1
fi

if [[ "$latest_trade" != "18311" && "$latest_trade" != "18311.0000" ]]; then
  echo "Expected latest FDAX trade price 18311.0000, got $latest_trade" >&2
  exit 1
fi

echo "ClickHouse smoke test passed."
echo "Contracts loaded: $contract_count"
echo "Ticks loaded: $tick_count"
echo "FDAX ticks across 2024-03-18..2024-03-19: $range_count"
echo "FDAX trades on 2024-03-19: $trade_count"
echo "Latest FDAX trade price: $latest_trade"

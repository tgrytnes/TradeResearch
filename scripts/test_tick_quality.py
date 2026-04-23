import unittest
import csv
import subprocess
import os
from scripts import clickhouse_http

class TestTickQuality(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Setup schema
        with open("infra/clickhouse/sql/003_tick_diagnostics.sql", "r") as f:
            sql = f.read()
            clickhouse_http.execute(sql)

        # 2. Import anomalous data
        # First, clear previous anomalous ticks for this contract if any.
        clickhouse_http.execute("ALTER TABLE market_data.futures_ticks DELETE WHERE contract_code = 'ESZ24'")

        # Manually load the CSV for simplicity in the test
        with open("infra/clickhouse/samples/futures_ticks_anomalies.csv", "r") as f:
            reader = csv.reader(f)
            next(reader) # skip header
            for row in reader:
                formatted_row = []
                for val in row:
                    if val == "":
                        formatted_row.append("NULL")
                    elif any(char.isalpha() for char in val) or '/' in val or '-' in val or ':' in val:
                        formatted_row.append(f"'{val}'")
                    else:
                        formatted_row.append(val)

                sql = f"INSERT INTO market_data.futures_ticks (root_symbol, contract_code, contract_id, exchange, provider, ts_exchange, trading_day, sequence, event_type, trade_price, trade_size, bid_price, bid_size, ask_price, ask_size) VALUES ({','.join(formatted_row)})"
                clickhouse_http.execute(sql)

    def test_price_jump_detection(self):
        """Verify that abnormal price jumps are detected."""
        res = clickhouse_http.query_scalar("SELECT count() FROM market_data.futures_tick_diagnostics WHERE check_name = 'abnormal_price_jump' AND contract_code = 'ESZ24'")
        count = int(res)
        self.assertGreater(count, 0, "Should have detected at least one abnormal price jump")

    def test_volume_anomaly_detection(self):
        """Verify that zero or negative volume is detected."""
        res = clickhouse_http.query_scalar("SELECT count() FROM market_data.futures_tick_diagnostics WHERE check_name = 'invalid_volume' AND contract_code = 'ESZ24'")
        count = int(res)
        self.assertGreater(count, 0, "Should have detected at least one volume anomaly")

    def test_timestamp_anomaly_detection(self):
        """Verify that duplicate or out-of-order timestamps are detected."""
        res = clickhouse_http.query_scalar("SELECT count() FROM market_data.futures_tick_diagnostics WHERE check_name IN ('duplicate_timestamp', 'out_of_order_timestamp') AND contract_code = 'ESZ24'")
        count = int(res)
        self.assertGreater(count, 0, "Should have detected at least one timestamp anomaly")

    def test_malformed_row_detection(self):
        """Verify that impossible price relationships (e.g. bid > ask) are detected."""
        res = clickhouse_http.query_scalar("SELECT count() FROM market_data.futures_tick_diagnostics WHERE check_name = 'impossible_price_relationship' AND contract_code = 'ESZ24'")
        count = int(res)
        self.assertGreater(count, 0, "Should have detected at least one malformed row anomaly")

    def test_session_gap_detection(self):
        """Verify that suspiciously low activity or gaps are detected."""
        res = clickhouse_http.query_scalar("SELECT count() FROM market_data.futures_tick_diagnostics WHERE check_name = 'session_gap' AND contract_code = 'ESZ24'")
        count = int(res)
        self.assertGreater(count, 0, "Should have detected at least one session gap")

if __name__ == "__main__":
    unittest.main()

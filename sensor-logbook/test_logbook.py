import csv
from datetime import datetime, timezone, timedelta
import http.client
from http.server import HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

from logbook import Logbook, make_handler, demo, iso

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)


class LogbookTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = Path(self.folder.name) / "test.sqlite"
        self.book = Logbook(self.path)

    def tearDown(self):
        self.book.close()
        self.folder.cleanup()

    def reading(self, sequence=1, temperature=60, vibration=3, **extra):
        return dict(asset="pump-01", sequence=sequence, timestamp=iso(NOW+timedelta(seconds=sequence)),
                    temperature=temperature, vibration=vibration, **extra)

    def add(self, **kwargs):
        return self.book.ingest(self.reading(**kwargs), now=NOW+timedelta(minutes=10))

    def test_persistence_after_reopen(self):
        self.add()
        self.book.close()
        self.book = Logbook(self.path)
        self.assertEqual(self.book.status(NOW)["reading_count"], 1)

    def test_retries_are_idempotent_and_conflicts_fail(self):
        self.assertTrue(self.add()["inserted"])
        self.assertFalse(self.add()["inserted"])
        with self.assertRaisesRegex(ValueError, "different content"):
            self.add(temperature=70)
        self.assertEqual(len(self.book.readings()), 1)

    def test_hysteresis_acknowledgement_and_repeat_episode(self):
        self.add(temperature=80)
        self.book.acknowledge(1, NOW)
        self.add(sequence=2, temperature=78)
        alarm = self.book.status(NOW)["alarms"][0]
        self.assertIsNone(alarm["closed_at"])
        self.assertIsNotNone(alarm["acknowledged_at"])
        self.add(sequence=3, temperature=75)
        self.assertIsNotNone(self.book.status(NOW)["alarms"][0]["closed_at"])
        self.add(sequence=4, temperature=81)
        self.assertEqual(len(self.book.status(NOW)["alarms"]), 2)

    def test_alarm_metrics_are_independent(self):
        self.add(temperature=85, vibration=8)
        self.add(sequence=2, temperature=70, vibration=6.5)
        alarms = self.book.status(NOW)["alarms"]
        self.assertIsNotNone(alarms[0]["closed_at"])
        self.assertIsNone(alarms[1]["closed_at"])

    def test_out_of_order_and_timestamp_regression(self):
        self.add(sequence=3)
        with self.assertRaises(ValueError):
            self.add(sequence=2)
        item = self.reading(sequence=4)
        item["timestamp"] = iso(NOW)
        with self.assertRaises(ValueError):
            self.book.ingest(item, NOW)
        self.assertEqual(len(self.book.readings()), 1)

    def test_stale_boundary(self):
        self.add()
        self.assertFalse(self.book.status(NOW+timedelta(seconds=31))["assets"][0]["stale"])
        self.assertTrue(self.book.status(NOW+timedelta(seconds=32))["assets"][0]["stale"])

    def test_invalid_values_leave_database_unchanged(self):
        for key, value in [("sequence", True), ("sequence", 2**70), ("asset", "a'; DROP TABLE readings;--"),
                           ("temperature", float("nan")), ("temperature", True), ("temperature", 251), ("temperature", 10**400),
                           ("vibration", -1), ("timestamp", "2026-11-23"), ("timestamp", "bad")]:
            with self.subTest(key=key, value=value):
                item = self.reading()
                item[key] = value
                with self.assertRaises(ValueError):
                    self.book.ingest(item, NOW)
        self.assertEqual(self.book.status(NOW)["reading_count"], 0)

    def test_future_timestamp_rejected(self):
        with self.assertRaisesRegex(ValueError, "future"):
            self.book.ingest(self.reading(sequence=31), NOW)

    def test_timezone_normalization(self):
        item = self.reading()
        item["timestamp"] = "2026-11-23T13:00:01+01:00"
        self.book.ingest(item, NOW)
        self.assertEqual(self.book.readings()[0]["timestamp"], iso(NOW+timedelta(seconds=1)))

    def test_alarm_and_reading_roll_back_together(self):
        self.book.db.executescript("CREATE TRIGGER fail_alarm BEFORE INSERT ON alarms BEGIN SELECT RAISE(ABORT, 'test'); END;")
        import sqlite3
        with self.assertRaises(sqlite3.IntegrityError):
            self.add(temperature=90)
        self.assertEqual(self.book.status(NOW)["reading_count"], 0)

    def test_csv_export(self):
        self.add()
        target = Path(self.folder.name) / "readings.csv"
        self.book.export(target)
        with target.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(rows[0]["asset"], "pump-01")
        self.assertEqual(rows[0]["sequence"], "1")

    def test_demo_is_reproducible(self):
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            demo(self.book, Path(self.folder.name))
            demo(self.book, Path(self.folder.name))
        status = self.book.status(NOW)
        self.assertEqual(status["reading_count"], 106)
        self.assertEqual(len(status["alarms"]), 2)
        self.assertTrue((Path(self.folder.name) / "report.svg").exists())

    def test_http_auth_validation_and_retry(self):
        token = "local-test-token-123456"
        # Store is constructed in the server thread, respecting SQLite ownership.
        ready = threading.Event()
        state = {}
        def run():
            book = Logbook(self.path)
            with HTTPServer(("127.0.0.1", 0), make_handler(book, token)) as server:
                server.timeout = 0.1
                state["server"] = server
                ready.set()
                while not state.get("stop"):
                    server.handle_request()
            book.close()
        thread = threading.Thread(target=run)
        thread.start()
        self.assertTrue(ready.wait(5))
        client = http.client.HTTPConnection("127.0.0.1", state["server"].server_port, timeout=5)
        try:
            client.request("GET", "/status")
            response = client.getresponse()
            self.assertEqual(response.status, 401)
            response.read()
            headers = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
            item = self.reading()
            item["timestamp"] = iso(datetime.now(timezone.utc))
            for expected in (201, 200):
                client.request("POST", "/readings", json.dumps(item), headers)
                response = client.getresponse()
                self.assertEqual(response.status, expected)
                response.read()
            client.request("POST", "/readings", "{bad", headers)
            response = client.getresponse()
            self.assertEqual(response.status, 400)
            response.read()
            client.request("GET", "/status", headers=headers)
            response = client.getresponse()
            self.assertEqual(json.loads(response.read())["reading_count"], 1)
        finally:
            client.close()
            state["stop"] = True
            thread.join(5)
            self.assertFalse(thread.is_alive())


if __name__ == "__main__":
    unittest.main()

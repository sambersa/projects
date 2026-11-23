"""Small, transactional sensor store. Python standard library only."""
from __future__ import annotations

import argparse
import csv
import hashlib
import hmac
import json
import math
import os
from pathlib import Path
import re
import sqlite3
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer

RULES = {"temperature": (80.0, 75.0, "C"), "vibration": (7.0, 6.0, "mm/s")}


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError("timestamp must be an ISO 8601 string with a timezone")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("invalid timestamp") from None
    if dt.tzinfo is None:
        raise ValueError("timestamp requires a timezone")
    return dt.astimezone(timezone.utc)


def iso(dt):
    return dt.astimezone(timezone.utc).isoformat(timespec="microseconds")


def validate(data):
    if not isinstance(data, dict) or set(data) != {"asset", "sequence", "timestamp", *RULES}:
        raise ValueError("expected asset, sequence, timestamp, temperature, vibration")
    if not isinstance(data["asset"], str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", data["asset"]):
        raise ValueError("asset must be 1-40 letters, numbers, underscores or hyphens")
    if type(data["sequence"]) is not int or not 0 <= data["sequence"] <= 2**63 - 1:
        raise ValueError("sequence must be a nonnegative 64-bit integer")
    result = dict(data, timestamp=iso(timestamp(data["timestamp"])))
    for metric in RULES:
        value = data[metric]
        if type(value) not in (float, int):
            raise ValueError(f"{metric} must be a finite number")
        if not (-50 <= value <= 250 if metric == "temperature" else 0 <= value <= 100):
            raise ValueError(f"{metric} outside accepted measurement range")
        if not math.isfinite(value):
            raise ValueError(f"{metric} must be a finite number")
        result[metric] = float(value)
    return result


class Logbook:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS readings (
                asset TEXT NOT NULL, sequence INTEGER NOT NULL, timestamp TEXT NOT NULL,
                temperature REAL NOT NULL, vibration REAL NOT NULL,
                PRIMARY KEY (asset, sequence)
            );
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY, asset TEXT NOT NULL, metric TEXT NOT NULL,
                opened_at TEXT NOT NULL, closed_at TEXT, acknowledged_at TEXT
            );
            CREATE UNIQUE INDEX IF NOT EXISTS one_active_alarm
                ON alarms(asset, metric) WHERE closed_at IS NULL;
        """)

    def close(self):
        self.db.close()

    def ingest(self, data, now=None):
        item = validate(data)
        now = now or datetime.now(timezone.utc)
        if timestamp(item["timestamp"]) > now + timedelta(seconds=30):
            raise ValueError("reading is more than 30 seconds in the future")
        # Reading + alarm transitions commit together, including under retry.
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute("SELECT * FROM readings WHERE asset=? AND sequence=?",
                                  (item["asset"], item["sequence"])).fetchone()
            if old:
                if dict(old) != item:
                    raise ValueError("sequence already exists with different content")
                return {"inserted": False, "sequence": item["sequence"]}
            latest = self.db.execute("SELECT sequence,timestamp FROM readings WHERE asset=? ORDER BY sequence DESC LIMIT 1",
                                     (item["asset"],)).fetchone()
            if latest and (item["sequence"] <= latest["sequence"] or item["timestamp"] <= latest["timestamp"]):
                raise ValueError("sequence and timestamp must both increase for each asset")
            self.db.execute("INSERT INTO readings VALUES (:asset,:sequence,:timestamp,:temperature,:vibration)", item)
            for metric, (high, clear, _) in RULES.items():
                if item[metric] >= high:
                    self.db.execute("INSERT OR IGNORE INTO alarms(asset,metric,opened_at) VALUES (?,?,?)",
                                    (item["asset"], metric, item["timestamp"]))
                elif item[metric] <= clear:
                    self.db.execute("UPDATE alarms SET closed_at=? WHERE asset=? AND metric=? AND closed_at IS NULL",
                                    (item["timestamp"], item["asset"], metric))
        return {"inserted": True, "sequence": item["sequence"]}

    def acknowledge(self, alarm_id, now=None):
        if type(alarm_id) is not int or alarm_id < 1:
            raise ValueError("alarm id must be a positive integer")
        with self.db:
            row = self.db.execute("SELECT * FROM alarms WHERE id=?", (alarm_id,)).fetchone()
            if row is None:
                raise ValueError("alarm not found")
            self.db.execute("UPDATE alarms SET acknowledged_at=COALESCE(acknowledged_at,?) WHERE id=?",
                            (iso(now or datetime.now(timezone.utc)), alarm_id))

    def readings(self, asset=None):
        query = "SELECT * FROM readings"
        params = ()
        if asset is not None:
            query += " WHERE asset=?"
            params = (asset,)
        return [dict(row) for row in self.db.execute(query + " ORDER BY asset,sequence", params)]

    def status(self, now=None):
        now = now or datetime.now(timezone.utc)
        rows = self.db.execute("""SELECT r.* FROM readings r JOIN
            (SELECT asset,MAX(sequence) seq FROM readings GROUP BY asset) latest
            ON r.asset=latest.asset AND r.sequence=latest.seq ORDER BY r.asset""")
        assets = []
        for row in rows:
            item = dict(row)
            age = max(0, (now - timestamp(item["timestamp"])).total_seconds())
            item.update(age_seconds=round(age, 1), stale=age > 30)
            assets.append(item)
        alarms = [dict(row) for row in self.db.execute("SELECT * FROM alarms ORDER BY id")]
        return {"assets": assets, "alarms": alarms,
                "reading_count": self.db.execute("SELECT COUNT(*) FROM readings").fetchone()[0]}

    def export(self, path):
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["asset", "sequence", "timestamp", *RULES])
            writer.writeheader()
            writer.writerows(self.readings())


def make_handler(book, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not log authorization headers or request bodies.

        def reply(self, code, data):
            body = json.dumps(data, allow_nan=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def authorized(self):
            supplied = self.headers.get("Authorization", "")
            # Hash to a fixed length before a constant-time comparison.
            return hmac.compare_digest(hashlib.sha256(supplied.encode()).digest(),
                                       hashlib.sha256(("Bearer " + token).encode()).digest())

        def do_GET(self):
            if not self.authorized():
                return self.reply(401, {"error": "unauthorized"})
            if self.path != "/status":
                return self.reply(404, {"error": "not found"})
            self.reply(200, book.status())

        def do_POST(self):
            if not self.authorized():
                return self.reply(401, {"error": "unauthorized"})
            if self.path != "/readings":
                return self.reply(404, {"error": "not found"})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 1 <= size <= 16384:
                    return self.reply(413, {"error": "body must be 1-16384 bytes"})
                data = json.loads(self.rfile.read(size))
                result = book.ingest(data)
                self.reply(201 if result["inserted"] else 200, result)
            except (ValueError, UnicodeError) as error:
                self.reply(400, {"error": str(error)})
            except sqlite3.Error:
                self.reply(503, {"error": "storage unavailable"})
    return Handler


def demo(book, folder):
    """Fixed, reproducible demo: two assets, high readings, recovery, and one stale asset."""
    from report import render
    base = datetime(2026, 11, 23, 9, 0, tzinfo=timezone.utc)
    for n in range(60):
        for asset in ("pump-01", "pump-02"):
            if asset == "pump-02" and n > 45:
                continue
            hot = asset == "pump-01" and 20 <= n <= 35
            book.ingest({"asset": asset, "sequence": n,
                         "timestamp": iso(base + timedelta(seconds=n * 5)),
                         "temperature": round(85 + 3 * math.sin(n) if hot else 62 + 4 * math.sin(n / 5), 2),
                         "vibration": round(8 + math.sin(n) / 2 if hot else 3 + math.sin(n / 4), 2)},
                        now=base + timedelta(minutes=10))
    book.acknowledge(1, now=base + timedelta(seconds=125))
    folder.mkdir(parents=True, exist_ok=True)
    book.export(folder / "readings.csv")
    status = book.status(base + timedelta(seconds=300))
    (folder / "status.json").write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    (folder / "report.svg").write_text(render(book, status), encoding="utf-8")
    print(json.dumps(status, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", default="logbook.sqlite")
    sub = parser.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("demo")
    seed.add_argument("--out", default="demo-output")
    sub.add_parser("status")
    ingest = sub.add_parser("ingest")
    ingest.add_argument("file", type=Path)
    export = sub.add_parser("export")
    export.add_argument("file", type=Path)
    ack = sub.add_parser("ack")
    ack.add_argument("id", type=int)
    server = sub.add_parser("serve")
    server.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    book = Logbook(args.db)
    try:
        if args.command == "demo":
            demo(book, Path(args.out))
        elif args.command == "status":
            print(json.dumps(book.status(), indent=2))
        elif args.command == "ingest":
            print(json.dumps(book.ingest(json.loads(args.file.read_text(encoding="utf-8")))))
        elif args.command == "export":
            book.export(args.file)
        elif args.command == "ack":
            book.acknowledge(args.id)
        else:
            token = os.environ.get("LOGBOOK_TOKEN", "")
            if len(token) < 16:
                raise ValueError("set LOGBOOK_TOKEN to at least 16 characters")
            with HTTPServer(("127.0.0.1", args.port), make_handler(book, token)) as httpd:
                httpd.timeout = 5
                print(f"Listening on http://127.0.0.1:{httpd.server_port}; Ctrl+C to stop", flush=True)
                httpd.serve_forever()
    except (ValueError, OSError) as error:
        parser.exit(2, f"Error: {error}\n")
    except KeyboardInterrupt:
        pass
    finally:
        book.close()


if __name__ == "__main__":
    main()

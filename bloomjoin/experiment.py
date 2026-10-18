"""Full-transfer baseline. Results stay at the local site."""
from contextlib import closing
import multiprocessing
import socket
import sqlite3
from time import perf_counter
from .protocol import Channel
from .worker import serve


PROJECTION = "SELECT l.join_key, l.payload, r.payload FROM records l JOIN incoming r ON l.join_key = r.join_key ORDER BY l.join_key"


def reference_join(local_path, remote_path):
    # Validation only: this local reference is outside measured query time/bytes.
    with closing(sqlite3.connect(local_path)) as db:
        db.execute("ATTACH DATABASE ? AS remote", (str(remote_path),))
        return db.execute("SELECT l.join_key, l.payload, r.payload FROM records l JOIN remote.records r ON l.join_key = r.join_key ORDER BY l.join_key").fetchall()


def run(local_path, remote_path, strategy="full"):
    if strategy != "full":
        raise NotImplementedError("Bloom strategies are starter issues; only full currently runs")
    context = multiprocessing.get_context("spawn")
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        listener.settimeout(30)
        process = context.Process(target=serve, args=(str(remote_path), listener.getsockname()))
        process.start()
        try:
            connection, _ = listener.accept()
            with connection, closing(sqlite3.connect(local_path)) as db:
                connection.settimeout(30)
                channel = Channel(connection)
                db.execute("CREATE TEMP TABLE incoming (join_key INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
                start = perf_counter()
                channel.send({"strategy": strategy})
                transferred = 0
                while True:
                    message = channel.receive()
                    if message.get("done"):
                        break
                    rows = message["rows"]
                    db.executemany("INSERT INTO incoming VALUES (?, ?)", rows)
                    transferred += len(rows)
                result = db.execute(PROJECTION).fetchall()
                elapsed = perf_counter() - start
                metrics = {
                    "strategy": strategy,
                    "application_bytes": channel.bytes_sent + channel.bytes_received,
                    "query_seconds": elapsed,
                    "filter_build_seconds": 0.0,
                    "transferred_records": transferred,
                    "nonmatching_records": transferred - len(result),
                    "result_rows": len(result),
                }
            process.join(timeout=30)
            if process.is_alive() or process.exitcode != 0:
                raise RuntimeError("Remote worker did not exit successfully")
        finally:
            if process.is_alive():
                process.terminate()
            process.join()
    expected = reference_join(local_path, remote_path)
    if result != expected:
        raise AssertionError("Distributed result differs from reference SQL join")
    metrics["verified"] = True
    return metrics

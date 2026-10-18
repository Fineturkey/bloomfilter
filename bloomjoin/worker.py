"""The remote process owns the remote SQLite connection."""
from contextlib import closing
import socket
import sqlite3
from .protocol import Channel, encode_json


def sizing_statistics(db):
    """Scan rows with bounded memory; width includes one separator per row.

    Batch envelopes and framing are excluded from this estimate, but are counted
    in application_bytes when actually transmitted. Empty width is zero.
    """
    count = 0
    row_bytes = 0
    for row in db.execute("SELECT join_key, payload FROM records"):
        count += 1
        row_bytes += len(encode_json(row)) + 1
    return {"row_count": count, "mean_row_bytes": row_bytes / count if count else 0.0}


def serve(database, address):
    with socket.create_connection(address, timeout=30) as connection:
        channel = Channel(connection)
        with closing(sqlite3.connect(database)) as db:
            request = channel.receive()
            if request == {"request": "sizing"}:
                channel.send({"sizing": sizing_statistics(db)})
                request = channel.receive()
            if request != {"strategy": "full"}:
                raise ValueError("Only the full-transfer baseline is implemented")
            cursor = db.execute("SELECT join_key, payload FROM records ORDER BY join_key")
            while True:
                batch = cursor.fetchmany(1000)
                if not batch:
                    break
                channel.send({"rows": batch})
        channel.send({"done": True})

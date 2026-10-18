"""The remote process owns the remote SQLite connection."""
from contextlib import closing
import socket
import sqlite3
from .protocol import Channel


def serve(database, address):
    with socket.create_connection(address, timeout=30) as connection:
        channel = Channel(connection)
        request = channel.receive()
        if request != {"strategy": "full"}:
            raise ValueError("Only the full-transfer baseline is implemented")
        with closing(sqlite3.connect(database)) as db:
            cursor = db.execute("SELECT join_key, payload FROM records ORDER BY join_key")
            while True:
                batch = cursor.fetchmany(1000)
                if not batch:
                    break
                channel.send({"rows": batch})
        channel.send({"done": True})

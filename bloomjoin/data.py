"""Reproducible data with unique, non-null integer keys."""
from contextlib import closing
import random
import sqlite3
from pathlib import Path


def generate(directory, rows=1000, overlap=0.1, payload_bytes=32, seed=42):
    if rows < 0 or not 0 <= overlap <= 1 or payload_bytes < 0:
        raise ValueError("rows and payload size must be nonnegative; overlap must be 0..1")
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    shared = int(rows * overlap)
    local_keys = list(range(rows))
    remote_keys = rng.sample(local_keys, shared) + list(range(rows, 2 * rows - shared))
    paths = []
    for name, keys in (("local", local_keys), ("remote", remote_keys)):
        rng.shuffle(keys)
        path = directory / (name + ".sqlite")
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("DROP TABLE IF EXISTS records")
            db.execute("CREATE TABLE records (join_key INTEGER PRIMARY KEY, payload TEXT NOT NULL)")
            db.executemany("INSERT INTO records VALUES (?, ?)",
                           ((key, name[0] * payload_bytes) for key in keys))
        paths.append(path)
    return tuple(paths)

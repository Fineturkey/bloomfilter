from contextlib import closing
import sqlite3
import tempfile
import unittest

from bloomjoin.data import generate
from bloomjoin.experiment import run
from bloomjoin.protocol import encode_json
from bloomjoin.worker import sizing_statistics


class SizingMetadataTests(unittest.TestCase):
    def test_width_uses_wire_json_escaping_and_key_digits(self):
        rows = [(1, '"\\\n'), (12345, '\u00e9\U0001f600')]
        with closing(sqlite3.connect(":memory:")) as db:
            db.execute("CREATE TABLE records (join_key INTEGER PRIMARY KEY, payload TEXT)")
            self.assertEqual(sizing_statistics(db), {"row_count": 0, "mean_row_bytes": 0.0})
            db.executemany("INSERT INTO records VALUES (?, ?)", rows)
            # Literal wire row contributions, including a separator each.
            expected = (len(b'[1,"\\"\\\\\\n"],')
                        + len(b'[12345,"\\u00e9\\ud83d\\ude00"],')) / 2
            self.assertEqual(sizing_statistics(db), {"row_count": 2, "mean_row_bytes": expected})

    def test_metadata_bytes_are_included_once_and_results_stay_exact(self):
        for rows, overlap in ((0, 0), (10, 0), (10, 0.5), (10, 1)):
            with self.subTest(rows=rows, overlap=overlap), tempfile.TemporaryDirectory() as tmp:
                local, remote = generate(tmp, rows, overlap, 8, 42)
                baseline = run(local, remote)
                measured = run(local, remote, collect_sizing=True)
                with closing(sqlite3.connect(remote)) as db:
                    stats = sizing_statistics(db)
                expected_bytes = (4 + len(encode_json({"request": "sizing"}))
                                  + 4 + len(encode_json({"sizing": stats})))
                sizing = measured["sizing"]
                self.assertEqual(sizing["metadata_application_bytes"], expected_bytes)
                self.assertEqual(measured["application_bytes"], baseline["application_bytes"] + expected_bytes)
                self.assertEqual(sizing["row_count"], rows)
                self.assertEqual(sizing["mean_row_bytes"], stats["mean_row_bytes"])
                self.assertFalse(sizing["filter_applied"])
                self.assertNotIn("sizing", baseline)
                self.assertTrue(measured["verified"])
                self.assertEqual(measured["result_rows"], int(rows * overlap))
                self.assertEqual(measured["transferred_records"], rows)
                if rows == 0:
                    self.assertEqual((sizing["bit_count"], sizing["hash_count"]), (0, 0))
                else:
                    self.assertGreater(sizing["bit_count"], 0)

    def test_empty_local_table_has_no_filter_proposal(self):
        with tempfile.TemporaryDirectory() as tmp:
            local, remote = generate(tmp, 10, 0, 8, 42)
            with closing(sqlite3.connect(local)) as db:
                db.execute("DELETE FROM records")
                db.commit()
            metrics = run(local, remote, collect_sizing=True)
            self.assertTrue(metrics["verified"])
            self.assertEqual(metrics["sizing"]["local_count"], 0)
            self.assertEqual(metrics["sizing"]["bit_count"], 0)
            self.assertEqual(metrics["result_rows"], 0)

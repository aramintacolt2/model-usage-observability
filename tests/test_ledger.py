import pathlib
import sqlite3
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))
from usage.ledger import UsageRecord, export, init, record, summary


class LedgerTests(unittest.TestCase):
    def item(self, request_id="r1"):
        return UsageRecord(request_id=request_id, task_id="t1", provider="argolink", model="gpt-5.4", endpoint="responses", input_tokens=20, cached_input_tokens=5, output_tokens=3, cost_usd=.0001, status="success", catalog_date="2026-10-07", started_at="2026-10-07T00:00:00Z", completed_at="2026-10-07T00:00:01Z")

    def test_roundtrip_and_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            db = pathlib.Path(directory) / "usage.db"
            init(db)
            record(db, self.item())
            out = pathlib.Path(directory) / "usage.csv"
            self.assertEqual(export(db, out), 1)
            self.assertIn("gpt-5.4", out.read_text(encoding="utf-8"))
            self.assertEqual(summary(db)["success_rate"], 1.0)

    def test_duplicate_response_id_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            db = pathlib.Path(directory) / "usage.db"
            record(db, self.item())
            with self.assertRaises(sqlite3.IntegrityError):
                record(db, self.item())

    def test_missing_usage_is_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            db = pathlib.Path(directory) / "usage.db"
            item = self.item("r2")
            record(db, UsageRecord(**{**item.__dict__, "input_tokens": None, "output_tokens": None, "cost_usd": None, "status": "unknown"}))
            self.assertEqual(summary(db)["unknown_usage"], 1)

    def test_invalid_record_fails(self):
        with self.assertRaises(ValueError):
            self.item("r3").__class__(**{**self.item("r3").__dict__, "cached_input_tokens": 30}).validate()


if __name__ == "__main__":
    unittest.main()

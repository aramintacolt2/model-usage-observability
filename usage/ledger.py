"""Client-side usage ledger; it is not a provider billing API."""
from __future__ import annotations

import csv
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS requests (
  request_id TEXT PRIMARY KEY,
  task_id TEXT,
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  input_tokens INTEGER,
  cached_input_tokens INTEGER,
  output_tokens INTEGER,
  cost_usd REAL,
  status TEXT NOT NULL,
  error_class TEXT,
  catalog_date TEXT NOT NULL,
  started_at TEXT NOT NULL,
  completed_at TEXT
)
"""
STATUSES = {"success", "error", "timeout", "cancelled", "unknown"}


@dataclass(frozen=True)
class UsageRecord:
    request_id: str
    provider: str
    model: str
    endpoint: str
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    cost_usd: float | None
    status: str
    catalog_date: str
    started_at: str
    task_id: str = ""
    error_class: str = ""
    completed_at: str | None = None

    def validate(self) -> None:
        if not all(isinstance(value, str) and value.strip() for value in (self.request_id, self.provider, self.model, self.endpoint, self.catalog_date, self.started_at)):
            raise ValueError("request_id, provider, model, endpoint, catalog_date, and started_at are required")
        if self.status not in STATUSES:
            raise ValueError(f"status must be one of {sorted(STATUSES)}")
        for name, value in (("input_tokens", self.input_tokens), ("cached_input_tokens", self.cached_input_tokens), ("output_tokens", self.output_tokens)):
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError(f"{name} must be a non-negative integer or null")
        if self.cached_input_tokens is not None and self.input_tokens is not None and self.cached_input_tokens > self.input_tokens:
            raise ValueError("cached_input_tokens cannot exceed input_tokens")
        if self.cost_usd is not None and (not isinstance(self.cost_usd, (int, float)) or self.cost_usd < 0):
            raise ValueError("cost_usd must be non-negative or null")


def init(path: str | Path) -> None:
    with sqlite3.connect(path) as connection:
        connection.execute(SCHEMA)


def record(path: str | Path, item: UsageRecord) -> None:
    """Insert one immutable response ID; duplicate IDs fail instead of double-counting."""
    item.validate()
    init(path)
    with sqlite3.connect(path) as connection:
        connection.execute(
            """INSERT INTO requests
            (request_id, task_id, provider, model, endpoint, input_tokens, cached_input_tokens,
             output_tokens, cost_usd, status, error_class, catalog_date, started_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (item.request_id, item.task_id, item.provider, item.model, item.endpoint, item.input_tokens, item.cached_input_tokens, item.output_tokens, item.cost_usd, item.status, item.error_class, item.catalog_date, item.started_at, item.completed_at),
        )


def export(path: str | Path, out: str | Path) -> int:
    """Export rows with a stable header; prompt and authorization data are never stored."""
    init(path)
    with sqlite3.connect(path) as connection:
        rows = connection.execute("SELECT request_id, task_id, provider, model, endpoint, input_tokens, cached_input_tokens, output_tokens, cost_usd, status, error_class, catalog_date, started_at, completed_at FROM requests ORDER BY started_at, request_id").fetchall()
    columns = ["request_id", "task_id", "provider", "model", "endpoint", "input_tokens", "cached_input_tokens", "output_tokens", "cost_usd", "status", "error_class", "catalog_date", "started_at", "completed_at"]
    with Path(out).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    return len(rows)


def summary(path: str | Path) -> dict[str, float | int | None]:
    init(path)
    with sqlite3.connect(path) as connection:
        row = connection.execute("SELECT COUNT(*), SUM(CASE WHEN status='success' THEN 1 ELSE 0 END), SUM(cost_usd), SUM(CASE WHEN input_tokens IS NULL OR output_tokens IS NULL THEN 1 ELSE 0 END) FROM requests").fetchone()
    count, successes, cost, unknown = row
    return {"count": count, "successes": successes or 0, "success_rate": round((successes or 0) / count, 4) if count else None, "estimated_usd": round(cost or 0, 8), "unknown_usage": unknown or 0}

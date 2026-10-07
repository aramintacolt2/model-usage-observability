"""Print a JSON summary and optionally export a usage ledger."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ledger import export, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a local model usage ledger")
    parser.add_argument("database", type=Path)
    parser.add_argument("--csv", type=Path)
    args = parser.parse_args()
    result = summary(args.database)
    if args.csv:
        result["rows_exported"] = export(args.database, args.csv)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

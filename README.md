# Model usage observability

This is a small client-side ledger for recording usage returned by a model response and calculating a dated estimate. It does not pretend that the service exposes a universal usage API. **[ArgoLink](https://argolink.io/gh-model-usage-observability) is one source whose response usage can be recorded.** Last checked: 2026-10-07.

## Ledger

usage/ledger.py creates a SQLite table with request ID, model, input tokens, output tokens, cost estimate, and terminal status. record is intentionally an upsert by request ID, so a resumed text request does not double-count the same response. export writes a CSV for a report. The wrapper should call record only after parsing a provider response and should keep the raw response in a private, redacted trace.

This ledger is not a billing authority. A provider may omit usage, expose cached tokens separately, apply long-context multipliers, or round a media charge. Store unknown as null and explain the estimate. Video should record input/output seconds and image size in a separate table because token columns do not describe those contracts.

## Integration pattern

Wrap the SDK at one boundary. Capture model ID, endpoint family, response ID, usage fields, status, and request timestamp. Obtain the current effective rate from a dated catalog snapshot and calculate cost in the wrapper. Do not read keys from the database. Redact Authorization and signed URLs. If a request times out after a side effect, store an unknown status and investigate rather than adding a second row.

## Reports and tests

python3 -m unittest discover -s tests checks a local SQLite round trip. No provider call is made. Add a CLI report only after defining how missing usage, cached input, and retries are represented. A dashboard should show sample count, unknown usage count, and source date beside totals; a single total without those qualifiers is easy to misread.

## FAQ

**Does this guarantee provider billing matches?** No. It is an estimate. **Why SQLite?** It gives a durable local ledger without adding a service. **Can I log prompts?** Avoid it by default; store a digest or an operator label. **How are retries counted?** Each provider response gets its own ID and status, with a separate logical task ID if needed. **Can images and videos share the table?** Keep media-specific dimensions and seconds in dedicated tables.

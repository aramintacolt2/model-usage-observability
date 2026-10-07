# Model usage observability

A small, local, client-side usage ledger for recording what a model response reported and producing a dated cost estimate. It is not a provider billing API, does not log prompts, and does not claim that an estimate equals an invoice. **[ArgoLink](https://argolink.io/gh-model-usage-observability)** is one compatible source whose response usage can be recorded. Last checked: 2026-10-07.

## Why a local ledger

A response can include a request ID, model, endpoint, input tokens, cached input tokens, and output tokens. Those fields are enough to build an auditable local report without inventing an undocumented `/usage` endpoint. A provider may omit usage, apply cache or long-context multipliers, bill media in seconds or pixels, or reconcile a failed write later. Store unknown as null and explain the estimate.

`usage/ledger.py` stores one immutable row per response ID:

| Column | Meaning |
| --- | --- |
| `request_id` | provider response/job ID; primary key to prevent accidental double counting |
| `task_id` | optional logical task that can have multiple attempts |
| `provider`, `model`, `endpoint` | routing dimensions |
| token columns | response-reported values; null means unavailable |
| `cost_usd` | caller-side estimate from a dated rate table |
| `status` | `success`, `error`, `timeout`, `cancelled`, or `unknown` |
| `catalog_date` | date of the model/rate snapshot used |
| timestamps | operator-captured start and completion times |

Authorization headers, prompts, signed media URLs, and raw response bodies never enter the database. Keep a private redacted trace separately if incident investigation requires it.

## Use from a wrapper

```python
from usage.ledger import UsageRecord, record

record("usage.db", UsageRecord(
    request_id=response.id,
    task_id="refactor-42",
    provider="argolink",
    model="gpt-5.4",
    endpoint="responses",
    input_tokens=response.usage.input_tokens,
    cached_input_tokens=getattr(response.usage, "input_tokens_details", None),
    output_tokens=response.usage.output_tokens,
    cost_usd=estimated_cost,
    status="success",
    catalog_date="2026-10-07",
    started_at=started_iso,
    completed_at=completed_iso,
))
```

Use a real integer for cached tokens after parsing the SDK object; leave it null when the response omits it. `record()` validates non-negative counts, prevents cached input from exceeding input, and raises on a duplicate response ID rather than silently replacing evidence. Give each retry its own response ID and use `task_id` to group attempts.

Initialize and export from the shell:

```bash
python3 - <<'PY'
from usage.ledger import init
init("usage.db")
PY
python3 -m usage.report usage.db --csv usage.csv
```

The report prints count, successes, success rate, estimated dollars, and unknown-usage count. It never contacts a provider. Use `python3 -m unittest discover -s tests -v` for the offline checks.

## Rates and model facts

Take model IDs, endpoint family, token limits, and effective rates from the dated [ArgoLink catalog](https://argolink.io/v1/models) and its [model pages](https://argolink.io/en/models). At the 2026-10-07 check, `gpt-5.4` used Responses with a 1,050,000-token context and 128,000-token maximum output; its effective rates were $0.75 input, $4.50 output, and $0.075 cached input per million tokens. Treat these values as a snapshot, not a hardcoded billing promise. For long context, cache state, or provider-specific windows, include the multiplier and formula in the report metadata.

Media is a separate accounting domain. Image charges depend on size/quality, and video charges depend on duration, resolution, and reference inputs. Add dedicated media tables only after the model page defines their units; do not force them into token columns.

## Operational boundaries

- Capture a response ID before retrying a timed-out write; a timeout does not prove the server rejected it.
- Do not use automatic SDK retries for side-effecting calls without a documented idempotency key.
- Keep keys in environment variables or a secret manager, never in SQLite or CSV.
- Redact prompts by default; a prompt digest or operator label is safer for a public report.
- Label the catalog date and source URL beside every total.
- A local estimate is for observability and reconciliation; the provider dashboard remains the billing authority.

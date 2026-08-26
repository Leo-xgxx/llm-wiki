# Observability

What the system records about itself, and what people look at.

## Four sources

| Source | Written by | Contains | Retention |
|---|---|---|---|
| runtime traces | the answering runtime, per request | task normalization, route rungs used, cards loaded, adapter calls, disclosures emitted, token and time cost | short; outside Git |
| gap records | runtime and people | the record contract in `gap.schema.json` | until closed and archived |
| evaluation results | the gates, per revision | routing and golden results per record, rank and margin per expected card, layer per card | per release |
| usage statistics | a scheduled aggregation over traces | counts per domain, per card, per rung, per disclosure kind; no identities | rolling |

None of the four contains user identifiers. Aggregations are keyed by role, domain and card.

## Detectors

Detectors run on a schedule, produce gap records or findings, and never edit cards.

| Detector | Signal | Produces |
|---|---|---|
| drift patrol | a registry contract's origin changed (schema, view definition) since `captured_on` | a `wrong-answer` or `coverage-gap` lead on the cards indexing it |
| usage audit | cards answered often with a disclosure; questions answered from rung 5–6; recurring ask-backs | `ranking-miss` leads, alias candidates |
| asset discovery | interfaces referenced by questions but absent from any interface card | `coverage-gap` leads with `interface-locate` shape |
| freshness runner | `review_after <= as_of` | sets effective status `stale`; writes a re-verification gap record for sentinel intake; a ticket requires the three-way eligibility gate |
| coverage statistics | cards per type per domain, certified share, cards without any eval, metrics without an interface | a report, not a ticket |

## Reading the numbers

- Daily counts depend on the day boundary and timezone the aggregation uses; state it on every report.
- "Answered" and "answered from certified knowledge" are different columns; a rising first with a flat second is a warning.
- A card that is never retrieved is not necessarily useless; check whether its evals still pass before proposing deletion.
- The interesting rung is not the top one: answers that needed rung 4 or below are the routing backlog.

## Dashboards

Two views are enough:

1. **Operations**: run outcomes, warden escalations, merge-lock state, queue depth. For maintainers.
2. **Team**: aggregate usage without identities — questions per domain, certified-answer share, open gaps per door, median time from gap to merge. Shareable.

A dashboard with identities (who asked what) is a separate, access-controlled artifact if it exists at all, and never the default.

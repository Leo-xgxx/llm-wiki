# Acme Analytics · domain handbook

Read this file before any card in the domain. Rules here override card prose; cards override nothing here.

## Hard rules

1. Revenue metrics use the order recognition date as the time axis. Never regroup by creation date or refund date.
2. Pending orders and pending refunds are excluded from every revenue figure. The execution contract on each metric card enforces this; do not re-derive it from prose.
3. An unqualified "revenue" question means net revenue and must disclose that completed refunds were subtracted. See `acme-analytics.consistency.revenue-term`.
4. Dashboard framing (for example the sample-region exclusion on the commerce overview) applies only when the question names that dashboard.
5. The `demo` adapter is fictional. Execution is never available in this repository; report the procedure and the interface, never a number.

## Domain boundaries

| Sounds like this domain | Actually owned by | What we know here |
|---|---|---|
| why a refund was granted, support cases | `acme-support` | only how completed refunds reduce revenue |
| cash collected, settlement timing | `acme-finance` | only that net revenue is not cash |

## Where things live

| Question shape | Start at |
|---|---|
| definition, formula, filters | `wiki/metrics/` |
| what a field value means | `wiki/dimensions/` |
| a term that two cards share | `wiki/consistency/` |
| how to produce a breakdown | `wiki/playbooks/` |
| a known way to get it wrong | `wiki/traps/` |
| where to look, what a view shows | `wiki/dashboards/`, `wiki/datasets/` |
| what evidence a card rests on | `wiki/sources/` and `raw/source-contracts.yaml` |

## Maintenance notes

- New value in `order_status`: set the dimension card to `needs-decision` and re-check the authoritative interface contract; do not edit the value list by observation. If review confirms the old card is invalid, deprecate or replace it.
- New metric that shares a word with an existing one: write the consistency card in the same change.

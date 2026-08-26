---
id: acme-analytics.dimension.order-status
type: dimension
domain: acme-analytics
title: Order status
summary: Value domain of the order_status field and which values count as recognized.
status: needs-decision
status_note: The interface contract now lists on_hold; whether it counts as recognized revenue is undecided.
knowledge_role: canonical
maintainer: demo-maintainer
aliases:
  - order_status
scope:
  grain: one value per order
  time_semantics: current state at query time; history is not kept in the interface
  dimensions: []
  filters: []
value_domain:
  source_ref: acme-analytics.synthetic.orders-v1
  captured_on: "2026-08-25"
  open: false
  values:
    - value: completed
      meaning: paid and fulfilled; the only state that counts as recognized
    - value: pending
      meaning: created but not yet paid or fulfilled
    - value: on_hold
      meaning: payment authorized but not yet fulfilled; recognition rule pending owner decision
    - value: cancelled
      meaning: closed without fulfilment; never recognized
      deprecated: false
source_refs:
  - acme-analytics.synthetic.orders-v1
relations:
  depends_on: []
  related:
    - acme-analytics.metric.net-revenue
    - acme-analytics.metric.gross-revenue
  supersedes: []
evidence:
  - kind: interface-contract
    ref: acme-analytics.synthetic.orders-v1
    checked_at: "2026-08-26"
freshness:
  last_verified: "2026-08-26"
  review_after: "2027-02-26"
---

# Order status

## Definition

- `order_status` has a closed value domain of four values in the interface contract; only `completed` is recognized today.
- The list comes from the interface contract, not from observing data. The new `on_hold` value appeared in the contract on 2026-08-26; this card is `needs-decision` until an owner rules whether it counts as recognized.

## Value domain

| value | meaning | recognized |
|---|---|---|
| completed | paid and fulfilled | yes |
| pending | created, not yet paid or fulfilled | no |
| on_hold | payment authorized, not yet fulfilled | undecided |
| cancelled | closed without fulfilment | no |

## Common mistakes

- Filtering `order_status != 'cancelled'` includes pending orders and overstates revenue.
- Treating the current status as historical: an order that was pending yesterday and completed today counts today.
- Applying a filter for `on_hold` before the owner decision is recorded.

## Caveats

Synthetic example only. Do not treat `on_hold` as recognized or excluded until the semantic decision is recorded.

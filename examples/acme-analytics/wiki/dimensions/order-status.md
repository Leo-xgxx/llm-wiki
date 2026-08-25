---
id: acme-analytics.dimension.order-status
type: dimension
domain: acme-analytics
title: Order status
summary: Value domain of the order_status field and which values count as recognized.
status: certified
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
    - value: cancelled
      meaning: closed without fulfilment; never recognized
      deprecated: false
source_refs:
  - acme-analytics.synthetic.orders-v1
relations:
  depends_on: []
  related:
    - acme-analytics.metric.net-revenue
  supersedes: []
evidence:
  - kind: interface-contract
    ref: acme-analytics.synthetic.orders-v1
    checked_at: "2026-08-25"
  - kind: semantic-decision
    ref: acme-analytics.synthetic.net-revenue-v1
    checked_at: "2026-08-25"
freshness:
  last_verified: "2026-08-25"
  review_after: "2027-02-25"
---

# Order status

## Definition

- `order_status` has a closed value domain of three values; only `completed` is recognized.
- The list comes from the interface contract, not from observing data; if a new value appears, the interface contract changed and this card is stale.

## Value domain

| value | meaning | recognized |
|---|---|---|
| completed | paid and fulfilled | yes |
| pending | created, not yet paid or fulfilled | no |
| cancelled | closed without fulfilment | no |

## Common mistakes

- Filtering `order_status != 'cancelled'` includes pending orders and overstates revenue.
- Treating the current status as historical: an order that was pending yesterday and completed today counts today.

## Caveats

Synthetic example only.

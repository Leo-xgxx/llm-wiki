---
id: acme-analytics.playbook.net-revenue-by-region
type: playbook
domain: acme-analytics
title: Net revenue by region
summary: How to produce a regional net revenue breakdown through the daily orders interface.
status: certified
knowledge_role: canonical
maintainer: demo-maintainer
aliases:
  - regional net revenue
procedure:
  question_shape: net revenue split by region for a date range
  executable: true
  inputs:
    - date range on recognition_date
    - optional product_category filter
  outputs:
    - one row per region and day
source_refs:
  - acme-analytics.synthetic.orders-interface-v1
  - acme-analytics.synthetic.net-revenue-v1
relations:
  depends_on:
    - acme-analytics.metric.net-revenue
    - acme-analytics.dataset.orders-daily
  related:
    - acme-analytics.trap.pending-refund-double-count
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

# Net revenue by region

## Procedure

1. Apply the net-revenue execution contract: `order_status = completed`, `refund_status in (completed, none)`.
2. Restrict `recognition_date` to the requested range; default to the contract's 30-day window when none is given.
3. Group by `region` and `recognition_date`; compute `sum(gross_amount) - sum(refund_amount)`.
4. Report the unit as demo currency and disclose the window used.

## When this playbook does not apply

- The question asks for cash collected or refund rate: different canonical cards.
- The requested region value is not in the interface's value domain: report the miss instead of guessing.

## Failure behaviour

If the `demo` adapter is unavailable, return the procedure and the interface name; never return invented numbers.

## Caveats

Synthetic example only.

---
id: acme-analytics.metric.net-sales
type: metric
domain: acme-analytics
title: Net sales (legacy)
summary: Legacy daily revenue definition that subtracted refunds on the refund date instead of the order recognition date.
status: deprecated
status_note: Replaced when the refund-date attribution was ruled inconsistent with recognition-date reporting.
knowledge_role: canonical
importance: general
maintainer: demo-maintainer
aliases: []
scope:
  grain: day
  time_semantics: order recognition date for orders, refund date for refunds
  dimensions:
    - region
  filters:
    - include completed orders
    - subtract refunds on the refund date
definition:
  formula: sum(gross_amount) - sum(refund_amount_by_refund_date)
  unit: demo currency
source_refs:
  - acme-analytics.synthetic.orders-v1
relations:
  depends_on: []
  related: []
  supersedes: []
evidence:
  - kind: interface-contract
    ref: acme-analytics.synthetic.orders-v1
    checked_at: "2026-07-10"
freshness:
  last_verified: "2026-07-10"
  review_after: "2026-08-10"
retirement:
  outcome: replaced
  target_card: acme-analytics.metric.net-revenue
  reason: Refund attribution moved to the order recognition date so that one day's revenue never changes after the fact.
  retired_on: "2026-08-01"
---

# Net sales (legacy)

## Definition

- Historical only. Refunds were attributed to the day they completed, so a day's figure could keep changing for weeks.
- Use `acme-analytics.metric.net-revenue` for any current question.

## Why it was retired

Reports built on this definition disagreed with recognition-date reports by the amount of refunds that crossed a day boundary. The domain owner role ruled that recognized revenue must be stable once a day closes.

## Caveats

This card stays in the tree only while inbound links are being cleaned. Its reviewed tombstone already exists in `retirements.jsonl`; deletion will add `deleted_on` without changing the recorded final-card hash.

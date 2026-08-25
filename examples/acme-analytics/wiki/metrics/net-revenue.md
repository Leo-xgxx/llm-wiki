---
id: acme-analytics.metric.net-revenue
type: metric
domain: acme-analytics
title: Net revenue
summary: Daily recognized revenue after subtracting completed refunds.
status: certified
status_note: Certified by the domain owner role after the refund-handling decision was recorded.
knowledge_role: canonical
importance: north-star
confidence: high
maintainer: demo-maintainer
aliases:
  - revenue after refunds
  - daily net sales
  - net_revenue
scope:
  grain: day
  time_semantics: order recognition date
  dimensions:
    - product category
    - region
  filters:
    - include completed orders
    - subtract completed refunds
definition:
  formula: sum(gross_amount) - sum(refund_amount)
  unit: demo currency
execution_contract:
  always_filter:
    - field: order_status
      op: eq
      value: completed
      reason: pending orders are not recognized revenue
    - field: refund_status
      op: in
      value: [completed, none]
      reason: pending refunds must not be subtracted yet
  time_default:
    window: last 30 days
    grain: day
source_refs:
  - acme-analytics.synthetic.orders-v1
  - acme-analytics.synthetic.net-revenue-v1
relations:
  depends_on:
    - acme-analytics.concept.recognition-date
    - acme-analytics.dimension.order-status
  related:
    - acme-analytics.metric.gross-revenue
    - acme-analytics.trap.pending-refund-double-count
  supersedes:
    - acme-analytics.metric.net-sales
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

# Net revenue

## Definition

- Net revenue is completed-order gross amount minus completed refunds, grouped by the order recognition date.
- Pending orders and pending refunds are excluded; the exclusion is enforced by the execution contract, not by the reader.
- A bare "revenue" question defaults to this card; see the revenue-term consistency card for the ruling.

## Scope

The default grain is one day. Product category and region are optional dimensions. The time axis is the recognition date, not the order creation date.

## Interpretation

This metric measures recognized commercial value after refunds. It is not the same as cash collected or gross order value.

## Common mistakes

- Subtracting pending refunds double-counts once they complete; see `acme-analytics.trap.pending-refund-double-count`.
- Grouping by order creation date shifts revenue across day boundaries.

## Suggested analysis

Compare with gross revenue to obtain the refund share; split by region through the daily orders interface.

## Caveats

All names and values in this card are synthetic.

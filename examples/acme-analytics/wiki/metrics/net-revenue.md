---
id: acme-analytics.metric.net-revenue
type: metric
domain: acme-analytics
title: Net revenue
summary: Daily recognized revenue after subtracting completed refunds.
status: certified
knowledge_role: canonical
maintainer: demo-maintainer
aliases:
  - revenue after refunds
  - daily net sales
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
source_refs:
  - acme-analytics.synthetic.orders-v1
  - acme-analytics.synthetic.net-revenue-v1
relations:
  depends_on: []
  related: []
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

# Net revenue

## Definition

Net revenue is completed-order gross amount minus completed refunds, grouped by the order recognition date.

## Scope

The default grain is one day. Product category and region are optional dimensions. Pending orders and pending refunds are excluded.

## Interpretation

This metric measures recognized commercial value after refunds. It is not the same as cash collected or gross order value.

## Examples

A request for “revenue after completed refunds by day” uses this definition. A request for refund rate or cash collection does not.

## Caveats

All names and values in this card are synthetic.

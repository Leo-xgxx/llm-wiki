---
id: acme-analytics.metric.gross-revenue
type: metric
domain: acme-analytics
title: Gross revenue
summary: Daily recognized order value before any refund is subtracted.
status: certified
knowledge_role: canonical
importance: secondary
confidence: high
maintainer: demo-maintainer
aliases:
  - gross order value
  - gross_amount total
scope:
  grain: day
  time_semantics: order recognition date
  dimensions:
    - product category
    - region
  filters:
    - include completed orders
definition:
  formula: sum(gross_amount)
  unit: demo currency
execution_contract:
  required_fields:
    - recognition_date
    - product_category
    - region
  always_filter:
    - field: order_status
      op: eq
      value: completed
      reason: only completed orders are recognized
source_refs:
  - acme-analytics.synthetic.orders-v1
  - acme-analytics.synthetic.gross-revenue-v1
relations:
  depends_on:
    - acme-analytics.concept.recognition-date
  related:
    - acme-analytics.metric.net-revenue
  supersedes: []
evidence:
  - kind: interface-contract
    ref: acme-analytics.synthetic.orders-v1
    checked_at: "2026-08-25"
  - kind: semantic-decision
    ref: acme-analytics.synthetic.gross-revenue-v1
    checked_at: "2026-08-25"
freshness:
  last_verified: "2026-08-25"
  review_after: "2027-02-25"
---

# Gross revenue

## Definition

- Gross revenue is the completed-order gross amount grouped by recognition date, with no refund adjustment.
- It exists as the numerator-side reference for refund share and as the value that finance reconciles before adjustments.

## Scope

Same grain, time axis and dimensions as net revenue. Refund status is ignored entirely.

## Interpretation

Gross revenue is always greater than or equal to net revenue for the same day and slice. A gap between the two is the refund effect, never a data error by itself.

## Common mistakes

- Answering a bare "revenue" question with this card. The consistency card rules that the bare term means net revenue.

## Caveats

Synthetic example only.

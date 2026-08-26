---
id: acme-analytics.dashboard.commerce-overview
type: dashboard
domain: acme-analytics
title: Commerce overview dashboard
summary: Synthetic dashboard that shows gross and net revenue by day with a region filter, framed to exclude the sample region.
status: certified
knowledge_role: interface
maintainer: demo-maintainer
aliases:
  - commerce overview
canonical_cards:
  - acme-analytics.metric.net-revenue
  - acme-analytics.metric.gross-revenue
scope:
  grain: day
  time_semantics: recognition date, last 90 days by default
  dimensions:
    - region
  filters:
    - excludes the sample region on every chart
query_interface:
  adapter: demo
  asset_key: acme-analytics.demo.commerce-overview
  logical_fields:
    - recognition_date
    - region
    - order_status
    - refund_status
    - gross_amount
    - refund_amount
  availability:
    status: unavailable
    reason: the demo adapter is fictional and has no executable connection in this repository
  refresh: daily
execution_contract:
  required_fields:
    - recognition_date
    - order_status
    - refund_status
    - gross_amount
    - refund_amount
  by_layer:
    - layer: revenue-trend-chart
      metrics:
        - acme-analytics.metric.net-revenue
        - acme-analytics.metric.gross-revenue
      require_filter:
        - field: region
          op: neq
          value: sample
          reason: the dashboard owner excludes the internal sample region from every chart
source_refs:
  - acme-analytics.synthetic.commerce-overview-v1
relations:
  depends_on: []
  related:
    - acme-analytics.dataset.orders-daily
  supersedes: []
evidence:
  - kind: interface-contract
    ref: acme-analytics.synthetic.commerce-overview-v1
    checked_at: "2026-08-25"
  - kind: semantic-decision
    ref: acme-analytics.synthetic.orders-interface-v1
    checked_at: "2026-08-25"
freshness:
  last_verified: "2026-08-25"
  review_after: "2027-02-25"
---

# Commerce overview dashboard

## Interface

A synthetic dashboard with one revenue trend chart and a region selector. It reads the same logical fields as the daily orders interface.

## Framing versus definition

The dashboard excludes the `sample` region on every chart. That is a framing choice of this view, so it lives in `execution_contract.by_layer` for this card. It is not part of the net-revenue definition and must not be copied into the metric's `always_filter`; a question about net revenue that does not mention the dashboard includes the sample region.

## Boundaries

This card locates the view and records its framing. Definitions belong to the canonical metric cards.

## Examples

"What does the overview dashboard show for net revenue?" applies the by-layer filter. "What is net revenue?" does not.

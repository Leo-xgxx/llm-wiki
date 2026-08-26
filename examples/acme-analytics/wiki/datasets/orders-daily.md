---
id: acme-analytics.dataset.orders-daily
type: dataset
domain: acme-analytics
title: Daily orders interface
summary: Synthetic logical dataset used to demonstrate a thin interface card.
status: certified
knowledge_role: interface
maintainer: demo-maintainer
aliases:
  - demo daily orders
  - orders_daily
canonical_cards:
  - acme-analytics.metric.net-revenue
  - acme-analytics.metric.gross-revenue
  - acme-analytics.dimension.order-status
  - acme-analytics.concept.recognition-date
scope:
  grain: one row per order
  time_semantics: partitioned by order recognition date
  dimensions:
    - product category
    - region
  filters: []
query_interface:
  adapter: demo
  asset_key: acme-analytics.demo.orders-daily
  logical_fields:
    - recognition_date
    - order_status
    - refund_status
    - gross_amount
    - refund_amount
    - product_category
    - region
  availability:
    status: unavailable
    reason: the demo adapter is fictional and has no executable connection in this repository
  refresh: daily, previous day complete by early morning
source_refs:
  - acme-analytics.synthetic.orders-v1
  - acme-analytics.synthetic.orders-interface-v1
relations:
  depends_on: []
  related:
    - acme-analytics.dimension.order-status
  supersedes: []
evidence:
  - kind: interface-contract
    ref: acme-analytics.synthetic.orders-v1
    checked_at: "2026-08-25"
  - kind: semantic-decision
    ref: acme-analytics.synthetic.orders-interface-v1
    checked_at: "2026-08-25"
freshness:
  last_verified: "2026-08-25"
  review_after: "2027-02-25"
---

# Daily orders interface

## Interface

This fictional logical dataset exposes one row per order through the `demo` adapter and partitions access by the order recognition date.

## Access shape

The logical contract exposes recognition date, order and refund status, gross and refund amounts, product category, and region. It contains no physical table, query expression, or credential.

## Boundaries

The dataset card owns only interface location, row grain, logical fields, and availability. The daily aggregation and completed-status filters belong to the canonical metric cards; this intentional grain difference does not transfer semantic ownership to the interface.

## Examples

An execution planner may pair this interface with the net-revenue card when the adapter is available. In this repository the adapter is fictional, so execution must remain unavailable rather than returning invented values.

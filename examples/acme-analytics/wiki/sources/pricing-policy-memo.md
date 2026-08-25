---
id: acme-analytics.source.pricing-policy-memo
type: source
domain: acme-analytics
title: Pricing policy memo (snapshot)
summary: Managed snapshot of the fictional memo that fixed refund handling and the meaning of the bare term revenue.
status: certified
knowledge_role: evidence
maintainer: demo-maintainer
aliases: []
index_to:
  - acme-analytics.metric.net-revenue
  - acme-analytics.consistency.revenue-term
snapshot:
  registry_ref: acme-analytics.synthetic.pricing-memo-snapshot-v1
  captured_on: "2026-08-25"
  origin_kind: document
  trust: authoritative
source_refs:
  - acme-analytics.synthetic.pricing-memo-snapshot-v1
relations:
  depends_on: []
  related: []
  supersedes: []
evidence:
  - kind: document-snapshot
    ref: acme-analytics.synthetic.pricing-memo-snapshot-v1
    checked_at: "2026-08-25"
  - kind: semantic-decision
    ref: acme-analytics.synthetic.revenue-term-ruling-v1
    checked_at: "2026-08-25"
freshness:
  last_verified: "2026-08-25"
  review_after: "2027-02-25"
---

# Pricing policy memo (snapshot)

## What this source is

A fictional internal memo, captured once, that states two things: refunds reduce revenue only once completed, and "revenue" in reports means the net figure. The snapshot itself would live under `raw/` with a provenance header; this card is the bridge that tells the graph which canonical cards the snapshot supports.

## What was extracted

- Refund handling → `acme-analytics.metric.net-revenue` execution contract.
- Meaning of the bare term → `acme-analytics.consistency.revenue-term`.

## What was deliberately not extracted

Draft pricing tiers discussed in the memo. They were marked as proposals, so they are not knowledge yet; a gap record would be the right place if someone asks.

## Caveats

Synthetic example only. No real document exists behind this card.

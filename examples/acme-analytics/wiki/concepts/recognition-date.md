---
id: acme-analytics.concept.recognition-date
type: concept
domain: acme-analytics
title: Recognition date
summary: The date on which an order counts toward revenue, as opposed to its creation or refund date.
status: certified
knowledge_role: canonical
maintainer: demo-maintainer
aliases:
  - recognition_date
  - recognized date
source_refs:
  - acme-analytics.synthetic.orders-v1
  - acme-analytics.synthetic.net-revenue-v1
relations:
  depends_on: []
  related:
    - acme-analytics.metric.net-revenue
    - acme-analytics.metric.gross-revenue
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

# Recognition date

## Definition

- The recognition date is the day an order became `completed`. All revenue metrics in this domain use it as the time axis.
- It differs from the creation date (when the order was placed) and from any refund date (when a refund completed).

## Why it matters

Using the recognition date makes a closed day immutable: later refunds are attributed back to the day the order was recognized, so history does not drift. This was the reason the legacy net-sales definition was retired.

## Not to be confused with

- Creation date: shifts revenue earlier for orders that take days to complete.
- Refund date: the axis the legacy definition used; produces drifting history.

## Caveats

Synthetic example only.

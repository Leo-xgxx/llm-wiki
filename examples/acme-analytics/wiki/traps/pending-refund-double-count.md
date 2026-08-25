---
id: acme-analytics.trap.pending-refund-double-count
type: trap
domain: acme-analytics
title: Pending refunds double-count when subtracted early
summary: Subtracting refunds while they are pending and again when they complete understates net revenue twice.
status: certified
knowledge_role: canonical
maintainer: demo-maintainer
aliases: []
trap:
  kind: definition
  severity: high
  symptom: net revenue for recent days is lower than expected and rises back after refunds complete
  detection: compare the refund_status filter in the query with the execution contract; any query that subtracts refund_amount where refund_status = pending is affected
  workaround: apply the execution contract of the net-revenue card; pending refunds contribute zero until completed
  fixed: false
source_refs:
  - acme-analytics.synthetic.net-revenue-v1
  - acme-analytics.synthetic.refund-timing-observation-v1
relations:
  depends_on: []
  related:
    - acme-analytics.metric.net-revenue
    - acme-analytics.playbook.net-revenue-by-region
  supersedes: []
evidence:
  - kind: observed-output
    ref: acme-analytics.synthetic.refund-timing-observation-v1
    checked_at: "2026-08-20"
  - kind: semantic-decision
    ref: acme-analytics.synthetic.net-revenue-v1
    checked_at: "2026-08-25"
freshness:
  last_verified: "2026-08-25"
  review_after: "2027-02-25"
---

# Pending refunds double-count when subtracted early

## Trap

- A refund exists as a row from the moment it is requested, with `refund_status = pending` and a non-zero `refund_amount`.
- Queries that subtract `refund_amount` without filtering on `refund_status` subtract the refund while pending and continue subtracting it once completed. The day's figure dips, then stays low.

## How to detect

Inspect the query's refund filter. If there is none, or it allows `pending`, the result is affected. The execution contract on the net-revenue card is the reference.

## Workaround

Use the execution contract. Pending refunds contribute zero until `refund_status = completed`.

## Caveats

Synthetic example only. The observation contract in the registry records that the pattern was seen, not any real figure.

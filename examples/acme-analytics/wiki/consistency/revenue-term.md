---
id: acme-analytics.consistency.revenue-term
type: consistency
domain: acme-analytics
title: What "revenue" means when unqualified
summary: Arbitration between gross revenue and net revenue for the bare term "revenue".
status: certified
knowledge_role: canonical
maintainer: demo-maintainer
aliases:
  - revenue
arbitration:
  term: revenue
  parties:
    - acme-analytics.metric.net-revenue
    - acme-analytics.metric.gross-revenue
  default_party: acme-analytics.metric.net-revenue
  ruling: An unqualified "revenue" question is answered with net revenue, and the answer must state that refunds were subtracted. A question that says "gross", "before refunds" or "order value" routes to gross revenue.
  ruled_by: domain owner role
  ruled_on: "2026-08-25"
source_refs:
  - acme-analytics.synthetic.revenue-term-ruling-v1
relations:
  depends_on: []
  related:
    - acme-analytics.metric.net-revenue
    - acme-analytics.metric.gross-revenue
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

# What "revenue" means when unqualified

## Ruling

- Bare "revenue" means net revenue. The answer discloses that completed refunds were subtracted.
- "Gross", "before refunds" and "order value" mean gross revenue.
- Neither party may hold the alias `revenue`; this card holds it and routes.

## Why an arbitration card exists

Two canonical cards legitimately compete for one word. Without a ruling, retrieval would pick whichever card happened to score higher that day, and the answer would silently change when either card was edited. The build rejects any alias held by two active cards; the fix is to move the alias here and list both holders as parties.

## Caveats

Synthetic example only.

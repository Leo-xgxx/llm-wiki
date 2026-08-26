---
id: <domain>.consistency.<slug>
type: consistency
domain: <domain>
title: <what the shared term means when unqualified>
summary: <arbitration between the parties for the term>
status: draft             # draft | review | needs-decision | certified | deprecated; never stale
# status_note: <optional context for the chosen lifecycle status>
knowledge_role: canonical
maintainer: <role>
aliases:
  - <the arbitrated term>        # this card holds the term; the parties must not
arbitration:
  term: <the shared surface>
  parties:
    - <card-id>
    - <card-id>
  default_party: <card-id>       # omit when the ruling requires asking back
  ruling: <the rule, including what the answer must disclose>
  ruled_by: <role>
  ruled_on: "YYYY-MM-DD"
source_refs: []
relations:
  depends_on: []
  related: []
  supersedes: []
evidence: []
freshness:
  last_verified: "YYYY-MM-DD"
  review_after: "YYYY-MM-DD"
---

# <title>

## Ruling

- <bare term means which party, and what the answer must disclose>
- <which qualifiers route to the other party>

## Why an arbitration card exists

<the conflict, and why neither party can own the term>

## Caveats

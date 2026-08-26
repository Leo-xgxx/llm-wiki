---
id: <domain>.trap.<slug>
type: trap
domain: <domain>
title: <title>
summary: <the wrong result and its cause in one sentence>
status: draft             # draft | review | needs-decision | certified | deprecated; never stale
# status_note: <optional context for the chosen lifecycle status>
knowledge_role: canonical
maintainer: <role>
aliases: []
trap:
  kind: definition               # production-bug | display | definition | data-quality | access
  severity: medium
  symptom: <what a reader observes>
  detection: <a check that tells whether the trap applies>
  workaround: <what to do instead>
  fixed: false
source_refs: []
relations:
  depends_on: []
  related:
    - <the card this trap threatens>   # at least one
  supersedes: []
evidence: []
freshness:
  last_verified: "YYYY-MM-DD"
  review_after: "YYYY-MM-DD"
---

# <title>

## Trap

- <mechanism: why the wrong result appears>
- <which queries or readings are affected>

## How to detect

<the check, stated so an agent can run it>

## Workaround

<the correct procedure or the contract to apply>

## Caveats

<whether a fix is pending; the observation is recorded as a pattern, not as figures>

---
id: <domain>.playbook.<slug>
type: playbook
domain: <domain>
title: <title>
summary: <what question shape this procedure answers>
status: draft             # draft | review | needs-decision | certified | deprecated; never stale
# status_note: <optional context for the chosen lifecycle status>
knowledge_role: canonical
maintainer: <role>
aliases: []
procedure:
  question_shape: <the shape of question this answers>
  executable: false              # true only with an active interface dependency that bridges every metric dependency
  inputs: []
  outputs: []
source_refs: []
relations:
  depends_on:
    - <metric or dataset card this procedure uses>   # at least one
  related: []
  supersedes: []
evidence: []
freshness:
  last_verified: "YYYY-MM-DD"
  review_after: "YYYY-MM-DD"
---

# <title>

## Procedure

1. <apply the execution contract of the canonical card>
2. <restrict, group, compute>
3. <disclose the window and unit>

## When this playbook does not apply

<question shapes that look similar but belong to other cards>

## Failure behaviour

<what to return when the interface is unavailable; never invented values>

## Caveats

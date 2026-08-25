---
id: <domain>.dimension.<slug>
type: dimension
domain: <domain>
title: <title>
summary: <what the field means and which values matter>
status: draft
knowledge_role: canonical
maintainer: <role>
aliases: []
scope:
  grain: <one value per what>
  time_semantics: <current state or history>
  dimensions: []
  filters: []
value_domain:
  source_ref: <registry contract that lists the values; hand-typed lists are not allowed>
  captured_on: "YYYY-MM-DD"
  open: false                    # true when new values may appear without notice
  values:
    - value: <value>
      meaning: <meaning>
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

## Definition

- <what the field means and where the value list comes from>
- <which values count for the metrics that depend on it>

## Value domain

| value | meaning | note |
|---|---|---|

## Common mistakes

<filters that look right but include the wrong values>

## Caveats

<what to do when a new value appears>

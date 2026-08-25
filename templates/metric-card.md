---
id: <domain>.metric.<slug>
type: metric
domain: <domain>
title: <title>
summary: <one-sentence retrieval surface; no other domain's product names>
status: draft
knowledge_role: canonical
importance: general
maintainer: <role>
aliases: []            # concrete noun surfaces only: field names, report names; never question phrasing
scope:
  grain: <grain>
  time_semantics: <which date axis and why>
  dimensions: []
  filters: []
definition:
  formula: <formula over logical fields exposed by an interface card>
  unit: <unit>
execution_contract:      # optional; machine-executed, wins over prose
  always_filter: []
  time_default:
    window: <default window>
    grain: <default grain>
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

<!-- This section compiles into the brief (hard limit 900 chars). Bullet order is decision weight: the most important conclusion first. No dangling lead-ins ("the two cases are:"), no nested bullets, no other domain's product names, no example enumerations. -->

- <what the metric is, in one sentence>
- <the inclusion rule that most often goes wrong>

## Scope

<grain, time semantics, inclusion and exclusion rules, value-domain handling>

## Interpretation

<how to read the result; which similar concepts must not be mixed with it>

## Common mistakes

<!-- Not scored by retrieval. Examples, enumerations and other domains' names belong here or in Suggested analysis, never in Definition. -->

## Suggested analysis

<what to compare it with; which playbook produces the breakdown>

## Caveats

<unresolved or conditional behaviour; open decisions with who must decide>

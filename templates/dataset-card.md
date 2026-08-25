---
id: <domain>.dataset.<slug>
type: dataset
domain: <domain>
title: <title>
summary: <what this interface locates>
status: draft
knowledge_role: interface
maintainer: <role>
aliases: []
canonical_cards:
  - <canonical-card-id>          # ownership bridge; the build derives the reverse lookup
scope:
  grain: <row grain>
  time_semantics: <partition or time behaviour>
  dimensions: []
  filters: []
query_interface:
  adapter: <adapter name, injected at runtime>
  asset_key: <stable logical key; never a physical location>
  logical_fields:
    - <logical field>
  availability: <availability contract; start with "available" only when a live adapter exists>
  refresh: <cadence and expected lag>
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

## Interface

<logical interface, grain, partition or time behaviour, availability>

## Access shape

<only the stable logical fields canonical formulas need; no physical expressions or credentials>

## Boundaries

<point to canonical cards; do not restate formulas or take semantic ownership>

## Examples

<synthetic usage; what happens when the adapter is unavailable>

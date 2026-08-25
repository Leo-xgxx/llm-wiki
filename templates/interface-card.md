---
id: <domain>.dataset.<slug>
type: dataset
domain: <domain>
title: <title>
summary: <what this interface locates>
status: draft
knowledge_role: interface
maintainer: <maintainer>
aliases: []
canonical_cards:
  - <canonical-card-id>
scope:
  grain: <grain>
  time_semantics: <time semantics>
  dimensions: []
  filters: []
query_interface:
  adapter: <adapter>
  asset_key: <stable logical key>
  logical_fields:
    - <logical field>
  availability: <availability contract>
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

Describe the logical interface, grain, partition or time behavior, and availability.

## Access shape

List only stable logical fields required by canonical formulas. Keep physical expressions and credentials outside this repository.

## Boundaries

Point to canonical cards for definitions. Do not duplicate formulas or semantic ownership here.

## Examples

Add synthetic usage examples and unavailable-interface behavior.

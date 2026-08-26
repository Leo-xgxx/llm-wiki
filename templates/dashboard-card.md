---
id: <domain>.dashboard.<slug>
type: dashboard
domain: <domain>
title: <title>
summary: <what the view shows and how it frames the data>
status: draft
# status_note: <required when status is stale; optional otherwise>
knowledge_role: interface
maintainer: <role>
aliases: []
canonical_cards:
  - <canonical-card-id>
scope:
  grain: <grain of the view>
  time_semantics: <default window>
  dimensions: []
  filters: []                    # human-readable framing; the machine version is execution_contract.by_layer
query_interface:
  adapter: <adapter>
  asset_key: <stable logical key>
  logical_fields:
    - <field or metric exposed by the view>
  availability:
    status: unavailable          # available | unavailable
    reason: <how this state was established>
execution_contract:
  required_fields:       # use [] when no extra logical inputs are needed
    - <logical field exposed by this interface>
  by_layer:
    - layer: <chart or tab name>
      metrics:
        - <active metric card id>
      require_filter: []         # framing that applies only when the question names this view
      forbid_filter: []
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

<what the view contains>

## Framing versus definition

<which filters are this view's framing; state explicitly that they are not part of the canonical definition>

## Boundaries

<definitions live in canonical cards>

## Examples

<a question that applies the framing and one that does not>

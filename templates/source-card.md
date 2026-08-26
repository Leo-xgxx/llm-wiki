---
id: <domain>.source.<slug>
type: source
domain: <domain>
title: <title> (snapshot)
summary: <what the managed snapshot is and what it fixed>
status: draft
# status_note: <required when status is stale; optional otherwise>
knowledge_role: evidence
maintainer: <role>
aliases: []
index_to:
  - <canonical card this snapshot supports>
snapshot:
  registry_ref: <document-snapshot registry contract with a domain-relative artifact path and SHA-256>
  captured_on: "YYYY-MM-DD"
  origin_kind: document          # document | thread | report-definition | schema | second-hand
  trust: authoritative           # authoritative | second-hand | low; must equal registry provenance.trust
source_refs:
  - <same registry contract>
relations:
  depends_on: []
  related: []
  supersedes: []
evidence: []
freshness:
  last_verified: "YYYY-MM-DD"
  review_after: "YYYY-MM-DD"
---

# <title> (snapshot)

## What this source is

<origin kind, capture date, trust level; date and trust match the registry, whose artifact path and hash bind the file under raw/>

## What was extracted

<bullet per canonical card: which statement went where>

## What was deliberately not extracted

<proposals, drafts, figures; and where a question about them should go (a gap record)>

## Caveats

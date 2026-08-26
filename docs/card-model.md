# Card model

## What a card is

A card is a small contract with two synchronized surfaces:

- machine-readable frontmatter for validation, routing, graph construction and execution;
- human-readable prose for definition, scope, caveats, and examples.

A card defines a stable method, not the wording of a temporary question. The test: if another person asked the same thing in different words, would the card still be the right answer? If not, it records a phrasing, not a method.

## Minimum contract

| Field | Purpose |
|---|---|
| `id` | stable global identity, `<domain>.<type>.<slug>`; the prefix must equal `domain` and the middle segment must equal `type` |
| `type` | one of the nine card types below |
| `domain` | canonical ownership boundary |
| `title` / `summary` | human and retrieval surfaces |
| `status` | lifecycle and answer policy |
| `status_note` | optional explanatory context for an author-set status; it never overrides freshness or permits `status: stale` |
| `knowledge_role` | canonical, interface or evidence |
| `relations` | typed graph edges |
| `evidence` | dated review acts against registry contracts |
| `freshness` | last verification and review deadline |

The structural contract is [card.schema.json](../schemas/card.schema.json). The complete authoring contract combines that schema with the cross-record rules in [tools/validate.py](../tools/validate.py): id and directory placement, reference existence, registry and snapshot resolution, supersedes/retirement reciprocity, tombstones, redirects, alias arbitration, execution-field coverage by one interface, freshness, brief length, and manifest hashes. This reference validator checks structure, references, and fixtures; it does not execute retrieval, ranking, an adapter, or answer scoring.

## Card types

| Type | Role | Owns | Required block |
|---|---|---|---|
| `metric` | canonical | formula, unit, grain, time semantics, inclusion rules | `definition`, `scope`, `importance` |
| `dimension` | canonical | the value domain of a field and which values count | `value_domain` with a registry source |
| `concept` | canonical | a term, and what it is not | body only |
| `playbook` | canonical | a procedure that answers one question shape | `procedure`, at least one `depends_on` |
| `trap` | canonical | a known way to get a wrong result, with a detection rule | `trap`, at least one `related` |
| `consistency` | canonical | the ruling when two cards compete for one term | `arbitration` |
| `dataset` | interface | where a logical dataset is and what it exposes | `canonical_cards`, `query_interface`, `scope` |
| `dashboard` | interface | where a view is and how it frames the data | `canonical_cards`, `query_interface` |
| `source` | evidence | a managed snapshot and what was extracted from it | `index_to`, `snapshot` |

An executable playbook depends on at least one active interface card. Every metric in its `depends_on` list must be completely bridged by one of those interface dependencies: that single interface exposes the metric's formula, required-input, and filter fields. A different interface elsewhere in the domain cannot make the playbook executable, and coverage cannot be assembled across partial dependencies.

Extension rule: a new type (entity, pipeline, api, task are the usual candidates) is added only with its own required block, template, synthetic example, validator rule and evaluation record. Placeholder fields must not be invented to satisfy a shared schema.

The rule that keeps the type list short is **no bridge, no card**: content becomes a card only when it plays a role in answering — a definition, a value domain, a procedure, a trap, a ruling, a location, or evidence for one of these. Information that is merely true but plays no role goes into the handbook, the changelog, or nowhere.

## Knowledge roles

### Canonical

Owns a definition, formula, value domain, procedure, trap, or ruling. Other cards reference it instead of reproducing its body.

### Interface

Locates a dataset or view and links to canonical cards. It may describe grain, availability, refresh, partition semantics, and access shape, but it must not take ownership of definitions. It carries:

- `canonical_cards`, the ownership bridge to the cards that define semantics;
- `query_interface`, a logical adapter, stable asset key, logical fields, and availability contract.

An interface without `canonical_cards` is a locator nobody can plan with; a metric without any bridging interface compiles to the `knowledge` layer and can only be explained, never executed.

Availability is structured so that prose cannot accidentally compile as a live adapter:

```yaml
availability:
  status: available        # available | unavailable
  reason: <how this state was established>
```

Only the exact value `status: available` is eligible for direct execution. `reason` is required for both states and is surfaced when execution is unavailable.

An interface exposes only the fields in its own `query_interface.logical_fields`. If the interface also carries an `execution_contract`, every field named by its `required_fields`, `always_filter`, or `by_layer` filters must be in that same list. A `by_layer.metrics` entry is an active metric card id, not a free-form label, and must also appear in that interface's `canonical_cards`; view framing cannot claim a metric the interface does not bridge.

### Evidence

A source card bridges a managed snapshot to the canonical cards it supports. It never defines anything; it records what was extracted and, just as important, what was deliberately not extracted.

All three roles may use `depends_on` and `related` for dependency or navigation across roles. Those relations do not transfer ownership: `canonical_cards` and `index_to` are the ownership bridges, and their targets are canonical cards. `supersedes` records replacement history rather than an ownership edge.

## Body sections and what compiles from them

The body is not free prose. Sections have compile semantics:

| Section | Compiles into | Scored by retrieval |
|---|---|---|
| first `##` section (Definition, Ruling, Interface, Trap, Procedure) | the brief; hard limit 900 characters | yes |
| Scope / Interpretation / Value domain / How to detect | full-card context for `guided` and `knowledge` answers | no |
| Common mistakes / Suggested analysis / Examples | full-card context | no |
| Caveats | disclosure text | no |

Consequences for authors:

- **Bullet order in the first section is decision weight.** Keep the most important conclusion first: a brief over 900 characters is a build error and no artifact is emitted.
- **No dangling lead-ins** ("the two cases are:"), no nested bullets carrying key conclusions. Even inside the limit, each scored statement must stand on its own.
- **Enumerations, examples and other domains' product names go into non-scored sections.** The brief is part of the retrieval surface; rare terms in it pull unrelated questions toward this card (see ranking budget in [retrieval-and-evaluation.md](retrieval-and-evaluation.md)).
- Check the compiled brief, not just the source file, after editing.

## Execution contract

Prose says what a metric means. The `execution_contract` block says what the machine must do:

- `required_fields`: logical input fields that cannot be derived mechanically from the formula or filters, such as the selected time axis, grouping keys, and supported slice fields. It must not repeat a formula identifier or filter field. The property is required for an explicit contract but may be an empty array when no additional inputs exist.
- `always_filter`: filters applied to every execution of the card.
- `by_layer`: filters that apply only when the question names a specific view, chart or consumer. Its optional `metrics` list contains active metric card ids. View framing goes here, never into `always_filter`.
- `time_default`: window and grain used when the question gives none.

Filter operators have machine-level value shapes: `in` and `not_in` take a non-empty array of scalar values; `is_null` and `not_null` take `null`; `eq` and `neq` take one non-null scalar; `gte` and `lte` take one string or number. A mismatched operator/value pair is an invalid contract, not a runtime coercion.

Layer names are unique within a card. The same `field + op + value` condition cannot be both required (`always_filter` or the layer's `require_filter`) and forbidden by that layer; the validator rejects that direct contradiction rather than choosing one side.

The complete field requirement is the union of formula identifiers, `required_fields`, and every field used by `always_filter` or `by_layer`. A metric compiles to `direct` only when one active (present and non-deprecated) interface that bridges to it is exactly `available` and exposes that complete set in its own `logical_fields`. Coverage cannot be assembled by taking different fields from several partial interfaces.

When prose and contract disagree, **the contract wins**. That is why every definition change is a structure change first: contract, handbook, interface bridges, then prose. A change that updates the body and leaves the contract is an unfinished change and a review must reject it.

## Aliases

Aliases are the retrieval surface most likely to break neighbours. Rules:

- concrete noun surfaces only: field names, report names, product terms;
- never question phrasing ("when does X end", "X does not match") — generic words inside such phrases match unrelated questions;
- one surface, one holder: if two active cards need the same alias, a consistency card holds it and lists both as parties.

## Importance

`importance` (`north-star`, `secondary`, `general`) is a review-priority and routing tie-break signal. It never changes answer policy; a `general` certified card is as authoritative as a `north-star` one.

## Lifecycle

| Status | Meaning | Default answer behaviour | Who may set |
|---|---|---|---|
| `draft` | extracted, evidence or wording incomplete | reference only with caveat | anyone |
| `review` | ready for semantic review | reference only with caveat | anyone |
| `needs-decision` | technical evidence sufficient, meaning must be decided by an owner | disclose the open decision | anyone |
| `certified` | evidence and semantics accepted | eligible as a default answer | the certification gate only |
| `deprecated` | replaced by a newer contract | historical navigation only | a reviewed change |
| effective `stale` | freshness contract expired | disclose staleness | freshness runner only; never written into a card file |

The first five rows are card-file statuses. Effective `stale` appears only in derived build or runtime state.

Technical evidence and semantic approval are separate axes. A system can prove how something is currently computed without deciding whether that computation is the intended definition; that gap is exactly `needs-decision`.

`certified` is not a badge, it is a signed obligation: the card must be re-verified before `review_after`. A certified card needs a maintainer role, at least one technical evidence item (schema, interface, implementation, observed output or document snapshot) and one `semantic-decision` whose registry provenance is both `approved` and `authoritative`. A raw source reference, draft decision, or low-trust decision is not approval.

`review_after` is the first expired day, not the last valid day: when `review_after <= as_of`, build or runtime derives an effective `stale` state and blocks undisclosed default use without rewriting the source file. A card file never carries `status: stale`, and `status_note` is not an override. If a person finds unresolved uncertainty, the card-file status becomes `needs-decision`; if a reviewed change confirms that the card is invalid, it becomes `deprecated` with retirement records. Re-verification clears derived staleness by updating the evidence and freshness dates.

Status is a ranking and disclosure signal, not a permission. A non-certified card may still be the best available knowledge; it is shown with its state, not hidden.

## Evidence

Evidence records are dated review acts against contracts in the domain's source registry, never raw dumps. Every registry contract carries a complete provenance record, regardless of evidence kind:

- `schema-contract`, `interface-contract`: the shape of a source;
- `implementation-expression`: how something is computed today;
- `observed-output`: a dated observation used for verification, recorded as a pattern rather than as figures;
- `document-snapshot`: a managed copy of a document, thread or report definition; its registry contract names a domain-relative artifact path and the artifact's SHA-256;
- `semantic-decision`: an explicit ruling by a role.

When evidence conflicts, keep the conflict visible and require human resolution. If the conflict is between two cards over one term, the resolution is a consistency card; if it is inside one card, the status is `needs-decision`.

## Retirement

A deprecated card carries a `retirement` block with an outcome (`replaced`, `merged`, `retired`), a reason and a date. Replaced and merged outcomes name the target; the target must list the old card in `supersedes`. That historical `supersedes` edge remains after deletion: the old id must have a tombstone whose target points back to the replacement. A redirect is added before the file is deleted. Evaluation and gap records may retain the old id: cross-record validation resolves it through the redirect, while active card relations other than `supersedes` must use the current id. See [processing-pipeline.md](processing-pipeline.md) §9.

## Structure before body

Reviews of definition changes repeatedly find the same defect: the prose is right and the structure is old. The order of edits for any definition change is:

1. execution contract on the card;
2. domain handbook hard rules;
3. interface bridges (`canonical_cards`) and consistency cards;
4. evals and changelog;
5. prose.

If step 5 is done and steps 1–4 are not, nothing has changed for the machine, and the old structure will override the new prose.

# Card model

## What a card is

A card is a small contract with two synchronized surfaces:

- machine-readable frontmatter for validation, routing, and graph construction;
- human-readable prose for definition, scope, caveats, and examples.

A card should define a stable method, not preserve the wording of a temporary question.

## Minimum contract

| Field | Purpose |
|---|---|
| `id` | stable global identity |
| `type` | metric or dataset in the initial machine contract |
| `domain` | canonical ownership boundary |
| `title` / `summary` | human and retrieval surfaces |
| `status` | lifecycle and answer policy |
| `knowledge_role` | canonical knowledge or interface bridge |
| `scope` | grain, time semantics, dimensions, and filters |
| `relations` | typed graph edges |
| `evidence` | reviewable support for claims |
| `freshness` | last verification and next review date |

The base structural contract is in [card.schema.json](../schemas/card.schema.json). The complete authoring contract combines that schema with cross-record validation for ID/domain prefixes, reference existence, graph direction, freshness relative to the validation date, formula-to-interface field coverage, and manifest hashes.

IDs use `<domain>.<type>.<slug>`, and the `<domain>` prefix must equal the card's `domain` field. IDs remain stable when titles or aliases change.

## Card types

| Type | Owns |
|---|---|
| `metric` | a formula, unit, grain, time semantics, and inclusion rules |
| `dataset` | a logical data contract or interface and its access shape |

Concept, playbook, trap, and consistency cards are possible future extensions, but they are not valid in this initial machine contract. Each should be added only with its own required fields, template, synthetic example, and evaluation contract; placeholder fields must not be invented to satisfy a shared schema.

## Knowledge roles

### Canonical

Owns a definition, formula, scope, decision rule, or disambiguation. Other cards should reference it instead of reproducing its body.

### Interface

Locates a data or tool interface and links to canonical cards. It may describe grain, availability, partition semantics, and access shape, but it must not take ownership of definitions.

An interface card therefore requires:

- `canonical_cards`, a top-level ownership bridge to the cards that define semantics;
- `query_interface`, containing a logical adapter, stable asset key, required logical fields, and availability contract.

`canonical_cards` is not a general graph edge. A build may derive its reverse projection so that a canonical card can discover compatible interfaces without copying their location details.

## Definitions, sources, and evidence

A canonical metric requires `definition.formula` and `definition.unit`. The formula names only logical fields exposed by an interface contract; physical source expressions remain outside this design repository.

`source_refs` identifies stable source contracts on which the card depends. Every ID must resolve through the domain's machine-readable source registry. `evidence` records dated review acts against those contracts. A certified card needs at least one technical item, such as `schema-contract` or `interface-contract`, and one `semantic-decision`; a raw source reference alone is not approval.

Typed relations have narrower meanings:

- `depends_on`: this card requires another canonical definition to be understood;
- `related`: navigation only, without ownership or dependency;
- `supersedes`: this card replaces an older contract.

Execution or interface location is not a definition dependency. It is represented by an interface card's `canonical_cards` bridge.

## Lifecycle

| Status | Meaning | Default answer behavior |
|---|---|---|
| `draft` | incomplete evidence or wording | reference only with caveat |
| `review` | ready for semantic review | reference only with caveat |
| `needs-decision` | facts are known but meaning is unresolved | disclose the unresolved decision |
| `certified` | evidence and semantics are accepted | eligible as a default answer |
| `deprecated` | replaced by a newer contract | historical navigation only |
| `stale` | freshness contract has expired | disclose staleness |

Technical evidence and semantic approval are separate axes. A system can prove how something is currently computed without deciding whether that computation is the intended definition.

`review_after` is evaluated by validation or runtime policy. Expiry derives an effective stale state and blocks undisclosed default use; it does not silently rewrite the source file. A reviewed change may then update dates or set `status: stale` explicitly.

A deprecated card also records a retirement outcome: `replaced`, `merged`, or `retired`. Replaced and merged outcomes name the target card, while retirement without replacement does not.

## Evidence

Evidence records should be stable references, not raw dumps. Useful categories include:

- schema or interface contract;
- implementation or model expression;
- observed output used for verification;
- explicit semantic decision.

When evidence conflicts, keep the conflict visible and require human resolution instead of silently selecting one side. A future consistency-card extension may formalize this only after its contract is defined.

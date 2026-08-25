# Architecture

## Five layers

| Layer | Owns | Must not own |
|---|---|---|
| Governance | schemas, status policy, templates, validation rules | domain facts |
| Source | minimum evidence needed to reproduce or review a claim | bulk dumps, live credentials, transient logs |
| Knowledge | canonical cards and typed relationships | generated indexes or runtime state |
| Build | deterministic indexes, compact capsules, relation projections | hand-authored truth |
| Runtime | routing, resolution, planning, answer assembly | source-of-truth edits |

The layers can live in one repository or separate packages, but their authority must stay explicit.

## Source and card separation

Source material answers “what evidence supports this claim?” A card answers “what stable knowledge should a reader or agent use?”

- Store only the smallest evidence snapshot that can reproduce or review the card.
- Normalize definitions, scope, caveats, and relationships into cards.
- Keep changing observations and transient failures out of canonical card bodies.
- Query live state at runtime when the answer depends on current values.

## Canonical ownership

Each concept, metric, or decision rule has one canonical card. Cross-domain semantic relationships use typed links:

- `depends_on`: this card requires another definition.
- `related`: useful navigation without ownership.
- `supersedes`: this card replaces an older contract.

An interface uses the top-level `canonical_cards` bridge to point to cards that own semantics. This bridge represents ownership, not definition dependency; a build may derive the reverse lookup for planning.

This prevents silent divergence between copied definitions.

## Build products

A deterministic compiler may derive:

- a manifest with one compact row per active card;
- domain capsules for broad navigation;
- full card records split into bounded files;
- bidirectional typed relations;
- status and answer policy;
- source and artifact hashes.

Build products are disposable. The source cards and their contracts remain authoritative.

Small files named `*.expected.jsonl` under an example's `evals/` directory are reviewed test fixtures for the build contract, not runtime build products. They may include expected source hashes so drift is visible. Actual generated manifests remain outside Git.

For these fixtures, `source_sha256` means SHA-256 over the source card's UTF-8 bytes with LF line endings, including its final newline. A build should normalize or reject other line endings before hashing.

## Runtime boundary

The repository should be usable without any production identity. Runtime adapters may provide search, data access, or messaging, but they must be injected from outside and operate under the caller's identity.

Credentials, identity mappings, sessions, user caches, outputs, and live configuration never belong in the knowledge repository.

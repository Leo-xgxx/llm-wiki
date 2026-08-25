# Architecture

## Five layers

| Layer | Owns | Must not own |
|---|---|---|
| Governance | schemas, status policy, templates, validation rules, the handbook contract | domain facts |
| Source | minimum evidence needed to reproduce or review a claim, with provenance | bulk dumps, live credentials, transient logs |
| Knowledge | canonical cards, interface cards, evidence bridges and typed relationships | generated indexes or runtime state |
| Build | deterministic manifest, compiled layers, domain capsules, relation projections | hand-authored truth |
| Runtime | routing, resolution, planning, live execution, answer assembly, gap registration | source-of-truth edits |

The layers can live in one repository or separate packages, but their authority must stay explicit. In practice the first three live in one Git repository, the build is a deterministic script over it, and the runtime consumes a release of the build.

## Domain layout

A domain is the unit of ownership, routing and review. Its layout is fixed so that tools and readers know where to start:

```text
<domain>/
  domain.yaml            identity, registry pointer, handbook pointer, boundaries, routing hints
  AGENTS.md              domain handbook: first-read hard rules; read before any card
  raw/                   managed evidence snapshots + source-contracts.yaml (the registry)
  wiki/<type>/*.md       cards, one directory per card type
  changelog/             one dated file per reviewed change
  retirements.jsonl      tombstones; append-only
  redirects.json         old ids -> current home
  evals/                 routing.jsonl, golden.jsonl, manifest.expected.jsonl
```

Two rules follow from the layout:

- The handbook is read before cards and overrides card prose. Anything that must hold for every answer in the domain goes there, not into ten cards.
- Runtime write areas (`proposals/`, `gaps/`, caches) live outside the domain tree and outside Git.

## Source and card separation

Source material answers "what evidence supports this claim?" A card answers "what stable knowledge should a reader or agent use?"

- Store only the smallest evidence snapshot that can reproduce or review the card, with a provenance header (see [evidence-and-raw.md](evidence-and-raw.md)).
- Normalize definitions, scope, caveats, and relationships into cards.
- Keep changing observations and transient failures out of canonical card bodies.
- Query live state at runtime when the answer depends on current values.

## Canonical ownership and three roles

Each concept, metric, value domain or decision rule has one canonical card. Cards carry one of three roles:

| Role | Owns | Points to |
|---|---|---|
| `canonical` | a definition, formula, value domain, procedure, trap or ruling | other canonical cards through typed relations |
| `interface` | the location and access shape of a dataset or view | canonical cards through `canonical_cards` |
| `evidence` | a managed snapshot and what was extracted from it | canonical cards through `index_to` |

Typed relations between canonical cards:

- `depends_on`: this card requires another definition to be understood.
- `related`: navigation without ownership or dependency.
- `supersedes`: this card replaces an older contract; the old card's `retirement.target_card` must point back.

`canonical_cards` and `index_to` are ownership bridges, not graph edges. A build derives their reverse lookups so a metric can discover its interfaces and its evidence without copying location details.

## Build products

A deterministic compiler derives, from source cards only:

- a manifest with one row per active card, including the compiled answer layer and the source hash;
- a compiled layer per card: `direct`, `guided` or `knowledge` (see [retrieval-and-evaluation.md](retrieval-and-evaluation.md));
- a brief per card, compiled from the first body section under a hard length limit;
- domain capsules: the handbook plus the briefs of that domain's cards, for cheap navigation;
- bidirectional typed relations and the reverse projections of the ownership bridges;
- status and answer policy after applying the freshness rule;
- source and artifact hashes.

Build products are disposable and never edited by hand. A clean checkout must rebuild them to identical hashes.

Build order matters when one product is the input of another. The reference order is: regenerate the retrieval index (aliases and briefs) → regenerate handbook projections → compile the build → package any distributed skill. Running a later step before an earlier one produces drift that looks like a content bug.

Small files named `*.expected.jsonl` under an example's `evals/` directory are reviewed fixtures for the build contract, not runtime build products. `source_sha256` means SHA-256 over the source card's UTF-8 bytes with LF line endings, including the final newline; a build normalizes or rejects other line endings before hashing.

## Consumption outlets

One card serves three outlets without being rewritten:

| Outlet | Reads | Notes |
|---|---|---|
| answering agent | compiled layers, capsules, contracts | never the raw layer by default |
| portal / browsing | the human-readable body | frontmatter rendered as metadata |
| command line / scripts | frontmatter and manifest | for lint, statistics and freshness runs |

If an outlet needs a different wording, the fix is a projection in the build, not a second copy of the card.

## Deployment forms

| Form | How the runtime gets knowledge | Freshness | Typical use |
|---|---|---|---|
| embedded | reads a clone of the repository at a pinned release | as fresh as the clone | a bot that lives next to the repository |
| distributed pack | receives the compiled capsules and layers as a package | pack carries its release hash and a validity window; a stale pack must say so | a skill shipped to many workstations |

Both forms are read-only consumers. A distributed pack that has passed its validity window answers with a staleness disclosure instead of pretending to be current.

## Runtime boundary

The repository is usable without any production identity. Runtime adapters may provide search, data access, or messaging, but they are injected from outside and operate under the caller's identity.

Credentials, identity mappings, sessions, user caches, outputs, and live configuration never belong in the knowledge repository. Runtime-written records such as gap files use role labels (`runtime`, `person`), never user identifiers.

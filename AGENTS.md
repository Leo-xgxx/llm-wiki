# Repository instructions

## Purpose

This repository records a generic LLM Wiki architecture: how to keep definitions as code, let machines do every verifiable step, and let the system repair its own gaps. It is a clean-room design notebook with a runnable example, not a source-code mirror or backup of any deployment.

## Hard boundaries

- Never copy files, code, prompts, tests, commit history, or generated artifacts from another repository. Re-derive generically.
- Never add real company names, product names, people, email addresses, user identifiers, repository paths, private hosts, document tokens, asset ids, table names, query results, or credentials.
- All examples are synthetic and use the `acme` namespace. Owners are roles, never names.
- Runtime state, sessions, caches, logs, outputs, proposals, gap files and secrets stay outside Git.
- Generated artifacts stay outside Git. The only reviewed exceptions are the `*.expected.jsonl` fixtures under `examples/**/evals/`, regenerated through `tools/validate.py --write-manifest`.

## Pre-push scan

Before every push, scan the tree for four classes of leakage and stop on any hit: organization and people identifiers; asset identifiers (numeric ids, table names, tokens); internal hosts, paths and URLs; real figures or definitions. The example domain must read as fiction to someone who has never seen a real deployment.

## Knowledge rules

- A card owns a stable definition, value domain, procedure, trap, ruling, location or evidence bridge. It is not shaped around one incident or one question.
- Each fact has one canonical home. Other cards link to it rather than copying it.
- No bridge, no card: content that plays no role in answering goes into the handbook or the changelog, not into a card.
- Separate machine-verifiable evidence from human semantic decisions; separate data facts, view framing and requester phrasing.
- Interface cards are thin. They locate an asset and point to canonical knowledge.
- Record uncertainty explicitly through status, evidence, freshness and disclosure; never resolve it by picking a side in prose.
- Structure before body: contract, handbook, bridges and evals change before prose.
- Aliases are concrete noun surfaces; shared aliases are held by a consistency card.

## Change discipline

- Update schema, templates, validator, example cards and documentation together when a contract changes.
- Every routing rule has synthetic positive and negative examples; every arbitration and boundary has a golden question.
- Automate only checks with objective pass/fail criteria. Semantic decisions remain manual.
- Deleting a card removes active references, marks it deprecated with a retirement block, appends a tombstone, and adds a redirect.
- Do not stack mechanisms: remove one before adding one; a single incident does not justify a gate.
- Run `python3 tools/validate.py examples/acme-analytics` before opening a change; it must report zero errors.

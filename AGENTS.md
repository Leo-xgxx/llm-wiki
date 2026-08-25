# Repository instructions

## Purpose

This repository records a generic LLM Wiki architecture. It is a clean-room design notebook, not a source-code mirror or backup.

## Hard boundaries

- Never copy files, code, prompts, tests, commit history, or generated artifacts from another repository.
- Never add real company names, people, email addresses, user identifiers, repository paths, private hosts, document tokens, asset IDs, table names, query results, or credentials.
- All examples must be synthetic and use the `acme` namespace.
- Runtime state, sessions, caches, logs, outputs, and secrets stay outside Git.
- Keep generated runtime artifacts out of Git. Small synthetic `*.expected.jsonl` files may be reviewed as explicit build-contract fixtures.

## Knowledge rules

- A card owns a stable definition, scope, formula, decision rule, or interface boundary. It must not be shaped around one incident or one question.
- Each fact has one canonical home. Other domains link to it rather than copying it.
- Separate machine-verifiable evidence from human semantic decisions.
- Keep interface cards thin. They locate an asset and point to canonical knowledge; they do not duplicate business definitions.
- Record uncertainty explicitly through status, evidence, and freshness fields.

## Change discipline

- Update schema, templates, example cards, and documentation together when their contract changes.
- Use synthetic positive and negative retrieval examples for every routing rule.
- Automate only checks with objective pass/fail criteria. Semantic decisions remain manual.
- Deleting a card requires removing active references and preserving a permanent tombstone that records whether it was replaced, merged, or retired.

# Governance

## Machine and human responsibilities

Machines are well suited to objective checks: required fields, schema compatibility, hashes, link integrity, duplicate IDs, freshness dates, and deterministic builds.

Humans remain responsible for semantic ownership, intended definitions, acceptable caveats, conflict resolution, and changes that affect policy.

Automate a bulk transformation only when correctness has a machine-checkable criterion. Otherwise surface the debt and review cards individually.

## Source discipline

Keep only minimum sufficient evidence. Never commit:

- live credentials or identity mappings;
- row-level production data;
- complete machine dumps that can be queried on demand;
- transient failures and debug output;
- expiring or signed download URLs;
- duplicate copies of the same source;
- generated runtime artifacts.

## Change review

A meaningful change should state:

- which canonical contract changed;
- what evidence supports it;
- which dependent cards and routes are affected;
- whether ranking or execution behavior changed;
- how to roll back or retire the old contract.

## Generated artifacts

Generated runtime files stay outside Git and are never edited directly. A clean checkout should be able to rebuild them from source cards and produce identical hashes. Drift means either the source, compiler, or committed policy is inconsistent.

A synthetic `*.expected.jsonl` file under `examples/**/evals/` is a reviewed expectation for the build contract, not a generated runtime artifact. It must be clearly named, contain no production content, and be updated when its source-card hash changes.

## Runtime isolation

The runtime consumes immutable releases and remains read-only. It may cache generated artifacts outside the repository, but it must not write semantic changes back without a separately reviewed contribution path.

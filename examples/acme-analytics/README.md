# Acme Analytics example

A synthetic domain that exercises every contract in this repository without representing any real organization or data source.

## What it contains

| Path | What it demonstrates |
|---|---|
| `domain.yaml` | domain descriptor: registry, handbook, boundaries, routing hints |
| `AGENTS.md` | domain handbook, read before any card; hard rules and boundaries |
| `raw/source-contracts.yaml` | machine-readable source registry with provenance; document snapshots bind a domain-relative artifact path and SHA-256; every `source_refs` and `evidence.ref` resolves here |
| `raw/snapshots/` | managed synthetic document artifacts whose bytes are bound by the registry |
| `wiki/metrics/` | two canonical metrics that share a word, plus one deprecated metric with a retirement block |
| `wiki/datasets/`, `wiki/dashboards/` | thin interface cards; the dashboard carries a by-layer framing filter |
| `wiki/dimensions/` | a value-domain card whose values come from a registry contract |
| `wiki/concepts/` | a concept card that two metrics depend on |
| `wiki/playbooks/` | an executable procedure that names the cards and interface it uses |
| `wiki/traps/` | a known failure pattern with a detection rule |
| `wiki/consistency/` | the arbitration card that holds the shared alias `revenue` |
| `wiki/sources/` | the evidence bridge from a managed snapshot to the cards it supports |
| `retirements.jsonl` | tombstones: one for a card already deleted, one for the deprecated card still in the tree |
| `redirects.json` | old ids pointing at their current home |
| `changelog/` | one dated change record in the review format |
| `evals/routing.jsonl` | non-empty routing contract fixture with negatives, cutoff and execution readiness; ranking is run by a separate harness |
| `evals/golden.jsonl` | non-empty answer contract fixture with ground-truth provenance, including refusal and trap questions; scoring is run separately |
| `evals/manifest.expected.jsonl` | reviewed build fixture with source hashes and compiled layers |
| `gaps.example.jsonl` | two reviewed, fully synthetic gap records: a coverage gap from a fictional runtime and a wrong-answer lead from a fictional person; this fixture is the explicit exception to keeping operational gaps outside Git |

## Validate

```bash
python3 -m unittest -v
python3 tools/validate.py examples/acme-analytics --as-of 2026-08-26
python3 tools/validate.py examples/acme-analytics --as-of 2026-08-26 --write-manifest   # after a reviewed change
```

`evals/manifest.expected.jsonl` is hand-reviewed test data for the build contract. The fixed `--as-of 2026-08-26` matches the integration-test fixture, so effective freshness and the expected manifest do not change with the wall clock. It is regenerated only through `--write-manifest` and the diff is part of the review. A release check also validates against the actual release date.

The reference validator checks schemas, cross-record references (including redirects used by eval and gap records), and the expected manifest. It does not execute retrieval, ranking, the fictional adapter, or golden-answer scoring. `--write-manifest` runs only after all validation errors are cleared and atomically replaces a safe target; otherwise the existing fixture is unchanged.

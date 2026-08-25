# Acme Analytics example

A synthetic domain that exercises every contract in this repository without representing any real organization or data source.

## What it contains

| Path | What it demonstrates |
|---|---|
| `domain.yaml` | domain descriptor: registry, handbook, boundaries, routing hints |
| `AGENTS.md` | domain handbook, read before any card; hard rules and boundaries |
| `raw/source-contracts.yaml` | machine-readable source registry with provenance; every `source_refs` and `evidence.ref` resolves here |
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
| `evals/routing.jsonl` | ranking expectations with negatives, cutoff and execution readiness |
| `evals/golden.jsonl` | end-to-end answer expectations with ground-truth provenance, including refusal and trap questions |
| `evals/manifest.expected.jsonl` | reviewed build fixture with source hashes and compiled layers |
| `gaps.example.jsonl` | two gap records: a coverage gap from the runtime and a wrong-answer lead from a person |

## Validate

```bash
python3 tools/validate.py examples/acme-analytics
python3 tools/validate.py examples/acme-analytics --write-manifest   # after a reviewed change
```

`evals/manifest.expected.jsonl` is hand-reviewed test data for the build contract. It is regenerated only through `--write-manifest` and the diff is part of the review.

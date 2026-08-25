# Implementation status

What in this design has been run in earnest, what has only been designed, and what was tried and removed. As of 2026-08. Update this table when the answer changes; a design document that does not say which parts are theory misleads its own author six months later.

| Area | Element | Status |
|---|---|---|
| card model | nine card types with per-type blocks | **in use** (a deployment carries more types; the nine here are the ones that earned a contract) |
| card model | execution contract (`always_filter`, `by_layer`, `time_default`) | **in use** |
| card model | consistency cards as alias arbiters; build error without one | **in use** |
| card model | brief compiled from the first section with a hard limit | **in use** |
| card model | `stale` runner-only; certification as re-verification obligation | **in use** |
| evidence | registry with provenance; KEEP/DELETE; source cards | **in use**; a second clean-up pass of process artefacts was still pending |
| build | deterministic manifest with hashes; fixed build order; artifacts outside Git | **in use** |
| build | three compiled layers and domain capsules | **in use** |
| build | distributed pack with validity window | **in use** |
| gates | frontmatter lint, cross-record validation, routing evals, rank regression, runtime impact, review three questions, freshness runner | **in use** |
| gates | golden questions with the full taxonomy | **in use**; the log-sourced share was still small |
| runtime | trust the model / feed facts / fail closed; salvage removed | **in use** |
| runtime | gap registration contract (schema version 2) | **designed**; version 1 in use, version 2 the target |
| runtime | conversation-side lead registration replacing the distillation pipeline | **designed, not built**; the old pipeline still ran |
| intake | two input chains; seven probe questions; proposals area | **in use** |
| mining | nine-step domain mining; source-type tactics | **in use** for several domains |
| loop | three-way eligibility; ticket lifecycle; six roles | **in use** |
| loop | three locks; machine-readable verdicts; merge as a separate step | **in use** |
| loop | failure-driven warden with shell fallback; absence check | **in use** |
| loop | queue-driven draining without caps | **in use** |
| observability | traces, gap records, eval results, usage statistics; operations and team views | **in use** |
| observability | drift patrol, usage audit, asset discovery detectors | **in use** |
| removed | per-query contract gate | **built, then removed** |
| removed | pre-routing modules, scope locks, salvage | **built, then removed** |
| removed | throughput caps and time budgets in the loop | **built, then removed** |
| this repository | reference validator (`tools/validate.py`) | **runs on the example**; not a production build |
| this repository | licence | **not chosen** |

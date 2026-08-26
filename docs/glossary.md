# Glossary

| Term | Meaning |
|---|---|
| alias | a concrete noun surface that routes a question to a card; never question phrasing |
| arbitration | the ruling recorded on a consistency card for a term two cards share |
| brief | the compiled first body section of a card, under a hard 900-character limit; overflow rejects the build; the only body text retrieval scores |
| canonical | the role of a card that owns a definition, value domain, procedure, trap or ruling |
| capsule | a domain's handbook plus the briefs of its cards; read whole for navigation |
| certified | status meaning evidence and semantics are accepted; a signed obligation to re-verify before `review_after` |
| consistency card | the card that holds a shared term and rules which party answers it |
| direct / guided / knowledge | the three compiled layers; `direct` requires one active available interface to expose the complete required field set |
| domain | the unit of ownership, routing and review; a directory with a handbook, registry, cards, evals |
| eligibility | the three-way condition under which a gap becomes a ticket |
| evidence | dated review acts against registry contracts; also the role of a source card |
| execution contract | the machine-executed constraints on a metric, dataset or dashboard card |
| fail closed | unresolved states stay visible; the runtime never converts them into a plausible answer |
| framing | a view's own restriction on what it shows; kept in `by_layer`, never in the definition |
| fixture_as_of | reproducible validation date declared by a domain fixture; overridden by CLI `--as-of`, and used before falling back to today |
| freshness runner | the only component that derives effective `stale` when `review_after <= as_of`; it never rewrites the card-file status |
| gap | a lead registered by the runtime or a person; never a card by itself |
| gate | a pass/fail condition on a change; several gates are never collapsed into one |
| golden question | an end-to-end answer expectation with ground-truth provenance |
| handbook | a domain's `AGENTS.md`: first-read hard rules that override card prose |
| interface | the role of a dataset or dashboard card; locates an asset and bridges to canonical cards |
| layer | see direct / guided / knowledge; also `stable` / `volatile` for eval records |
| manifest | one row per active card in a build, with layer and source hash |
| needs-decision | status meaning the technical evidence is sufficient but an owner must decide the meaning |
| owner role | the role that makes semantic decisions for a domain; a label, not a person, in this repository |
| provenance | required origin, capture date, state at capture and trust level of every source-registry contract |
| proposals | the runtime-writable area where drafts wait for confirmation; outside the canonical tree |
| ranking budget | the observation that every scored surface competes for the same top positions |
| redirect | a mapping from a retired or renamed id to its current home; evals, gap records and external links may retain the old id |
| registry | `raw/source-contracts.yaml`; every evidence reference resolves here |
| required fields | execution inputs not mechanically visible in a formula or filter, such as time, grouping, and slice fields |
| retirement | the block on a deprecated card: outcome, reason, date, target |
| ruling | the content of an arbitration |
| source card | the evidence bridge from a managed snapshot to the cards it supports |
| stale | runner-derived effective status when the review window expired; disclosed, never written into a card file |
| structure before body | the edit order: contract, handbook, bridges, evals, then prose |
| three locks | eligibility script, machine-readable verdict for the revision, pinned revision under a lock |
| tombstone | an append-only record of a retired card in `retirements.jsonl` |
| trap | a card describing a known way to get a wrong result, with a detection rule |
| value domain | the sourced list of a field's values and their meanings |
| warden | the failure-driven supervisor of scheduled machine roles |
| watermark | the first-line hash plus processed-line count a watcher uses to read new gap records |

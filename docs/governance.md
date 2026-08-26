# Governance

## Machine and human responsibilities

Machines are well suited to objective checks: required fields, schema compatibility, hashes, link integrity, duplicate ids, freshness dates, deterministic builds, rank comparisons, and the execution of contracts.

Humans remain responsible for semantic ownership, intended definitions, acceptable caveats, conflict resolution, and changes that affect policy.

The boundary is stated as a meta-rule: **no bulk transformation without a machine-checkable criterion.** If correctness of a change to many cards cannot be decided by a script, the change is done card by card with review, or surfaced as debt. Feeding the machine facts (a value list, a registry contract) is not a mechanism and needs no such criterion.

## Meta-rules

These rules override any specific procedure in this repository when they conflict.

1. **Structure before body.** Contract, handbook, bridges and evals change before prose. A prose-only change to a definition is incomplete.
2. **Delete over annotate.** The first option for stale, duplicate or wrong content is deletion with the reference repointed to the source of truth. A disambiguating note is interest paid on a debt.
3. **Do not stack mechanisms.** A one-off incident does not justify a new gate. Before adding a mechanism, remove one; prefer the smallest loop that closes.
4. **Throughput is limited only by correctness gates and owner decisions.** No daily quotas, no fixed-hour windows, no per-run count caps. If work is waiting and its gates pass, it proceeds.
5. **Evidence over deference.** A challenge is answered by checking the record, not by agreeing. An old conclusion is re-examined by asking whether its premises still hold.
6. **Define the method, not the phrasing.** Cards describe how something is computed; the requester's words stay in the gap record.
7. **Plain language.** Mechanisms are named by what they do. Metaphors and in-group jargon are rewritten.

## Source discipline

Keep only minimum sufficient evidence with provenance. The KEEP/DELETE rule, the provenance header and the list of things that never enter the repository are in [evidence-and-raw.md](evidence-and-raw.md).

## Official maintenance areas and owners

| Area | Who reviews |
|---|---|
| `schemas/`, `templates/`, validator rules | governance owner role |
| a domain's handbook, consistency cards, execution contracts | that domain's owner role |
| a domain's other cards | any reviewer, with the owner role for certification |
| build and release scripts | build owner role |

A change that touches an official area is routed to its owner role automatically (an `OWNERS` pattern file is the usual mechanism). Owners are roles, not names, in this repository.

## Who may set which status

| Status | Set by |
|---|---|
| `draft`, `review`, `needs-decision` | authors and machines |
| `certified` | the certification gate: evidence rule satisfied, maintainer role named, reviewed |
| `deprecated` | a reviewed change with a retirement block and a tombstone |
| effective `stale` | the freshness runner only, when `review_after <= as_of`; never written as a card-file status |

Certification is a signed obligation: the maintainer role commits to re-verification before `review_after`. That date is the first expired day, so `review_after <= as_of` makes the freshness runner derive effective `stale`. A repository-wide review window (for example sixty to one hundred and eighty days) is set in governance, and the runner enforces it.

The validation `as_of` date is also a reproducibility boundary: provenance captures, arbitration rulings, retirements, deletions, redirect start dates, measured golden answers, and gap registrations cannot come from its future. It resolves in this order: an explicit CLI `--as-of` override, the domain's `fixture_as_of`, then today. Fixture runs use the declared date; releases must explicitly pass their actual release date.

Derived staleness does not rewrite the card, and card files never set `status: stale`. A person who finds unresolved uncertainty uses `needs-decision`; a reviewed change that confirms invalidity uses `deprecated` with the retirement records. Re-verification clears derived staleness by updating evidence and freshness dates.

## Change review

A meaningful change states which canonical contract changed, what evidence supports it, which dependent cards and routes are affected, whether ranking or execution behaviour changed, and how to roll back. Reviews grade findings by **impact × realistic probability**, and every finding above the lowest grade names a concrete trigger scenario; "could theoretically" is not a grade.

Merging is always a separate step from reviewing: read the full review, confirm the counts of findings per grade against the reviewed revision, then merge. A merge that skips this step is how a known finding ships.

## Generated artifacts

Generated runtime files stay outside Git and are never edited directly. A clean checkout rebuilds them from source cards to identical hashes. Drift means the source, the compiler or the committed policy is inconsistent.

Two generated exceptions are allowed to live in Git, both reviewed: the domain's id index (because ids are the source of truth for references) and the small `*.expected.jsonl` fixtures under `examples/**/evals/`. Separately, `examples/**/gaps.example.jsonl` may be tracked as fully synthetic schema and cross-reference test data; operational gap files remain outside Git.

## Runtime isolation

The runtime consumes immutable releases and remains read-only. It may cache generated artifacts outside the repository, and it writes gap records and proposals into runtime areas, but it never writes semantic changes into the canonical tree without the reviewed contribution path.

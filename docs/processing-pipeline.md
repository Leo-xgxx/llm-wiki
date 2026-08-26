# Processing pipeline

The pipeline turns a request into a reviewed change and, later, into a retirement. Each step has a machine part and a human part; the split is stated explicitly so that neither side does the other's job.

## 1. Intake

Capture the request and classify it before touching any card:

| Classification | What it is | Where it goes |
|---|---|---|
| new knowledge | a definition, value domain, procedure or ruling that no card owns | a proposal draft, then a card |
| correction | a canonical card says something wrong | a card change with evidence |
| routing gap | the card exists but was not retrieved | alias or handbook change plus a negative test |
| template failure | the card exists and was retrieved, the compiled artifact failed | build fix, not a content change |
| transient incident | a temporary failure of a source or adapter | a runtime record; never a card |
| lead | someone said something plausible and unverified | a gap record with `narrated` confidence |

A question being asked is not a reason to create a card. The full intake and mining method, including the inclusion criteria and the seven probe questions, is in [intake-and-mining.md](intake-and-mining.md).

## 2. Evidence collection

Collect the smallest stable evidence needed to verify the proposed knowledge, register it in the domain's source registry with complete provenance for every contract kind, and store the managed snapshot under `raw/`. Exclude row dumps, full dependency graphs, temporary errors, signed URLs, sessions, and credentials. See [evidence-and-raw.md](evidence-and-raw.md).

## 3. Normalization

Choose one canonical owner and one card type. Extract:

- definition and formula over logical fields;
- grain and time semantics;
- inclusion and exclusion rules, written into the execution contract;
- time-axis, grouping, and slicing fields that cannot be inferred from the formula or filters, written into `execution_contract.required_fields`;
- dimensions and value-domain handling;
- ambiguity boundaries; if a term is shared, the consistency card is part of the same change;
- typed relations and evidence references.

Separate three kinds of statements before writing: **data facts** (a field's value domain, whether something can be computed), **view framing** (a chart's filter list, a report's exclusions) and **the requester's phrasing** (their ad-hoc groupings, their words). Only the first two enter a card, each labelled as what it is. The third stays in the gap record.

## 4. Structural validation

Two levels, run in this order:

1. **Frontmatter lint** on the changed files: required fields, enums, id format, dates. Fast, local, runs before every push.
2. **Cross-record validation** on the whole domain: reference existence, complete registry provenance and snapshot artifact hashes, supersedes reciprocity through live retirements or tombstones, redirects, alias arbitration, formula and execution-field coverage by one single active bridging interface, interface-local field exposure, freshness, brief length, required non-empty eval fixtures, and manifest determinism. Availability is an additional condition for compiling that complete bridge as `direct`; an unavailable complete bridge remains valid but `guided`. Evaluation and gap references may use a retired id only when the redirect resolves to a current active card.

Reject changes with missing required fields, duplicate ids, invalid statuses, broken links, conflicting ownership, shared aliases without an arbiter, or active references to retired cards.

`tools/validate.py` implements these structural, reference, and fixture checks for the synthetic example. It does not run the retriever, measure rank, execute an adapter, or score a generated answer; those are the separate gates in steps 6 and 7.

## 5. Deterministic build

Compile source cards into immutable runtime artifacts in the fixed build order (index → handbook projections → build → distributed pack). Store source and artifact hashes so the runtime can prove that its indexes and cards belong to the same release.

The manifest contract includes at least the card id, source path, type, title, lifecycle state, knowledge role, compiled layer, effective status after freshness and source-content hash. Checked-in example manifests are named as expected-output fixtures; production manifests are generated outside Git. Updating reviewed expected-output fixtures is opt-in. Validation errors prevent every requested update. Targets are then updated independently in order; a failed target keeps its prior fixture and stops later updates.

## 6. Ranking and runtime impact check

A content change can be semantically correct and still push a neighbouring card below the runtime cutoff, or change which layer a card compiles to. Before merge, compare base and candidate:

- routing evals at the runtime cutoff, positives and negatives;
- rank position and margin of every expected card, not only pass/fail;
- compiled layer of every card in the domain.

A card that silently moved from `guided` to `direct`, or an expected card that fell from rank 3 to rank 7 while still inside the cutoff, is a finding even when every eval is green.

## 7. Retrieval

Use a staged process at runtime:

```text
question
  -> normalize into a task (subject, requested action, time window)
  -> read the domain handbook
  -> route by subject and action
  -> resolve canonical candidates and one-hop relations
  -> decide whether execution is possible
  -> assemble the answer with evidence and disclosure policy
```

Details in [answering-runtime.md](answering-runtime.md).

## 8. Feedback

Classify failures before changing content:

- missing knowledge: add or extend a canonical card, through intake;
- bad ranking: change aliases, handbook or routing hints and add negative tests;
- wrong definition: update the canonical card with evidence, structure first;
- unavailable live data: fix the adapter or disclose the limitation;
- temporary incident: record it outside the canonical card body.

Failures arrive as gap records; the loop that turns them into tickets and changes is in [self-maintenance-loop.md](self-maintenance-loop.md).

## 9. Retirement

Deleting a card is a graph operation, not a file deletion:

1. Remove active inbound references (`depends_on`, `canonical_cards`, `index_to`, arbitration parties). `supersedes` references are the permanent exception: they are how the replacement points back to a retired id.
2. Mark the card `deprecated` with a `retirement` block: outcome, reason, date, and the target card for `replaced` and `merged`.
3. Append a tombstone to the domain's `retirements.jsonl`: original id, outcome, optional target, reason, retirement date, final source hash. Record that hash from the source card before deletion; after the source is gone the tombstone preserves it, but the repository cannot recompute it from a deleted file.
4. Add a redirect from the old id to its current home so evals, gap records and external links keep resolving. The replacement keeps the old id in `supersedes`; validation requires the live retirement block or deleted card's tombstone to target that replacement. Other active card relations and ownership bridges use the current id.
5. Delete the file in a later change and stamp `deleted_on` on the tombstone.

The build validates tombstone targets and retains tombstones after deletion, so deletion does not erase the audit trail.

## Change review checklist

A meaningful change states:

- which canonical contract changed;
- what evidence supports it;
- which dependent cards, handbook rules and routes are affected;
- whether ranking, compiled layer or execution behaviour changed;
- how to roll back or retire the old contract.

The changelog entry template in `templates/changelog-entry.md` has exactly these five headings.

# Answering runtime

The runtime consumes an immutable release of the build and answers questions. Its design principle, after a period of trying the opposite, is **trust the model, feed it hard facts, fail closed**: no pre-routing modules that decide for the model, no scope locks, no salvage layers that turn a failure into a plausible answer. The model gets the handbook, the capsule, the contracts and the live results, and every state it cannot resolve stays visible.

## Session model

- One conversation is one engine session; context is not shared across conversations or users.
- Precedence when the question is underspecified: the question text > what it refers back to in this conversation > the page or report defaults > the domain defaults.
- Messages written by the bot itself are context, never a new request.

## From question to task

1. Normalize the question into a task: subject, requested action (define, locate, compute, compare, explain a difference, check freshness, inventory), time window, slices.
2. Read the domain handbook; apply boundary overrides.
3. Route and resolve (see [retrieval-and-evaluation.md](retrieval-and-evaluation.md)); load context according to the compiled layer.
4. Decide executability: is there a `direct` card backed by one active, available interface that exposes all required fields, a `guided` card, or only knowledge?
5. Execute or explain; assemble the answer with disclosures.
6. If no certified knowledge answered, register a gap.

## Live execution rules

- The execution contract is executed literally: `required_fields` declares non-formula inputs, `always_filter` applies on every run, `by_layer` filters apply only when the question names that view, and `time_default` applies when no window is given. Prose is not consulted for fields or filters.
- Name catalogues resolve exactly: one match is used, several are listed back, zero is an error. Short codes never match by substring.
- No result is an error the user can retry, not a value. Salvaging a partial or cached value into an answer is forbidden.
- Empty output is reported as "empty, filtered or unavailable — established: <which>", never as zero.
- Nothing is computed through an interface the card does not declare. One active, available interface must expose the full field set by itself; fields from separate interfaces are not silently combined. Guessing a dataset, a join key or a filter to make a question executable is the failure mode the whole system exists to prevent.

## Time windows

- Default window and grain come from the card's `time_default`, else from the handbook, else the runtime's global default; the answer states which was used.
- "Latest" means the most recent complete period as defined by the interface's refresh contract, and the answer says which date that was.
- Questions that mix date axes (creation versus recognition) are `ask-back`, not best-effort.

## Disclosure, degradation, refusal

| State | Behaviour |
|---|---|
| certified card, adapter available | answer; cite the card's title; state window and unit |
| certified card, adapter unavailable | give the procedure and the interface name; say execution is unavailable |
| non-certified card is the best match | answer from it and say its state; status is a disclosure signal, not a permission |
| effective status stale | answer and disclose the expired review window |
| consistency card matched | apply the ruling; disclose what the bare term was taken to mean |
| `needs-decision` | state the open decision and who must decide; do not pick a side |
| topic outside all domain boundaries | refuse with the owning domain if known |
| question needs a clarification the handbook cannot supply | ask back; one question, with the options |

Internal identifiers (card ids, contract ids, adapter names) stay internal unless the reader is a maintainer; the reader sees titles and plain wording.

## Identity, safety, cost

- Adapters run under the caller's identity, injected by the host; the runtime holds no credentials of its own.
- Background or scheduled work runs only under a declared owner and never reads another user's session records; shared records read by scheduled jobs carry an ownership anchor.
- Batch requests are split per requester; a bot's own message never starts a batch.
- Cost is bounded by the layer design (capsules before full cards, full cards before live queries), not by a query counter that cuts an answer short.

## Gap registration

Whenever the answer did not come from certified knowledge — no card, wrong card, ranking miss, template failure, adapter unavailable — the runtime appends a gap record ([gap.schema.json](../schemas/gap.schema.json)) in an operational store outside Git:

- `answered` is mandatory so that "answered wrongly" and "could not answer" are never merged;
- `kind` distinguishes coverage gap from template failure; the two are mutually exclusive;
- `searched` is non-empty and lists which surfaces were tried and what they returned, so a ranking miss is distinguishable from missing knowledge;
- `claims` carry the confidence level; every `verified_live` claim names authoritative technical registry evidence captured in `live` state no later than the gap, while `narrated` claims become leads and may become tickets only through the three-way eligibility gate in [self-maintenance-loop.md](self-maintenance-loop.md); they never produce a card;
- the requester is not in the record; the host keeps that mapping if it needs it.

A person can also register a lead ("I heard that X is computed as Y") through the same record with `registered_by: person`. Registering is deliberately cheap and deliberately never produces a card by itself; the loop in [self-maintenance-loop.md](self-maintenance-loop.md) decides what happens next.

The tracked `examples/**/gaps.example.jsonl` file is reviewed synthetic contract data only. It is not a runtime sink and is never appended to by an answering process.

## Output form

Plain text by default. Cards, buttons and rich blocks are opt-in per host. The answer carries: the statement, the definition applied (by title), the window and unit, and any disclosure from the table above. It does not carry ids, hashes or evidence lists unless asked by a maintainer.

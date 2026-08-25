# Retrieval and evaluation

## Route, resolve, plan

Treat retrieval as three contracts:

1. **Route** identifies the subject, domain, and requested action.
2. **Resolve** ranks canonical cards and expands only relevant typed neighbors.
3. **Plan** decides whether the selected knowledge supports explanation only or an executable action.

A high text-similarity score is not proof that a card owns the answer.

## Ranking safety

Every important route should include:

- a positive query that should retrieve the canonical card;
- paraphrases that exercise different wording;
- a near-neighbor negative query using similar terms but a different subject;
- a rank contract such as canonical top-1 or expected top-k;
- an execution expectation when a query interface is required.

An evaluation record should make that expectation explicit. Useful generic modes are `knowledge-only`, `interface-locate`, and `executable-if-available`; the last mode also names the required interface cards. Runtime availability is still checked live rather than inferred from retrieval success.

The minimal record contains `id`, `question`, `paraphrases`, `expected_cards`, `max_rank`, `execution_expectation`, and `negative_queries`. `required_interfaces` is mandatory for `executable-if-available`. A negative passes only when none of the positive `expected_cards` appears inside the configured retrieval cutoff; the evaluator records that cutoff alongside its result.

Evaluate base and candidate versions side by side. A content edit can be semantically correct while still pushing the canonical card below the runtime cutoff.

## Separate gates

| Gate | Question |
|---|---|
| Schema | Is every card structurally valid? |
| Graph | Are IDs unique and typed links resolvable? |
| Build | Are generated artifacts deterministic and complete? |
| Retrieval | Do positive, paraphrase, and negative queries rank correctly? |
| Planning | Is execution readiness reported accurately? |
| Answer | Does the final response use the right definition and caveat? |
| Freshness | Is the evidence still within its review window? |

Do not collapse these into one pass/fail signal.

## Fail closed

Unknown scope, missing evidence, unresolved semantics, stale sources, and unavailable execution interfaces must remain visible states. Empty output is not proof of zero, and failed retrieval is not proof that the knowledge does not exist.

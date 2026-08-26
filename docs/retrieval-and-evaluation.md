# Retrieval and evaluation

## Route, resolve, plan

Treat retrieval as three contracts:

1. **Route** identifies the subject, domain, and requested action. The domain handbook and its boundaries are read first; a topic listed under boundaries is routed to its owning domain before any scoring.
2. **Resolve** ranks canonical cards and expands only relevant typed neighbours (one hop of `depends_on`, the arbitration parties of a consistency card, the interfaces bridging to a metric).
3. **Plan** decides whether the selected knowledge supports explanation only or an executable action.

A high text-similarity score is not proof that a card owns the answer. A consistency card that holds the bare term is the correct top result for an unqualified question even when a metric scores higher on words.

## Three compiled layers

Every active card compiles to exactly one layer. The layer decides how much context the runtime loads:

| Layer | Meaning | Default context |
|---|---|---|
| `direct` | a metric whose formula, required, and filter fields are all exposed by one active bridging interface whose `availability.status` is exactly `available` | compact execution metadata; the full card is not read |
| `guided` | an interface exists or a procedure is declared, but execution is not safe without reading the card | the full card |
| `knowledge` | definition, value domain, ruling, trap, concept or evidence; nothing to execute | the full card |

The layer is derived by the build, never hand-set. Fields from several partial interfaces are never unioned to manufacture `direct`. It must not be improved by adding guessed interfaces, guessed join keys, or lowered evidence requirements; a domain with few `direct` cards is an honest domain.

## Capsules and the handbook

For navigation the runtime reads a **domain capsule**: the handbook plus the briefs of that domain's cards. A capsule is small enough to read whole. It answers "which card, if any" cheaply before the full card is loaded.

The handbook is read before the capsule's cards and overrides them. Hard rules that must hold for every answer in a domain belong there.

## Fallback ladder

When the first route does not produce a confident candidate, the runtime descends a fixed ladder and records which rung answered:

1. handbook boundary override (the topic is explicitly assigned elsewhere);
2. term rewrite through aliases and the redirect table; old ids retained by evals, gap records, or external links resolve to their current active target here;
3. asset index ("where do I look" questions match interface cards by name);
4. full-text retrieval over briefs at the runtime cutoff;
5. domain capsule read;
6. whole-repository lookup as the last resort.

Rung 6 is a diagnostic surface. An answer that needed it is a routing gap and produces a gap record even when the answer was right.

## Ranking is a shared budget

Every scored surface (title, aliases, summary, brief) competes with every other card's surfaces for the same top positions. Rules that follow:

- **Aliases are concrete noun surfaces.** Question phrasing, generic verbs and time words inside an alias match unrelated questions; a single bad alias can push another domain's expected card below the cutoff.
- **The brief stays inside its limit and inside its domain.** An overflow rejects the build. Examples, enumerations and other domains' product names are placed in non-scored sections.
- **Rare terms are the lever, not length.** A short brief containing one rare cross-word fragment pulls harder than a long plain one. When a change displaces a neighbour, find the two or three rare terms that overlap the neighbour's question and rephrase them; do not shorten blindly.
- **Reproduce at the runtime cutoff.** A ranking miss reproduced with a tool's default cutoff shows a different picture from the one the runtime sees.
- **Shared surfaces need an arbiter.** Two active cards holding the same alias is a build error, full stop. The resolution is a consistency card that holds the alias, lists both cards as parties, and rules which one answers the bare term.

## Ranking safety records

Every important route has a record in `evals/routing.jsonl`. A complete domain keeps both `evals/routing.jsonl` and `evals/golden.jsonl` present and non-empty:

- a positive query that should retrieve the canonical card;
- paraphrases that exercise different wording;
- a near-neighbour negative query using similar terms but a different subject;
- a rank contract (`max_rank`) and the runtime `cutoff`, with `len(expected_cards) <= max_rank <= cutoff`; `expected_cards` is an all-of set, not a list of alternatives;
- an execution expectation: `knowledge-only`, `interface-locate`, `executable-if-available`, or `ask-back` for questions that must not be answered without clarification. An executable record names at least one metric in `expected_cards`; its `required_interfaces` collectively bridge every expected metric, and every listed interface bridges at least one of them.

A negative passes only when none of the positive `expected_cards` appears inside the cutoff. Every record declares `cutoff`, `layer` (`stable` or `volatile`), and `status` (`active`, `quarantine`, `deprecated`) so that the runtime contract is reproducible and a record depending on moving data can be quarantined without blocking a release.

Positive questions and paraphrases must not duplicate a negative query after case and whitespace normalization. Redirected ids are accepted for migration, but two ids in one field may not resolve to the same active card. `required_interfaces` is present only on `executable-if-available`; each expected metric has an execution contract and at least one listed interface that exposes its complete formula, required, and filter field set.

The reference validator schema-checks these records and resolves their card ids, including old ids through redirects. It does not issue queries or assert that the expected card actually ranked within `max_rank`; a retrieval harness must run that gate at the declared cutoff.

## Rank regression and runtime impact

Evaluate base and candidate side by side, and look at more than pass/fail:

- rank and score margin of every expected card, before and after;
- compiled layer of every card, before and after;
- the set of cards that entered or left the cutoff for every eval question.

"All green" proves the assertions in the eval file; it does not prove that a card did not move from rank 3 to rank 7, or that an interface card did not silently become `direct` and start receiving execution traffic. Those are gate findings in their own right.

## Separate gates

| Gate | Question |
|---|---|
| Schema | Is every card structurally valid? |
| Graph | Are ids unique and typed links resolvable? Are shared aliases arbitrated? |
| Build | Are generated artifacts deterministic and complete? |
| Retrieval | Do positive, paraphrase, and negative queries rank correctly at the runtime cutoff? |
| Rank regression | Did any expected card lose rank or margin? Did any card change layer? |
| Planning | Is execution readiness reported accurately? |
| Answer | Does the final response use the right definition, disclosure and refusal? (see [golden-questions.md](golden-questions.md)) |
| Freshness | Is the evidence still within its review window? |

Do not collapse these into one pass/fail signal.

## Fail closed

Unknown scope, missing evidence, unresolved semantics, stale sources, and unavailable execution interfaces must remain visible states. Empty output is not proof of zero, and failed retrieval is not proof that the knowledge does not exist.

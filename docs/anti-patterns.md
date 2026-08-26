# Naming, decision framework, anti-patterns

## Naming dictionary

One word per thing. Synonyms drift into second meanings; the validator and the reviewers use these words.

| Use | Not | Meaning |
|---|---|---|
| card | page, entry, article | one file with frontmatter and body |
| canonical card | master, primary, truth card | the one card that owns a definition |
| interface card | bridge card, locator | a dataset or dashboard card with `canonical_cards` |
| source card | raw card, doc card | the evidence bridge from a snapshot to cards |
| execution contract | filter block, rules | the machine-executed constraints on a card |
| framing | hard filter, chart filter | a view's own restriction, kept in `by_layer` |
| brief | summary, abstract | the compiled first section, under the length limit |
| capsule | digest, index page | handbook + briefs of one domain |
| layer | tier, class | `direct` / `guided` / `knowledge` |
| ruling | decision, arbitration note | the content of a consistency card |
| gap | issue, bug, request | a runtime or person-registered lead |
| ticket | task, job | an eligible gap assigned for a fix |
| gate | check, test, guard | a pass/fail condition on a change |
| registry | manifest of sources, catalogue | `raw/source-contracts.yaml` |
| tombstone | archive entry | a row in `retirements.jsonl` |
| owner role | owner, maintainer name | a role label; never a person in this repository |

## Decision framework

### Card, handbook, contract, or gap?

| The content is … | Put it in |
|---|---|
| a rule that must hold for every answer in the domain | the handbook |
| a filter or default the machine must apply when computing one card | that card's execution contract |
| a definition, value domain, procedure, trap or ruling | a card of that type |
| something a person said that nobody has verified | a gap record with `narrated` confidence |
| a dated observation that supports a card | a registry contract, referenced from the card's evidence |
| a description of what changed and why | the changelog |

### Which card type?

| Question the content answers | Type |
|---|---|
| how is it computed | metric |
| what does this field's value mean; which values count | dimension |
| what does this word mean; what is it not | concept |
| how do I produce this breakdown | playbook |
| how does this go wrong; how do I tell | trap |
| which of two cards wins this term | consistency |
| where is this dataset; what does it expose | dataset |
| where is this view; how does it frame the data | dashboard |
| what did this document establish | source |

### Metric or playbook?

A metric owns one formula. A playbook owns a procedure over one or more cards. "X by region for the last quarter" is a playbook over metric X; it is not a second metric.

### Definition or framing?

If removing the filter would change what the metric *means*, it is definition (`always_filter`). If removing it would only change what one view *shows*, it is framing (`by_layer`). When unsure, it is framing; promoting framing to definition silently narrows every answer.

## Anti-patterns

Each of these was done at least once and cost more to undo than to avoid.

1. **Shaping a card around the question that triggered it.** The requester's grouping becomes a "definition"; the next requester's grouping contradicts it.
2. **Hand-typing a value list.** It is right on the day it is written and wrong the day a value is added. Value domains cite a source.
3. **Putting examples and product names into the brief.** They score in retrieval and pull unrelated questions to the card.
4. **Question-shaped aliases.** "When does X expire" contains "when" and "expire", which match every lifecycle question in every domain.
5. **Copying a view's framing into the metric's `always_filter`.** Every answer about the metric is now silently restricted to what one dashboard shows.
6. **Editing prose and leaving the contract.** The machine keeps executing the old contract; the review reads the new prose and approves.
7. **Two cards holding one alias, resolved by "whichever ranks higher".** The answer changes whenever either card is edited. Write the consistency card.
8. **Adding a guessed interface to make a metric `direct`.** The layer count improves; the answers are invented.
9. **Combining partial interfaces to make a metric `direct`.** No single adapter can execute the complete contract; one active available bridge must expose every required field itself.
10. **Certifying on a raw source reference.** A link to a document is not a decision. Certification needs a technical item and a semantic decision.
11. **Setting or clearing `stale` without a reason.** Freshness normally derives the effective state; an explicit source override needs a reviewed `status_note`, and re-verification must update the evidence and dates before clearing it.
12. **Annotating instead of deleting.** "Note: this may be outdated, see also …" is a debt with interest. Delete and repoint.
13. **Bulk edits without a machine criterion.** Forty cards changed by pattern, three of them wrong, nobody can say which.
14. **Committing generated artifacts and then hand-fixing them.** The next build reverts the fix and the hash check fails in a place nobody is looking.
15. **Running build steps out of order.** The index is rebuilt after the pack; the pack ships yesterday's aliases.
16. **Treating "all evals green" as "nothing moved".** Rank and layer are compared, not only assertions.
17. **A salvage layer in the runtime.** A failed query becomes a cached or partial value with a confident sentence around it.
18. **Reporting empty output as zero.** Unavailable, filtered and empty are three different facts.
19. **Machine tickets written as intent.** "Fix the definition to be correct" produces improvisation; a literal template produces a diff.
20. **Prose verdicts as merge conditions.** A parser guessing whether "looks fine apart from…" is an approval.
21. **Merging in the same breath as reviewing.** The known finding ships because nobody re-read the counts.
22. **Caps on throughput as a safety measure.** A daily quota does not make wrong changes right; it makes right changes late.
23. **Mechanisms added after single incidents.** Every one is defensible; together they are unmaintainable. Remove one before adding one.
24. **Metaphors for mechanisms.** A name that needs explaining is renamed by what it does.
25. **Internal content in a public design repository.** Real names, asset ids, hosts, tokens, query results. The scan in `AGENTS.md` runs before every push.

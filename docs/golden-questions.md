# Golden questions

Routing evals check that the right card is found. Golden questions check that the right **answer** is given, including the cases where the right answer is "not from this knowledge".

## Why a separate set

- A card can be retrieved and still be misapplied (wrong date axis, framing copied into the definition).
- Some correct answers are refusals or ask-backs; retrieval evals cannot express them.
- The runtime's answer policy (disclosure, staleness, execution unavailable) is only testable end to end.

## Record contract

Every record in `evals/golden.jsonl` (schema: [golden-question.schema.json](../schemas/golden-question.schema.json)) states:

| Field | Values | Why it exists |
|---|---|---|
| `category` | definition, source, arbitration, disambiguation, refusal, known_bug, boundary, diagnostic, cross_metric | coverage is measured per category, so a set with no refusal questions is visibly incomplete |
| `question_style` | naive_real, analyst_precise, adversarial_leading, owner_check | a definition that survives a precise question and fails a naive one is a routing problem; one that fails a leading question is a disclosure problem |
| `answer_type` | numeric, list, definition, source, refusal, arbitration, explanation | decides how the answer is scored |
| `ground_truth_type` | measured_live, snapshot_verified, curator_arbitrated, owner_arbitrated, known_bug, absence_boundary | says where the truth came from; a measured value expires, a ruling does not |
| `scoring_method` | exact, tolerance, keyword, llm_judge_with_ref | a judged answer always has a reference; free judging is not a method |
| `expected` | numeric value for `answer_type: numeric`, otherwise non-blank reference text | only `scoring_method: tolerance` may carry `tolerance`, and it requires a numeric expected value; an unavailable value is modelled as a refusal or disclosure expectation, not as numeric prose |
| `source_type` | log, expert, synthetic | questions taken from real usage carry the most authority; synthetic ones carry the least and must not be used to overrule a real user's complaint |
| `must_disclose` / `must_not` | strings | the number can be right and the answer still wrong |
| `status` / `layer` | active, quarantine, deprecated / stable, volatile | a volatile question depends on live data and may be quarantined without blocking a release |

`evals/golden.jsonl` is required and non-empty in a complete domain. The reference validator checks each record's schema and card references, including old ids that resolve through redirects. It does not call an answering model or apply the scoring method; the end-to-end harness does that separately.

`must_disclose` and `must_not` are disjoint after case and whitespace normalization. A measured record cannot be dated after the validation `as_of` date, and multiple old ids in one field may not collapse through redirects to the same active card.

## Refusal is an answer

Categories `refusal` and `boundary` exist so that "this domain does not cover cash collection" and "the adapter is unavailable; here is the procedure" are scored as **correct**. A set where every expected answer is a value trains the system to invent values.

## Two metrics, not one

Report both, always:

1. **Structural trusted-reference rate**: of the answers given, how many cite a certified card whose definition applies. This can be computed without a judge.
2. **End-to-end correctness**: how many golden questions score as correct, per category.

A change that raises the second while lowering the first is usually a model doing more guessing; a change that raises the first while the second stays flat is usually a routing fix. Neither number alone is the goal.

## Sourcing questions

- Take questions from real usage whenever available, with the requester's wording intact and no identity attached.
- Ask domain owners for `owner_check` questions: the ones they would use to catch an impostor.
- Write synthetic questions to cover contracts (every arbitration, every boundary, every trap), and mark them as synthetic.
- Quarantine, do not delete, questions whose truth moved; re-measure and reactivate.

## Base versus candidate

Golden questions are run on the base and the candidate of every content change that touches a certified card. A drop in any category blocks; a drop in a quarantined or volatile question does not.

## What green does not prove

- that no card lost rank (see rank regression);
- that the answer will still be right after the freshness window expires;
- that a question phrased by a different person routes the same way — add the paraphrase when you learn of it.

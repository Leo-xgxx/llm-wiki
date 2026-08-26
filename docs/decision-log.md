# Decision log

Decisions that shaped this design, in the order they were made, including the ones that were reversed. Each entry states the decision, the alternative it replaced, and why. Dates are the month the decision was settled. Nothing here names a real organization, system, person or asset; the decisions are recorded because they transfer.

| When | Decision | Replaced | Why |
|---|---|---|---|
| 2026-07 | Git is the single source of truth; a workflow tracker only carries state, never content | a ledger-first workflow with the repository as a mirror | diff, rollback, machine validation and review only exist on the repository side |
| 2026-07 | One card serves agent, portal and command line; projections are built, not authored | separate documents per consumer | copies diverged within weeks |
| 2026-07 | Managed snapshots with provenance under `raw/`, KEEP/DELETE classification | a raw directory that accepted anything useful during mining | the directory became a dump; reviewers could not tell evidence from noise |
| 2026-07 | Metric cards inline how to obtain the value; interface cards stay thin and carry an explicit role | a separate "how to query" card per metric | two cards per concept doubled the maintenance and split ownership |
| 2026-07 | No bulk transformation without a machine-checkable criterion | pattern-based bulk edits | a bulk edit introduced errors that no one could locate; the rule now precedes every mass change |
| 2026-07 | Process artefacts (inventories, checklists, review notes) are deleted from the repository once they stop carrying a card's truth | keeping them "for history" | history lives in version control; the files misled readers about what was current |
| 2026-07 | Golden questions include refusal and boundary questions scored as correct | a set of value questions only | the system learned to invent values because every expected answer was a value |
| 2026-07 | Runtime safety mechanisms live in the runtime code, not as knowledge-side contracts; a "query contract" gate was built and then removed | a per-query contract mechanism | it duplicated the execution contract on cards and added a second place to be wrong; removed rather than maintained |
| 2026-07 | Status is a ranking and disclosure signal, not a permission; non-certified cards are answered from, with their state disclosed | hiding non-certified cards | hidden cards produced "unknown" for questions the repository could answer with a caveat |
| 2026-07 | No general background-job ledger until a recurring need appears that the gap store cannot serve | building the ledger early | nothing needed it; the trigger condition is recorded instead |
| 2026-07 | The conversation-side distillation flow (capture → organise → check → repair → promote) is judged unfit for the current knowledge shape; replaced in design by "register a structured lead, never produce a card directly" | a pipeline that produced draft cards from chat | drafts from conversation were confidently wrong; the redesign makes registering cheap and card-writing a separate, evidenced act |
| 2026-08 | Ranking is treated as a shared budget; alias and brief discipline are gates | treating content edits as local | a single alias and a single product name in a brief each displaced an unrelated domain's expected card |
| 2026-08 | Rank regression and layer comparison run as gates in addition to routing evals | "evals green" as the release condition | a card changed compiled layer and pushed a family card down four ranks with every eval passing |
| 2026-08 | Consistency cards arbitrate shared terms; a shared alias without an arbiter is a build error | first-come alias ownership | answers flipped when either holder was edited |
| 2026-08 | Cards define the method, not the phrasing; requester groupings go into the gap record | building cards from the wording of the triggering question | a card carried a fake open decision that existed only in one requester's words |
| 2026-08 | Structure before body: contract, handbook, bridges, evals, then prose | reviewing prose changes as complete | three review rounds in a row found correct prose over stale structure |
| 2026-08 | Certification is a signed re-verification obligation with a repository-wide window; freshness derives effective `stale`, while an explicit override needs a reviewed reason | certification as a permanent badge | certified cards silently aged; nobody owned the re-check |
| 2026-08 | Answering runtime: trust the model, feed hard facts, fail closed; pre-routing modules, scope locks and salvage layers removed | a pre-orchestrated pipeline with fallbacks | the pipeline answered confidently from the wrong module; salvage turned failures into plausible numbers |
| 2026-08 | Self-maintenance loop with three-way eligibility; no card without an authoritative source | opening a ticket for every repeated question | repeated questions without a source produced guessed cards |
| 2026-08 | Three locks before auto-merge; verdicts are machine-readable lines pinned to a revision; merge is a separate step | prose approvals and merge-on-approve | a merge shipped with a known finding because the prose verdict was read as approval |
| 2026-08 | Human MRs are never auto-fixed or auto-merged | symmetric treatment of human and machine MRs | people expect their branch to stay theirs |
| 2026-08 | Warden is failure-driven with a model-free poller and a shell fallback | a model-driven supervisor on a timer | the supervisor cost more than what it supervised and could fail silently |
| 2026-08 | Throughput limited only by correctness gates and owner decisions; daily quotas, time budgets and per-run caps removed | conservative caps as a safety measure | caps delayed correct changes and prevented nothing |
| 2026-08 | Do not stack mechanisms; remove one before adding one; single incidents do not justify gates | a gate per incident | the gate list outgrew anyone's ability to explain it |
| 2026-08 | Plain-language naming; metaphoric mechanism names retired | in-group jargon | new readers could not tell what a mechanism did from its name |
| 2026-08 | Generated artifacts leave Git except the id index and reviewed fixtures | committing build outputs | committed outputs drifted and were hand-edited; the build hash check now runs on a clean checkout |
| 2026-08 | This repository is a clean-room design record: no code, prompts, history or examples copied from any deployment | a public mirror with scrubbing | scrubbing is a losing game; re-deriving generically is safer and produces better documentation |

## Deferred, deliberately

Recorded so they are not re-proposed without new evidence:

- pre-injecting a catalogue of business lines into every session (cost without a measured benefit);
- a soft budget that stops a session after a fixed number of queries (a cap, see above);
- a general-purpose job ledger (trigger condition recorded instead);
- a data-permission model inside the knowledge repository (belongs to the host).

# Self-maintenance loop

The loop turns runtime failures into reviewed changes with machines doing every verifiable step and people doing every semantic one. Its governing sentence: **machines only handle changes that can be verified.**

## Overview

```text
gap record  ->  watermark + dedup  ->  eligibility (three-way)  ->  ticket
   ->  fixer branch + machine MR  ->  automated review  ->  (re-fix loop)
   ->  three locks  ->  merge  ->  release  ->  readback in the human channel
```

Every arrow is a state transition with a machine-checkable condition. Every box that needs a semantic decision routes to an owner role and waits.

## Gap intake

- Gap records are appended by the runtime and by people ([gap.schema.json](../schemas/gap.schema.json)).
- A watcher reads new records by **watermark** (hash of the first line plus a processed-line count); it does not rescan history. A scheduled sweep late in the day and a morning scan cover the watcher's failures.
- Deduplication uses three keys: same question shape, same candidate cards, same kind. A repeated coverage gap raises a counter on the existing ticket; it does not open a new one.

## Eligibility: the three-way gate

A gap becomes a ticket only through one of three doors. The gate filters both false leads and low-value ones.

| Door | Condition | Result |
|---|---|---|
| wrong answer | a certified card was applied and the answer was wrong, with evidence | ticket immediately |
| owner-confirmed | the owning role confirmed the definition (the requester's own claim does not count) | ticket immediately |
| repeated coverage gap | the same coverage gap recurred, but no authoritative source exists yet | labelled "repeated demand, source missing"; routed to a person to find an owner; **no card is produced without a source, no exception** |

Everything else stays a lead in the gap file, visible in statistics, and never becomes a ticket.

Gap kinds such as `ranking-miss`, `template-failure`, and `unavailable-interface` follow the same rule: they remain leads unless one of the three doors applies. They feed statistics and detector reports; they do not bypass eligibility.

## Ticket lifecycle

`registered → eligible → assigned → in-fix → in-review → re-fix → merged | rejected | parked`

- A ticket names the classification from intake (missing knowledge, ranking, wrong definition, adapter, transient), the candidate cards, the evidence available, and the acceptance check.
- The task given to a fixer uses **literal output templates**. Field names written in the ticket are copied verbatim by the fixer; anything that should be inferred is left blank on purpose. Intent-only instructions produce improvisation.
- `parked` is a real state with a reason; tickets do not silently age out.

## Roles

Six machine roles, each with one job and one workspace:

| Role | Job | Never does |
|---|---|---|
| sentinel | runs detectors (drift, usage audit, asset discovery, freshness), turns findings into gap records | edits cards |
| fixer (knowledge) | takes a knowledge ticket, edits cards on a machine branch, runs the local gates, opens the machine MR | merges |
| fixer (runtime) | same for the runtime code | merges |
| reviewer | reviews a machine MR at each new revision, grades findings, writes the machine-readable verdict line | fixes |
| operator | drains the ticket queue, assigns, re-assigns after review, opens the release | reviews its own assignments |
| warden | watches for failed runs and missing scheduled runs; escalates | anything with a model when nothing failed |

People hold two roles: the **owner** (semantic decisions, certification) and the **release approver** (the human step before a release reaches production when one is configured).

## Machine merge requests

- A machine MR lives on a namespaced branch, carries a marker line and an AI-assistance declaration in its description, and pins the reviewed revision.
- **One open machine MR per repository at a time.** A second fixer waits; parallel machine MRs on the same generated files conflict every time.
- On conflict or generated-file drift the fixer rebases and re-runs the build; it does not resolve conflicts by hand-editing generated artifacts.
- A human's MR is never auto-fixed and never auto-merged. Humans can invoke the fixer on their own MR with an explicit action; nothing happens by default.

## Review

- Each new revision gets a fresh review session; the memory of the review is the MR thread, not the reviewer's context.
- Findings are graded by impact × realistic probability, and each finding above the lowest grade names the trigger scenario.
- A reviewer that has independent evidence (it re-reads the interface definition, it re-runs the eval) uses it; "the description says" is not a review.
- When findings remain, the operator sends the ticket back to the **same** fixer on the **same** branch. Review cycles have no hard-coded maximum; they end when findings reach zero or the owner parks the ticket.

## Three locks before auto-merge

All three must hold on the same revision:

1. **Eligibility script says yes.** A deterministic script checks: machine branch, marker line, declaration, gates green, generated artifacts current, no touched file in an official area that requires an owner.
2. **Machine-readable verdict line** from the reviewer for that exact revision, with zero findings above the accepted grade. Prose verdicts are not parsed; a verdict for an older revision is not a verdict.
3. **The revision is pinned** at merge time under a lock, so a push between review and merge invalidates the merge.

Merge is its own step, executed by one script that takes the lock, re-checks the three conditions, and merges. Nothing else merges.

Expect most definition changes to touch an official area (handbook, consistency cards, execution contracts) and therefore require an owner review even when the gates are green. Auto-merge is intended for fixes that stay outside those areas.

## Warden: failure-driven supervision

- A cheap timer (no model) polls run outcomes. Only a **new failure** wakes the warden model to diagnose and post.
- If the warden itself fails, a shell-level fallback posts the raw failure to the human channel, so supervision never depends on the thing it supervises.
- A daily absence check lists scheduled runs that did not happen; a startup failure leaves no run record, so absence is a separate signal from failure.

## Draining the queue

The operator runs on a schedule, but the run has no time budget and no item cap: it ends when the queue has nothing assignable. If the run is interrupted, the next one resumes from the queue, not from a counter. A silent exit on an empty queue is the normal case, not an anomaly.

## Audit, notice and readback

- Exactly one human-facing channel receives: a daily summary, the review verdict of every merged machine MR, and warden escalations. Machine dashboards exist for forensics, not for people to watch.
- Every machine comment carries the same literal marker so it can be filtered and counted.
- Mentioning a person is a deliberate act with a fixed syntax; mentioning the bot itself is forbidden because it would re-trigger the loop.

## Acceptance

Measure the loop by outcomes, not activity:

- gaps closed per door, and the median time from gap to merged change;
- wrong answers that recur after a fix (should be zero; each one is a golden question now);
- the share of tickets that needed a human decision (aim: a minority, and falling);
- machine MRs merged without a human reading them, and how many were later reverted.

## Controlling the number of mechanisms

Every element above earned its place by removing a failure that recurred. The loop is reviewed periodically with one question per element: what failure returns if this is removed? If nothing, remove it. Additions follow the same rule in reverse.

## Emergency stop

Documented, not automated: a runbook lists how to pause each scheduled role, how to release the merge lock, and which state files to leave untouched so that resumption is a restart rather than a rebuild.

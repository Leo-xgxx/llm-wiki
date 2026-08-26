# Intake and mining

This document covers how knowledge gets in: the criteria for accepting it, the two input chains, the intake procedure for a single item, and the mining procedure for bootstrapping a whole domain.

## Inclusion criteria

- **What answering needs goes into a card; nothing else does.** Definitions, formulas, filters, value domains, traps, rulings, procedures, locations. Verification ledgers, refresh-cycle observations, incident chronology and process notes go into the changelog, the registry, or nowhere.
- **The test is "better than nothing, and not lying", not "perfect".** A usable card with explicit caveats beats a missing card. A card that states more certainty than its evidence supports is rejected regardless of how complete it looks.
- **No bridge, no card.** Content must play a role in answering (see card-model). Facts that are true but never needed become handbook notes at most.
- **No authoritative source, no card, no exceptions.** A repeated question without any source that can settle it is registered as "repeated demand, source missing" and routed to an owner. It does not become a draft card that guesses.
- **An initiator's decision counts.** When the person who owns a definition states it and confirms it, that is a valid semantic decision; record it as a `semantic-decision` contract naming the role and date. A requester's own claim about a definition they do not own is not a decision.
- **Method, not phrasing.** Before writing, ask "what steps does a complete computation of this take?" The step that was missing is the card's value. The requester's wording, ad-hoc groupings and one-off categories stay out.

## Two input chains

| Chain | For whom | Flow |
|---|---|---|
| A · repository | people comfortable with version control | clone → draft with the intake procedure → local validation → merge request → review → merge |
| B · conversation | everyone else | send a document or a statement to the bot → it registers a lead and drafts into `proposals/` → the person confirms or rejects on a card → a merge request is opened on their behalf |

In chain B the person performs exactly two actions: sending material and confirming or rejecting. Everything else (classification, probing, drafting, validation, opening the change) is machine work, and the draft never lands in the canonical tree without the confirmation.

## Intake of one item

### Four input types

| Input | First probe action |
|---|---|
| a stated definition ("X is computed as …") | find which interface exposes the fields; check for an existing owner card |
| a document | snapshot with provenance; extract candidate statements; mark each as fact, framing or opinion |
| a chart or report | read its definition (filters, grouping, time axis); decide which filters are framing and which are definition |
| a dashboard or entry page | treat as mining (below), not as a single item |

### Seven probe questions

Answer all seven before drafting; unanswered ones become caveats or a `needs-decision` status, never guesses.

1. Which interface(s) expose the fields, and at what grain?
2. Is it computable through a declared interface, or only explainable?
3. What is the computation, over logical fields?
4. What is the business rule behind it, and who owns that rule?
5. Which fields carry the inclusion rules, and what are their value domains?
6. What is upstream, and is the direct upstream stable?
7. What are the partition and time semantics, and which date axis is intended?

### Draft shape

The draft has five parts: definition (the brief), how to obtain it (procedure or interface, executable or not), common mistakes, suggested analysis, and folded evidence (registry references with dates). It is written to `proposals/`, a runtime-writable area outside the canonical tree. Nothing in `proposals/` is knowledge until a person confirms it and the change passes validation.

### Evidence status levels

Every extracted statement carries one of:

| Level | Meaning | May become |
|---|---|---|
| `verified_live` | checked against authoritative technical evidence whose registry provenance was `live` and captured no later than the gap; the claim must name that `evidence_ref` | card content with evidence |
| `user_confirmed` | the owning role confirmed it | card content with a semantic-decision contract |
| `narrated` | said in conversation or found in a low-trust note; unverified | a gap record, a caveat, or a ticket; never card content |

## The three questions for a new card

Reviewers ask them; authors answer them in advance.

1. **Does the title or formula encode a slice?** "X for segment Y" is usually a view framing or a playbook, not a metric.
2. **Is any enumeration in the brief hand-typed?** Every value list needs a value-domain source, a snapshot date, or a "look it up live" instruction.
3. **Does a new metric or dataset card have any grounding at all?** Lineage, a verified flag, or an upstream-generation note. A card with none of these is a guess with a schema.

## Mining a domain

Mining bootstraps a domain from an entry point (a dashboard, an overview page, a domain index document). The output is a complete domain: evidence layer, cards of all needed types, evaluation candidates and a landing instruction.

### Nine steps

1. **Fix the entry point and the boundary.** Write the domain descriptor first: id, owner role, boundaries to neighbouring domains.
2. **Inventory assets.** Every view, dataset and document the entry point references, with what each one is for. No content yet.
3. **Capture evidence.** Snapshot definitions and documents under `raw/` with provenance; register each in the source registry. Apply the KEEP/DELETE rule from [evidence-and-raw.md](evidence-and-raw.md).
4. **Extract statements.** From each snapshot, list candidate statements labelled fact / framing / opinion, with the evidence status level.
5. **Choose owners and types.** Group statements into candidate cards; one canonical home per concept; decide the type by the decision framework in [anti-patterns.md](anti-patterns.md).
6. **Write interface cards first.** Datasets and views, with logical fields. Metrics can only be grounded once an interface exposes their fields.
7. **Write canonical cards.** Metrics, dimensions, concepts, traps, then consistency cards for every shared term found in step 5.
8. **Write evaluation candidates.** For every card: a positive, a paraphrase, a near-neighbour negative; for every arbitration, a bare-term question; for every boundary, a refusal question.
9. **Land.** Validate, build, compare rank against the existing domains, write the changelog and the handbook, open the change.

### Tactics by source type

| Source | What it is good for | What to distrust |
|---|---|---|
| notification threads (alerts, change announcements) | the most timely record of when a definition broke or changed | anything stated as intent rather than as a change that happened |
| already-distilled material (a previous team's notes, a tool's help text) | vocabulary, boundaries, which questions recur | its definitions; second-hand, re-verify against an interface before certifying |
| low-trust documents (AI-organised summaries, notes marked "may be wrong") | leads and question shapes | every factual claim; treat as `narrated` |
| report and view definitions | exact filters, grouping and date axis | mistaking a view's framing for the metric's definition |
| interface schemas | field names, types, value domains | inferring meaning from a field name |

### What mining must not do

- It must not certify. Mining produces `draft` and `review` cards; certification is a separate reviewed act.
- It must not invent interfaces to make a metric executable.
- It must not copy entire dumps into `raw/` because they were available.
- It must not organise the domain around the questions that happened to be asked during mining.

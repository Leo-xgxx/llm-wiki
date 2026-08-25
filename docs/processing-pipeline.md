# Processing pipeline

## 1. Intake

Capture the request and decide whether it describes new knowledge, a correction, a routing gap, or a transient incident. Do not create a card merely because a question was asked.

## 2. Evidence collection

Collect the smallest stable evidence needed to verify the proposed knowledge. Exclude row dumps, full dependency graphs, temporary errors, signed URLs, sessions, and credentials.

## 3. Normalization

Choose one canonical owner and card type. Extract:

- definition and formula;
- grain and time semantics;
- inclusion and exclusion rules;
- dimensions and value-domain handling;
- ambiguity boundaries;
- typed relations and evidence references.

## 4. Structural validation

Reject changes with missing required fields, duplicate IDs, invalid status values, broken links, conflicting ownership, or active references to retired cards.

## 5. Deterministic build

Compile source cards into immutable runtime artifacts. Store source and artifact hashes so the runtime can prove that its indexes and cards belong to the same release.

The manifest contract should include at least the card ID, source path, type, lifecycle state, knowledge role, and source-content hash. A fixture path is relative to its example domain root. Checked-in example manifests are named as expected-output fixtures; production manifests are generated outside Git.

## 6. Retrieval

Use a staged process:

```text
question
  -> route by subject and requested action
  -> resolve canonical candidates and one-hop relations
  -> decide whether execution is possible
  -> assemble the answer with evidence and disclosure policy
```

## 7. Feedback

Classify failures before changing content:

- missing knowledge: add or extend a canonical card;
- bad ranking: change aliases or routing and add negative tests;
- wrong definition: update the canonical card with evidence;
- unavailable live data: fix the adapter or disclose the limitation;
- temporary incident: record it outside the canonical card body.

## 8. Retirement

Deleting a card is a graph operation, not a file deletion. Remove active inbound references and first mark it deprecated with a retirement record containing the outcome, reason, date, and target card when applicable. The three outcomes are: replaced by another card, merged into another card, or retired without replacement.

Before physical deletion, append a permanent tombstone to the domain's `retirements.jsonl`. A tombstone contains the original card ID, outcome, optional target card, reason, retirement date, and final source hash. The build validates target existence and retains tombstones after source-card deletion, so deletion does not erase the audit trail.

# Acme Analytics example

This is a synthetic domain that demonstrates the repository contracts without representing any real organization or data source.

It contains:

- one canonical metric card;
- one thin dataset interface card;
- a reviewed expected-manifest fixture with source hashes;
- positive, near-neighbor negative, and planning examples;
- minimal fictional source contracts with no row data.

The fictional metric is net revenue by day. The interface card locates a made-up daily orders dataset but delegates the definition to the canonical metric card.

`evals/manifest.expected.jsonl` is hand-reviewed test data for the build contract. It is not a generated runtime index.

`domain.yaml` names `raw/source-contracts.yaml` as the machine-readable registry for every `source_refs` and `evidence.ref` value in the example cards.

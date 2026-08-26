# 2026-08-26 · design review alignment

## Contract changes

- Documentation aligned on Git exceptions, gap v2 status, three-way eligibility wording, and classification mapping in the glossary.
- `acme-analytics.dimension.order-status`: set to `needs-decision` after the interface contract listed `on_hold`; recognition rule is explicitly open.
- `acme-analytics.metric.gross-revenue`: added `depends_on` the order-status dimension card.
- Golden fixtures: corrected dashboard framing category, added diagnostic, support-boundary refusal, and on_hold disclosure cases.
- Routing fixtures: added trap and source card routes.

## Evidence

- Re-checked `acme-analytics.synthetic.orders-v1` on 2026-08-26 for the new `on_hold` value.

## Affected routes

- `pending-refund-trap` and `pricing-policy-source` routing records added.
- Golden evals now cover `diagnostic`, acme-support refusal, and `needs-decision` disclosure for `on_hold`.

## Ranking or execution behaviour

- No card changed compiled layer. Order-status effective status is now `needs-decision`.

## Rollback

- Restore order-status to `certified` with the three-value domain and revert the new eval records if the open decision is cancelled.

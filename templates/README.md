# Templates

One template per card type plus the two domain-level documents. Copy, fill, and run `tools/validate.py` on the domain.

| Template | Type | Role |
|---|---|---|
| `metric-card.md` | metric | canonical |
| `dimension-card.md` | dimension | canonical |
| `concept-card.md` | concept | canonical |
| `playbook-card.md` | playbook | canonical |
| `trap-card.md` | trap | canonical |
| `consistency-card.md` | consistency | canonical |
| `dataset-card.md` | dataset | interface |
| `dashboard-card.md` | dashboard | interface |
| `source-card.md` | source | evidence |
| `domain-handbook.md` | — | domain `AGENTS.md`, read before cards |
| `changelog-entry.md` | — | one file per change under `changelog/` |

Comments inside the templates (`# ...` in frontmatter, `<!-- -->` in the body) explain the rule behind each field; delete them when filling in.

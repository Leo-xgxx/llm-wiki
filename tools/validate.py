#!/usr/bin/env python3
"""Reference validator for the LLM Wiki contracts.

Usage:
    python3 tools/validate.py examples/acme-analytics [more domain dirs] [--write-manifest] [--as-of YYYY-MM-DD]

It is deliberately small. It proves that the fixtures in this repository obey
their own contracts; a production build would grow from the same checks.

Checks, in order:
  1. domain.yaml, source registry, handbook exist and validate.
  2. every card validates against schemas/card.schema.json.
  3. cross-record rules: id prefixes, directory placement, reference existence,
     registry resolution, supersedes/retirement reciprocity, tombstones, redirects,
     alias arbitration, formula field coverage, freshness, brief length.
  4. deterministic manifest (id, path, type, title, status, knowledge_role,
     layer, effective_status, source_sha256) compared with evals/manifest.expected.jsonl.
  5. routing and golden evaluation records validate and point at existing cards.

Exit status is 1 when any ERROR was reported.
Requires PyYAML and jsonschema.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import re
import sys

try:
    import yaml
    import jsonschema
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(f"missing dependency: {exc}. Install with: pip install pyyaml jsonschema\n")
    sys.exit(2)

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCHEMA_DIR = ROOT / "schemas"
BRIEF_LIMIT = 900
TYPE_DIR = {
    "metric": "metrics", "dataset": "datasets", "dimension": "dimensions", "concept": "concepts",
    "playbook": "playbooks", "trap": "traps", "consistency": "consistency", "dashboard": "dashboards",
    "source": "sources",
}
FORMULA_STOPWORDS = {
    "sum", "count", "avg", "min", "max", "distinct", "case", "when", "then", "else", "end", "and", "or",
    "not", "null", "coalesce", "if", "abs", "round", "div", "nullif",
}


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def info(self, msg: str) -> None:
        self.infos.append(msg)

    def dump(self) -> None:
        for m in self.errors:
            print(f"ERROR {m}")
        for m in self.warnings:
            print(f"WARN  {m}")
        for m in self.infos:
            print(f"INFO  {m}")


def load_schema(name: str) -> jsonschema.Draft202012Validator:
    with open(SCHEMA_DIR / name, encoding="utf-8") as fh:
        schema = json.load(fh)
    cls = jsonschema.Draft202012Validator
    return cls(schema, format_checker=cls.FORMAT_CHECKER)


def schema_errors(validator: jsonschema.Draft202012Validator, obj: object) -> list[str]:
    return [f"{'/'.join(str(p) for p in e.absolute_path) or '<root>'}: {e.message}" for e in validator.iter_errors(obj)]


def read_card(path: pathlib.Path, rep: Report) -> tuple[dict | None, str, str]:
    raw = path.read_bytes()
    if b"\r\n" in raw:
        rep.warn(f"{path}: CRLF line endings normalized to LF for hashing")
        raw = raw.replace(b"\r\n", b"\n")
    if not raw.endswith(b"\n"):
        rep.error(f"{path}: file must end with a newline (hash contract)")
    digest = hashlib.sha256(raw).hexdigest()
    text = raw.decode("utf-8")
    if not text.startswith("---\n"):
        rep.error(f"{path}: missing frontmatter")
        return None, "", digest
    try:
        _, fm_text, body = text.split("---\n", 2)
    except ValueError:
        rep.error(f"{path}: unterminated frontmatter")
        return None, "", digest
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        rep.error(f"{path}: frontmatter is not valid YAML: {exc}")
        return None, body, digest
    return fm, body, digest


def first_section(body: str) -> tuple[str, str]:
    """Return (heading, text) of the first H2 section; it compiles into the brief."""
    m = re.search(r"^## (.+)$", body, re.M)
    if not m:
        return "", ""
    rest = body[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    section = rest[: nxt.start()] if nxt else rest
    return m.group(1).strip(), section.strip()


def formula_identifiers(formula: str) -> set[str]:
    return {t for t in re.findall(r"[a-z_][a-z0-9_]*", formula.lower()) if t not in FORMULA_STOPWORDS}


def derive_layer(card: dict, interfaces_for: dict[str, list[dict]]) -> str:
    t = card["type"]
    if t in {"concept", "trap", "consistency", "dimension", "source"}:
        return "knowledge"
    if card["knowledge_role"] == "interface":
        return "guided"
    if t == "metric":
        bridges = interfaces_for.get(card["id"], [])
        if not bridges:
            return "knowledge"
        live = any(str(b.get("query_interface", {}).get("availability", "")).lower().startswith("available") for b in bridges)
        return "direct" if live and card.get("execution_contract") else "guided"
    if t == "playbook":
        return "guided" if card.get("procedure", {}).get("executable") else "knowledge"
    return "knowledge"


def effective_status(card: dict, as_of: dt.date) -> str:
    if card["status"] in {"deprecated", "stale"}:
        return card["status"]
    review_after = dt.date.fromisoformat(str(card["freshness"]["review_after"]))
    return "stale" if review_after < as_of else card["status"]


def read_jsonl(path: pathlib.Path, rep: Report) -> list[dict]:
    rows: list[dict] = []
    if not path.exists():
        return rows
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            rep.error(f"{path}:{n}: invalid JSON: {exc}")
    return rows


def validate_domain(domain_dir: pathlib.Path, rep: Report, write_manifest: bool, as_of: dt.date) -> None:
    card_v = load_schema("card.schema.json")
    domain_v = load_schema("domain.schema.json")
    registry_v = load_schema("source-registry.schema.json")
    tomb_v = load_schema("tombstone.schema.json")
    redirect_v = load_schema("redirects.schema.json")
    manifest_v = load_schema("manifest.schema.json")
    routing_v = load_schema("routing-eval.schema.json")
    golden_v = load_schema("golden-question.schema.json")
    gap_v = load_schema("gap.schema.json")

    # 1. domain descriptor, registry, handbook
    dpath = domain_dir / "domain.yaml"
    if not dpath.exists():
        rep.error(f"{dpath}: missing")
        return
    domain = yaml.safe_load(dpath.read_text(encoding="utf-8"))
    for e in schema_errors(domain_v, domain):
        rep.error(f"{dpath}: {e}")
    domain_id = domain.get("id", domain_dir.name)
    if domain_id != domain_dir.name:
        rep.warn(f"{dpath}: id {domain_id} differs from directory name {domain_dir.name}")

    registry_path = domain_dir / domain.get("source_registry", "raw/source-contracts.yaml")
    registry: dict[str, dict] = {}
    if registry_path.exists():
        reg = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        for e in schema_errors(registry_v, reg):
            rep.error(f"{registry_path}: {e}")
        for c in reg.get("contracts", []):
            if c["id"] in registry:
                rep.error(f"{registry_path}: duplicate contract id {c['id']}")
            registry[c["id"]] = c
    else:
        rep.error(f"{registry_path}: source registry missing")

    handbook = domain_dir / domain.get("handbook", "AGENTS.md")
    if not handbook.exists():
        rep.error(f"{handbook}: domain handbook missing (read-before-cards contract)")

    # 2. cards
    cards: dict[str, dict] = {}
    bodies: dict[str, str] = {}
    digests: dict[str, str] = {}
    paths: dict[str, str] = {}
    for path in sorted((domain_dir / "wiki").rglob("*.md")):
        fm, body, digest = read_card(path, rep)
        if fm is None:
            continue
        errs = schema_errors(card_v, fm)
        for e in errs:
            rep.error(f"{path}: {e}")
        if errs or "id" not in fm:
            continue
        cid = fm["id"]
        if cid in cards:
            rep.error(f"{path}: duplicate card id {cid}")
            continue
        cards[cid] = fm
        bodies[cid] = body
        digests[cid] = digest
        paths[cid] = path.relative_to(domain_dir).as_posix()

    referenced_contracts: set[str] = set()
    interfaces_for: dict[str, list[dict]] = {}
    for cid, card in cards.items():
        for target in card.get("canonical_cards", []):
            interfaces_for.setdefault(target, []).append(card)

    active = {cid for cid, c in cards.items() if c["status"] != "deprecated"}

    def ref_exists(ref: str) -> bool:
        return ref in cards

    for cid, card in cards.items():
        p = paths[cid]
        # id, domain, directory
        prefix, ctype, _ = cid.split(".", 2)
        if prefix != card["domain"] or card["domain"] != domain_id:
            rep.error(f"{p}: id prefix / domain field / directory domain disagree ({prefix}, {card['domain']}, {domain_id})")
        if ctype != card["type"]:
            rep.error(f"{p}: id says type {ctype} but frontmatter says {card['type']}")
        expected_dir = f"wiki/{TYPE_DIR[card['type']]}/"
        if not p.startswith(expected_dir):
            rep.error(f"{p}: {card['type']} cards live under {expected_dir}")

        # references
        rel = card["relations"]
        for kind in ("depends_on", "related", "supersedes"):
            for ref in rel[kind]:
                if ref == cid:
                    rep.error(f"{p}: relations.{kind} points at itself")
                elif not ref_exists(ref):
                    rep.error(f"{p}: relations.{kind} -> {ref} does not exist")
                elif kind == "depends_on" and ref not in active and cid in active:
                    rep.error(f"{p}: active card depends_on deprecated card {ref}")
        for ref in card.get("canonical_cards", []):
            if not ref_exists(ref):
                rep.error(f"{p}: canonical_cards -> {ref} does not exist")
            elif cards[ref]["knowledge_role"] != "canonical":
                rep.error(f"{p}: canonical_cards -> {ref} is not a canonical card")
            elif ref not in active and cid in active:
                rep.error(f"{p}: active interface bridges to deprecated card {ref}")
        for ref in card.get("index_to", []):
            if not ref_exists(ref):
                rep.error(f"{p}: index_to -> {ref} does not exist")
            elif ref not in active and cid in active:
                rep.error(f"{p}: active source card indexes deprecated card {ref}")
        arb = card.get("arbitration")
        if arb:
            for ref in arb["parties"]:
                if not ref_exists(ref):
                    rep.error(f"{p}: arbitration.parties -> {ref} does not exist")
                elif ref not in active:
                    rep.error(f"{p}: arbitration party {ref} is deprecated")
            if arb.get("default_party") and arb["default_party"] not in arb["parties"]:
                rep.error(f"{p}: arbitration.default_party must be one of the parties")
        ret = card.get("retirement")
        if ret and ret.get("target_card"):
            tgt = ret["target_card"]
            if not ref_exists(tgt):
                rep.error(f"{p}: retirement.target_card -> {tgt} does not exist")
            elif tgt not in active:
                rep.error(f"{p}: retirement.target_card -> {tgt} is itself deprecated")
            elif cid not in cards[tgt]["relations"]["supersedes"]:
                rep.error(f"{p}: {tgt} must list {cid} in relations.supersedes (reciprocity)")
        for ref in rel["supersedes"]:
            if ref_exists(ref):
                other = cards[ref]
                if other["status"] != "deprecated":
                    rep.error(f"{p}: supersedes {ref} but that card is not deprecated")
                elif other.get("retirement", {}).get("target_card") != cid:
                    rep.error(f"{p}: supersedes {ref} but its retirement.target_card is not {cid}")

        # registry resolution
        for ref in card.get("source_refs", []):
            referenced_contracts.add(ref)
            if ref not in registry:
                rep.error(f"{p}: source_refs -> {ref} not in registry")
        for ev in card["evidence"]:
            referenced_contracts.add(ev["ref"])
            if ev["ref"] not in registry:
                rep.error(f"{p}: evidence.ref -> {ev['ref']} not in registry")
            elif registry[ev["ref"]]["kind"] != ev["kind"]:
                rep.warn(f"{p}: evidence {ev['ref']} kind {ev['kind']} differs from registry kind {registry[ev['ref']]['kind']}")
        vd = card.get("value_domain")
        if vd:
            referenced_contracts.add(vd["source_ref"])
            if vd["source_ref"] not in registry:
                rep.error(f"{p}: value_domain.source_ref -> {vd['source_ref']} not in registry")
        snap = card.get("snapshot")
        if snap:
            referenced_contracts.add(snap["registry_ref"])
            if snap["registry_ref"] not in registry:
                rep.error(f"{p}: snapshot.registry_ref -> {snap['registry_ref']} not in registry")

        # freshness
        fr = card["freshness"]
        lv = dt.date.fromisoformat(str(fr["last_verified"]))
        ra = dt.date.fromisoformat(str(fr["review_after"]))
        if ra <= lv:
            rep.error(f"{p}: freshness.review_after must be after last_verified")
        for ev in card["evidence"]:
            if dt.date.fromisoformat(str(ev["checked_at"])) > lv:
                rep.warn(f"{p}: evidence checked_at {ev['checked_at']} is after last_verified {lv}")
        if cid in active and ra < as_of:
            rep.warn(f"{p}: review window expired on {ra}; effective status is stale")

        # brief
        heading, brief = first_section(bodies[cid])
        if not heading:
            rep.error(f"{p}: body needs at least one '## ' section; the first one compiles into the brief")
        else:
            if len(brief) > BRIEF_LIMIT:
                rep.error(f"{p}: first section '{heading}' is {len(brief)} chars; brief limit is {BRIEF_LIMIT}")
            if re.search(r":\s*$", brief, re.M):
                rep.warn(f"{p}: first section has a line ending in ':' (dangling lead-in; truncation would orphan it)")
        for alias in card.get("aliases", []):
            if len(alias.split()) >= 6:
                rep.warn(f"{p}: alias '{alias}' looks like a phrase, not a noun surface")

        # formula coverage
        if card["type"] == "metric" and cid in active:
            idents = formula_identifiers(card["definition"]["formula"])
            bridges = interfaces_for.get(cid, [])
            if not bridges:
                rep.info(f"{p}: no interface bridges to this metric; compiles as knowledge")
            else:
                fields = set()
                for b in bridges:
                    fields.update(b["query_interface"]["logical_fields"])
                missing = idents - fields
                if missing:
                    rep.error(f"{p}: formula uses {sorted(missing)} not exposed by any bridging interface")

    # alias arbitration
    holders: dict[str, list[str]] = {}
    for cid in active:
        for alias in cards[cid].get("aliases", []):
            holders.setdefault(alias.strip().lower(), []).append(cid)
    arbiters = {cid: cards[cid]["arbitration"] for cid in active if cards[cid]["type"] == "consistency"}
    for alias, owners in holders.items():
        if len(owners) >= 2:
            rep.error(f"alias '{alias}' held by {owners}; one surface has one holder — move it to a consistency card that lists these cards as parties")
    for cid, a in arbiters.items():
        term = a["term"].strip().lower()
        for party in a["parties"]:
            if party in cards and term in {x.strip().lower() for x in cards[party].get("aliases", [])}:
                rep.error(f"{paths[cid]}: party {party} still holds the arbitrated term '{a['term']}' as an alias")
        if term not in {x.strip().lower() for x in cards[cid].get("aliases", [])}:
            rep.warn(f"{paths[cid]}: consistency card should hold its own term '{a['term']}' as an alias so routing lands here")

    for contract_id in registry:
        if contract_id not in referenced_contracts:
            rep.warn(f"{registry_path}: contract {contract_id} is not referenced by any card")

    # tombstones and redirects
    tomb_path = domain_dir / domain.get("retirements", "retirements.jsonl")
    tombs = read_jsonl(tomb_path, rep)
    tomb_ids = set()
    for n, row in enumerate(tombs, 1):
        for e in schema_errors(tomb_v, row):
            rep.error(f"{tomb_path}:{n}: {e}")
        tomb_ids.add(row.get("id"))
        tgt = row.get("target_card")
        if tgt and tgt not in active:
            rep.error(f"{tomb_path}:{n}: target_card {tgt} is not an active card")
        if row.get("id") in active:
            rep.error(f"{tomb_path}:{n}: tombstone id {row['id']} is still an active card")
        if row.get("deleted_on") and row.get("id") in cards:
            rep.error(f"{tomb_path}:{n}: tombstone says deleted but the file still exists")
        if not row.get("deleted_on") and row.get("id") not in cards:
            rep.error(f"{tomb_path}:{n}: no deleted_on but card file is gone")
        if row.get("id") in cards and not row.get("deleted_on"):
            if digests[row["id"]] != row.get("final_sha256"):
                rep.warn(f"{tomb_path}:{n}: final_sha256 does not match current file (expected once the file is frozen)")
    for cid in cards:
        if cards[cid]["status"] == "deprecated" and cid not in tomb_ids:
            rep.error(f"{paths[cid]}: deprecated card has no tombstone in {tomb_path.name}")

    redirect_path = domain_dir / domain.get("redirects", "redirects.json")
    if redirect_path.exists():
        redirects = json.loads(redirect_path.read_text(encoding="utf-8"))
        for e in schema_errors(redirect_v, redirects):
            rep.error(f"{redirect_path}: {e}")
        for r in redirects.get("redirects", []):
            if r["from"] in active:
                rep.error(f"{redirect_path}: redirect from active card {r['from']}")
            if r["to"] not in active:
                rep.error(f"{redirect_path}: redirect to non-active card {r['to']}")
        redirect_from = {r["from"] for r in redirects.get("redirects", [])}
        for tid in tomb_ids:
            if tid not in redirect_from:
                rep.warn(f"{redirect_path}: tombstoned id {tid} has no redirect")

    # manifest
    rows = []
    for cid in sorted(active):
        c = cards[cid]
        rows.append({
            "id": cid, "path": paths[cid], "type": c["type"], "title": c["title"], "status": c["status"],
            "knowledge_role": c["knowledge_role"], "layer": derive_layer(c, interfaces_for),
            "effective_status": effective_status(c, as_of), "source_sha256": digests[cid],
        })
    for row in rows:
        for e in schema_errors(manifest_v, row):
            rep.error(f"manifest row {row['id']}: {e}")
    manifest_path = domain_dir / "evals" / "manifest.expected.jsonl"
    rendered = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
    if write_manifest:
        manifest_path.parent.mkdir(exist_ok=True)
        manifest_path.write_text(rendered, encoding="utf-8")
        rep.info(f"{manifest_path}: written ({len(rows)} rows)")
    elif manifest_path.exists():
        if manifest_path.read_text(encoding="utf-8") != rendered:
            rep.error(f"{manifest_path}: differs from deterministic build; review and run --write-manifest")
        else:
            rep.info(f"{manifest_path}: matches build ({len(rows)} rows)")
    else:
        rep.error(f"{manifest_path}: missing; run --write-manifest after review")

    # evals
    def check_eval(path: pathlib.Path, validator, card_fields: tuple[str, ...]) -> None:
        seen = set()
        for n, row in enumerate(read_jsonl(path, rep), 1):
            for e in schema_errors(validator, row):
                rep.error(f"{path}:{n}: {e}")
            if row.get("id") in seen:
                rep.error(f"{path}:{n}: duplicate eval id {row['id']}")
            seen.add(row.get("id"))
            for field in card_fields:
                for ref in row.get(field, []):
                    if ref not in active:
                        rep.error(f"{path}:{n}: {field} -> {ref} is not an active card")
            if "negative_queries" in row and not row["negative_queries"]:
                rep.warn(f"{path}:{n}: no negative queries; ranking safety is untested")

    check_eval(domain_dir / "evals" / "routing.jsonl", routing_v, ("expected_cards", "required_interfaces"))
    check_eval(domain_dir / "evals" / "golden.jsonl", golden_v, ("expected_cards",))
    gaps = domain_dir / "gaps.example.jsonl"
    for n, row in enumerate(read_jsonl(gaps, rep), 1):
        for e in schema_errors(gap_v, row):
            rep.error(f"{gaps}:{n}: {e}")

    rep.info(f"{domain_dir}: {len(cards)} cards ({len(active)} active), {len(registry)} contracts, {len(tombs)} tombstones")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("domains", nargs="+", help="domain directories containing domain.yaml")
    ap.add_argument("--write-manifest", action="store_true", help="rewrite evals/manifest.expected.jsonl (reviewed change only)")
    ap.add_argument("--as-of", default=None, help="validation date for freshness (default: today)")
    args = ap.parse_args()
    as_of = dt.date.fromisoformat(args.as_of) if args.as_of else dt.date.today()
    rep = Report()
    for d in args.domains:
        validate_domain(pathlib.Path(d).resolve(), rep, args.write_manifest, as_of)
    rep.dump()
    print(f"summary: {len(rep.errors)} errors, {len(rep.warnings)} warnings")
    return 1 if rep.errors else 0


if __name__ == "__main__":
    sys.exit(main())

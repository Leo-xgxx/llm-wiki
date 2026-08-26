#!/usr/bin/env python3
"""Reference validator for the LLM Wiki contracts.

Usage:
    python3 tools/validate.py examples/acme-analytics [more domain dirs] [--write-manifest] [--as-of YYYY-MM-DD]

It is a reference implementation. It proves that the fixtures in this
repository obey their structural and cross-record contracts; a production
build would add retrieval, execution, and answer-scoring gates separately.

Checks, in order:
  1. domain.yaml, source registry, handbook exist and validate.
  2. every card validates against schemas/card.schema.json.
  3. cross-record rules: id prefixes, directory placement, reference existence,
     registry resolution, supersedes/retirement reciprocity, tombstones, redirects,
     alias arbitration, formula field coverage, freshness, brief length.
  4. deterministic manifest (id, path, type, title, status, knowledge_role,
     layer, effective_status, source_sha256) compared with evals/manifest.expected.jsonl.
  5. routing and golden evaluation records validate and point at existing cards.

--write-manifest behaviour: validation errors prevent every requested manifest
update. Targets are then updated independently in order; a failed target keeps
its existing fixture and stops later updates.

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
from dataclasses import dataclass
from typing import Iterable

try:
    import jsonschema
except ImportError as exc:  # pragma: no cover
    sys.stderr.write(f"missing dependency: {exc}. Install with: python3 -m pip install -r requirements.txt\n")
    sys.exit(2)

try:
    from tools.validator_io import (
        Report,
        atomic_write_manifest,
        audit_snapshot_directory,
        discover_card_paths,
        domain_path,
        load_schema as load_schema_file,
        parse_json,
        read_bytes,
        read_card,
        read_jsonl,
        read_utf8,
        read_yaml,
        require_nonempty_file,
        require_path,
        schema_errors,
    )
except ModuleNotFoundError:  # Running as ``python3 tools/validate.py``.
    from validator_io import (  # type: ignore[no-redef]
        Report,
        atomic_write_manifest,
        audit_snapshot_directory,
        discover_card_paths,
        domain_path,
        load_schema as load_schema_file,
        parse_json,
        read_bytes,
        read_card,
        read_jsonl,
        read_utf8,
        read_yaml,
        require_nonempty_file,
        require_path,
        schema_errors,
    )

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
TECHNICAL_EVIDENCE_KINDS = {
    "schema-contract",
    "interface-contract",
    "implementation-expression",
    "observed-output",
    "document-snapshot",
}

DECLARED_PATHS = {
    "source_registry": "file",
    "handbook": "file",
    "retirements": "file",
    "redirects": "file",
    "changelog_dir": "directory",
}

SCHEMA_NAMES = (
    "card.schema.json",
    "domain.schema.json",
    "source-registry.schema.json",
    "tombstone.schema.json",
    "redirects.schema.json",
    "manifest.schema.json",
    "routing-eval.schema.json",
    "golden-question.schema.json",
    "gap.schema.json",
)
_VALIDATOR_CACHE: dict[tuple[object, ...], tuple[jsonschema.Draft202012Validator, ...]] = {}


def load_schema(name: str, rep: Report) -> jsonschema.Draft202012Validator | None:
    return load_schema_file(SCHEMA_DIR, name, rep)


def load_validators(rep: Report) -> tuple[jsonschema.Draft202012Validator, ...] | None:
    """Load immutable repository schemas once per schema snapshot."""
    try:
        signature: tuple[object, ...] = (
            str(SCHEMA_DIR.resolve()),
            *(
                (name, hashlib.sha256((SCHEMA_DIR / name).read_bytes()).digest())
                for name in SCHEMA_NAMES
            ),
        )
    except OSError as exc:
        rep.error(f"{SCHEMA_DIR}: could not inspect schemas: {exc}")
        return None
    cached = _VALIDATOR_CACHE.get(signature)
    if cached is not None:
        return cached
    loaded = tuple(load_schema(name, rep) for name in SCHEMA_NAMES)
    if any(validator is None for validator in loaded):
        return None
    validators = tuple(loaded)  # type: ignore[arg-type]
    _VALIDATOR_CACHE.clear()
    _VALIDATOR_CACHE[signature] = validators
    return validators


def resolve_domain_as_of(
    domain: dict,
    descriptor_path: pathlib.Path,
    override: dt.date | None,
    rep: Report,
) -> dt.date:
    if override is not None:
        return override
    fixture_value = domain.get("fixture_as_of")
    if fixture_value is None:
        return dt.date.today()
    if isinstance(fixture_value, str):
        try:
            return dt.date.fromisoformat(fixture_value)
        except ValueError:
            pass
    rep.error(f"{descriptor_path}: fixture_as_of must be an ISO date")
    return dt.date.today()


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


def execution_filter_fields(card: dict) -> set[str]:
    fields: set[str] = set()
    contract = card.get("execution_contract", {})
    if not isinstance(contract, dict):
        return fields
    for item in contract.get("always_filter", []):
        if isinstance(item, dict) and isinstance(item.get("field"), str):
            fields.add(item["field"].lower())
    for layer in contract.get("by_layer", []):
        if not isinstance(layer, dict):
            continue
        for key in ("require_filter", "forbid_filter"):
            for item in layer.get(key, []):
                if isinstance(item, dict) and isinstance(item.get("field"), str):
                    fields.add(item["field"].lower())
    return fields


def execution_fields(card: dict) -> set[str]:
    fields = execution_filter_fields(card)
    contract = card.get("execution_contract", {})
    if not isinstance(contract, dict):
        return fields
    for field in contract.get("required_fields", []):
        if isinstance(field, str):
            fields.add(field.lower())
    return fields


def filter_signature(item: object) -> tuple[str, str, str] | None:
    if not isinstance(item, dict):
        return None
    field = item.get("field")
    operator = item.get("op")
    if not isinstance(field, str) or not isinstance(operator, str):
        return None
    value = json.dumps(item.get("value"), ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return field.strip().lower(), operator, value


def active_interfaces_by_canonical(cards: dict[str, dict]) -> dict[str, list[dict]]:
    result: dict[str, list[dict]] = {}
    for card in cards.values():
        if card.get("status") == "deprecated" or card.get("knowledge_role") != "interface":
            continue
        for target in card.get("canonical_cards", []):
            if isinstance(target, str):
                result.setdefault(target, []).append(card)
    return result


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
        needed = formula_identifiers(card.get("definition", {}).get("formula", "")) | execution_fields(card)
        live = any(
            isinstance(b.get("query_interface", {}).get("availability"), dict)
            and b["query_interface"]["availability"].get("status") == "available"
            and needed.issubset({str(field).lower() for field in b["query_interface"].get("logical_fields", [])})
            for b in bridges
        )
        return "direct" if live and card.get("execution_contract") else "guided"
    if t == "playbook":
        return "guided" if card.get("procedure", {}).get("executable") else "knowledge"
    return "knowledge"


def effective_status(card: dict, as_of: dt.date) -> str:
    if card["status"] == "deprecated":
        return card["status"]
    review_after = dt.date.fromisoformat(str(card["freshness"]["review_after"]))
    return "stale" if review_after <= as_of else card["status"]


def parse_rfc3339(value: str) -> dt.datetime:
    """Parse the RFC 3339 subset used by gap records, with an explicit timezone."""
    if not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:[.,]\d+)?(?:[Zz]|[+-]\d{2}:\d{2})",
        value,
    ):
        raise ValueError("expected RFC 3339 date-time with an explicit timezone")
    normalized = value[:-1] + "+00:00" if value[-1] in "Zz" else value
    parsed = dt.datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timezone is required")
    return parsed


@dataclass(frozen=True)
class DomainContext:
    root: pathlib.Path
    descriptor: pathlib.Path
    config: dict
    domain_id: str
    declared: dict[str, pathlib.Path | None]
    as_of: dt.date


@dataclass
class CardState:
    cards: dict[str, dict]
    bodies: dict[str, str]
    digests: dict[str, str]
    paths: dict[str, str]
    active: set[str]
    interfaces_for: dict[str, list[dict]]


@dataclass
class LifecycleState:
    tombs: list[dict]
    tomb_by_id: dict[str, dict]
    redirect_by_from: dict[str, dict]
    active: set[str]

    def resolve_active_ref(self, reference: str) -> str | None:
        if reference in self.active:
            return reference
        redirect = self.redirect_by_from.get(reference)
        if redirect is None:
            return None
        target = redirect.get("to")
        return (
            target
            if isinstance(target, str)
            and target in self.active
            and target not in self.redirect_by_from
            else None
        )


def load_domain_phase(
    domain_dir: pathlib.Path,
    domain_validator: jsonschema.Draft202012Validator,
    as_of_override: dt.date | None,
    rep: Report,
) -> DomainContext | None:
    try:
        root = domain_dir.resolve()
    except (OSError, RuntimeError) as exc:
        rep.error(f"{domain_dir}: could not resolve domain directory: {exc}")
        return None
    descriptor = domain_path(root, "domain.yaml", "domain descriptor", rep)
    if not require_path(descriptor, "file", "domain descriptor", rep):
        return None
    assert descriptor is not None
    domain_text = read_utf8(descriptor, rep)
    if domain_text is None:
        return None
    config = read_yaml(domain_text, descriptor, rep)
    if not isinstance(config, dict):
        if config is not None:
            rep.error(f"{descriptor}: descriptor must be a YAML mapping")
        return None
    for error in schema_errors(domain_validator, config):
        rep.error(f"{descriptor}: {error}")
    domain_id = config.get("id", root.name)
    as_of = resolve_domain_as_of(config, descriptor, as_of_override, rep)
    if domain_id != root.name:
        rep.warn(f"{descriptor}: id {domain_id} differs from directory name {root.name}")

    declared: dict[str, pathlib.Path | None] = {}
    for field, kind in DECLARED_PATHS.items():
        path = domain_path(root, config.get(field), field, rep)
        declared[field] = path
        require_path(path, kind, field, rep)

    handbook_path = declared["handbook"]
    if handbook_path is not None and handbook_path.is_file():
        handbook_text = read_utf8(handbook_path, rep)
        if handbook_text is not None and not handbook_text.strip():
            rep.error(f"{handbook_path}: required handbook is empty")
    return DomainContext(root, descriptor, config, domain_id, declared, as_of)


def validate_registry_phase(
    context: DomainContext,
    registry_validator: jsonschema.Draft202012Validator,
    rep: Report,
) -> dict[str, dict]:
    registry_path = context.declared["source_registry"]
    registry: dict[str, dict] = {}
    artifact_contract_by_path: dict[str, str] = {}
    if registry_path is not None and registry_path.is_file():
        registry_text = read_utf8(registry_path, rep)
        loaded = read_yaml(registry_text, registry_path, rep) if registry_text is not None else None
        if not isinstance(loaded, dict):
            if loaded is not None:
                rep.error(f"{registry_path}: source registry must be a YAML mapping")
            loaded = {}
        for error in schema_errors(registry_validator, loaded):
            rep.error(f"{registry_path}: {error}")
        contracts = loaded.get("contracts", [])
        if not isinstance(contracts, list):
            contracts = []
        for contract in contracts:
            if not isinstance(contract, dict) or not isinstance(contract.get("id"), str):
                continue
            contract_id = contract["id"]
            if contract_id in registry:
                rep.error(f"{registry_path}: duplicate contract id {contract_id}")
            registry[contract_id] = contract
            provenance = contract.get("provenance")
            if not isinstance(provenance, dict):
                rep.error(f"{registry_path}: contract {contract_id} is missing provenance")
            else:
                captured_value = provenance.get("captured_on")
                if isinstance(captured_value, str):
                    try:
                        captured_on = dt.date.fromisoformat(captured_value)
                    except ValueError:
                        pass
                    else:
                        if captured_on > context.as_of:
                            rep.error(
                                f"{registry_path}: contract {contract_id} provenance.captured_on "
                                f"{captured_on} is after validation date {context.as_of}"
                            )

            if contract.get("kind") != "document-snapshot":
                continue
            artifact = contract.get("artifact")
            if not isinstance(artifact, dict):
                rep.error(f"{registry_path}: document-snapshot contract {contract_id} is missing artifact")
                continue
            artifact_value = artifact.get("path")
            artifact_path = domain_path(
                context.root,
                artifact_value,
                f"contract {contract_id} artifact.path",
                rep,
                owner=registry_path,
            )
            if artifact_path is None:
                continue
            if not isinstance(artifact_value, str) or not artifact_value.startswith("raw/snapshots/"):
                rep.error(
                    f"{registry_path}: document-snapshot contract {contract_id} "
                    "artifact.path must live under raw/snapshots/"
                )
                continue
            previous_contract = artifact_contract_by_path.get(artifact_value)
            if previous_contract is not None:
                rep.error(
                    f"{registry_path}: document-snapshot contracts {previous_contract} and "
                    f"{contract_id} share artifact.path {artifact_value}; paths must be unique"
                )
            else:
                artifact_contract_by_path[artifact_value] = contract_id
            if not require_path(artifact_path, "file", f"contract {contract_id} artifact", rep):
                continue
            expected_hash = artifact.get("sha256")
            if not isinstance(expected_hash, str):
                continue
            artifact_bytes = read_bytes(artifact_path, rep, f"contract {contract_id} artifact")
            if artifact_bytes is None:
                continue
            if not artifact_bytes:
                rep.error(f"{artifact_path}: contract {contract_id} artifact must not be empty")
                continue
            try:
                artifact_text = artifact_bytes.decode("utf-8")
            except UnicodeDecodeError as exc:
                rep.error(f"{artifact_path}: contract {contract_id} artifact must be UTF-8 Markdown: {exc}")
                continue
            if not artifact_text.strip():
                rep.error(f"{artifact_path}: contract {contract_id} artifact must contain non-blank Markdown")
                continue
            if hashlib.sha256(artifact_bytes).hexdigest() != expected_hash:
                rep.error(
                    f"{registry_path}: contract {contract_id} artifact.sha256 does not match "
                    f"{artifact_path.relative_to(context.root).as_posix()}"
                )

    if registry_path is not None:
        audit_snapshot_directory(context.root, registry_path, set(artifact_contract_by_path), rep)
    return registry


def validate_cards_phase(
    context: DomainContext,
    registry: dict[str, dict],
    card_validator: jsonschema.Draft202012Validator,
    rep: Report,
) -> CardState:
    domain_dir = context.root
    domain_id = context.domain_id
    as_of = context.as_of
    registry_path = context.declared["source_registry"]
    card_v = card_validator
    # 2. cards
    cards: dict[str, dict] = {}
    bodies: dict[str, str] = {}
    digests: dict[str, str] = {}
    paths: dict[str, str] = {}
    wiki_dir = domain_path(domain_dir, "wiki", "wiki card directory", rep)
    if not require_path(wiki_dir, "directory", "wiki card", rep):
        wiki_dir = None
    card_paths = discover_card_paths(wiki_dir, rep) if wiki_dir is not None else []
    for path in card_paths:
        relative_path = path.relative_to(domain_dir).as_posix()
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
        paths[cid] = relative_path

    active = {cid for cid, c in cards.items() if c["status"] != "deprecated"}
    referenced_contracts: set[str] = set()
    interfaces_for = active_interfaces_by_canonical(cards)

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
                elif kind != "supersedes" and not ref_exists(ref):
                    rep.error(f"{p}: relations.{kind} -> {ref} does not exist")
                elif kind in {"depends_on", "related"} and ref not in active and cid in active:
                    rep.error(f"{p}: active card relations.{kind} points to deprecated card {ref}")
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
            elif cards[ref]["knowledge_role"] != "canonical":
                rep.error(f"{p}: index_to -> {ref} is not a canonical card")
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
            ruled_on = dt.date.fromisoformat(str(arb["ruled_on"]))
            if ruled_on > as_of:
                rep.error(f"{p}: arbitration.ruled_on {ruled_on} is after validation date {as_of}")
        ret = card.get("retirement")
        if ret and ret.get("target_card"):
            tgt = ret["target_card"]
            if not ref_exists(tgt):
                rep.error(f"{p}: retirement.target_card -> {tgt} does not exist")
            elif tgt not in active:
                rep.error(f"{p}: retirement.target_card -> {tgt} is itself deprecated")
            elif cid not in cards[tgt]["relations"]["supersedes"]:
                rep.error(f"{p}: {tgt} must list {cid} in relations.supersedes (reciprocity)")
        if ret:
            retired_on = dt.date.fromisoformat(str(ret["retired_on"]))
            if retired_on > as_of:
                rep.error(f"{p}: retirement.retired_on {retired_on} is after validation date {as_of}")
        for ref in rel["supersedes"]:
            if ref_exists(ref):
                other = cards[ref]
                if other["status"] != "deprecated":
                    rep.error(f"{p}: supersedes {ref} but that card is not deprecated")
                elif other.get("retirement", {}).get("target_card") != cid:
                    rep.error(f"{p}: supersedes {ref} but its retirement.target_card is not {cid}")

        if card["type"] == "playbook" and card["procedure"]["executable"]:
            dependency_cards = [cards[ref] for ref in rel["depends_on"] if ref in active]
            interface_dependencies = [
                dependency for dependency in dependency_cards if dependency["knowledge_role"] == "interface"
            ]
            metric_dependencies = [
                dependency for dependency in dependency_cards if dependency["type"] == "metric"
            ]
            if not interface_dependencies:
                rep.error(f"{p}: executable playbook must depend on at least one active interface card")
            for metric_dependency in metric_dependencies:
                needed_fields = (
                    formula_identifiers(metric_dependency.get("definition", {}).get("formula", ""))
                    | execution_fields(metric_dependency)
                )
                if not any(
                    metric_dependency["id"] in interface.get("canonical_cards", [])
                    and needed_fields.issubset(
                        {
                            str(field).lower()
                            for field in interface.get("query_interface", {}).get("logical_fields", [])
                        }
                    )
                    for interface in interface_dependencies
                ):
                    rep.error(
                        f"{p}: executable playbook metric dependency {metric_dependency['id']} "
                        "is not bridged by any interface dependency with complete formula and "
                        "execution field coverage"
                    )

        # Execution contracts contain graph references and interface-local fields
        # that JSON Schema alone cannot resolve.
        contract = card.get("execution_contract")
        if isinstance(contract, dict):
            required_values = [
                field.lower() for field in contract.get("required_fields", []) if isinstance(field, str)
            ]
            required_fields = set(required_values)
            if len(required_fields) != len(required_values):
                rep.error(f"{p}: execution_contract.required_fields contains duplicate field names")
            formula_fields = formula_identifiers(card.get("definition", {}).get("formula", ""))
            redundant_required = required_fields & (formula_fields | execution_filter_fields(card))
            if redundant_required:
                rep.error(
                    f"{p}: execution_contract.required_fields repeats formula or filter fields "
                    f"{sorted(redundant_required)}"
                )
            by_layer = contract.get("by_layer", [])
            always_signatures = {
                signature
                for item in contract.get("always_filter", [])
                if (signature := filter_signature(item)) is not None
            }
            seen_layers: set[str] = set()
            if isinstance(by_layer, list):
                for layer_index, layer in enumerate(by_layer, 1):
                    if not isinstance(layer, dict):
                        continue
                    layer_name = layer.get("layer")
                    if isinstance(layer_name, str):
                        normalized_layer = layer_name.strip().lower()
                        if normalized_layer in seen_layers:
                            rep.error(f"{p}: duplicate execution_contract.by_layer name {layer_name!r}")
                        seen_layers.add(normalized_layer)
                    required_signatures = {
                        signature
                        for item in layer.get("require_filter", [])
                        if (signature := filter_signature(item)) is not None
                    }
                    forbidden_signatures = {
                        signature
                        for item in layer.get("forbid_filter", [])
                        if (signature := filter_signature(item)) is not None
                    }
                    for conflict in sorted(forbidden_signatures & (required_signatures | always_signatures)):
                        rep.error(
                            f"{p}: execution_contract.by_layer[{layer_index}] both requires and forbids "
                            f"filter {conflict[0]} {conflict[1]} {conflict[2]}"
                        )
                    metrics = layer.get("metrics", [])
                    if not isinstance(metrics, list):
                        continue
                    for metric_ref in metrics:
                        if not isinstance(metric_ref, str):
                            continue
                        if metric_ref not in active or cards[metric_ref]["type"] != "metric":
                            rep.error(
                                f"{p}: execution_contract.by_layer[{layer_index}].metrics -> "
                                f"{metric_ref} is not an active metric card"
                            )
                        elif (
                            card["knowledge_role"] == "interface"
                            and metric_ref not in card.get("canonical_cards", [])
                        ):
                            rep.error(
                                f"{p}: execution_contract.by_layer[{layer_index}].metrics -> "
                                f"{metric_ref} is not bridged by this interface's canonical_cards"
                            )
            if card["knowledge_role"] == "interface" and isinstance(card.get("query_interface"), dict):
                logical_fields = {
                    str(field).lower()
                    for field in card["query_interface"].get("logical_fields", [])
                    if isinstance(field, str)
                }
                missing_fields = execution_fields(card) - logical_fields
                if missing_fields:
                    rep.error(
                        f"{p}: interface execution contract uses fields {sorted(missing_fields)} "
                        "not present in query_interface.logical_fields"
                    )

        # registry resolution
        for ref in card.get("source_refs", []):
            referenced_contracts.add(ref)
            if ref not in registry:
                rep.error(f"{p}: source_refs -> {ref} not in registry")
        for ev in card["evidence"]:
            referenced_contracts.add(ev["ref"])
            if ev["ref"] not in registry:
                rep.error(f"{p}: evidence.ref -> {ev['ref']} not in registry")
            elif registry[ev["ref"]].get("kind") != ev["kind"]:
                rep.error(
                    f"{p}: evidence {ev['ref']} kind {ev['kind']} differs from registry kind "
                    f"{registry[ev['ref']].get('kind')!r}"
                )
            if ev["ref"] in registry and cid in active:
                provenance = registry[ev["ref"]].get("provenance")
                captured_value = provenance.get("captured_on") if isinstance(provenance, dict) else None
                if isinstance(captured_value, str):
                    try:
                        captured_on = dt.date.fromisoformat(captured_value)
                    except ValueError:
                        pass  # Registry diagnostics carry the malformed date.
                    else:
                        checked_at = dt.date.fromisoformat(str(ev["checked_at"]))
                        if checked_at < captured_on:
                            rep.error(
                                f"{p}: active-card evidence {ev['ref']} checked_at {checked_at} is before "
                                f"registry provenance.captured_on {captured_on}"
                            )
        vd = card.get("value_domain")
        if vd:
            referenced_contracts.add(vd["source_ref"])
            if vd["source_ref"] not in registry:
                rep.error(f"{p}: value_domain.source_ref -> {vd['source_ref']} not in registry")
            captured_value = vd.get("captured_on")
            if isinstance(captured_value, str):
                captured_on = dt.date.fromisoformat(captured_value)
                if captured_on > as_of:
                    rep.error(f"{p}: value_domain.captured_on {captured_on} is after validation date {as_of}")
                source_contract = registry.get(vd["source_ref"])
                provenance = source_contract.get("provenance") if isinstance(source_contract, dict) else None
                if isinstance(provenance, dict) and captured_value != provenance.get("captured_on"):
                    rep.error(
                        f"{p}: value_domain.captured_on disagrees with registry provenance "
                        f"({captured_value!r} != {provenance.get('captured_on')!r})"
                    )
            seen_values: set[str] = set()
            for value_row in vd.get("values", []):
                value = value_row["value"]
                if value in seen_values:
                    rep.error(f"{p}: duplicate value_domain value {value!r}")
                seen_values.add(value)
        snap = card.get("snapshot")
        if snap:
            referenced_contracts.add(snap["registry_ref"])
            if snap["registry_ref"] not in registry:
                rep.error(f"{p}: snapshot.registry_ref -> {snap['registry_ref']} not in registry")
            else:
                snapshot_contract = registry[snap["registry_ref"]]
                if snapshot_contract.get("kind") != "document-snapshot":
                    rep.error(
                        f"{p}: snapshot.registry_ref -> {snap['registry_ref']} must be a document-snapshot contract"
                    )
                provenance = snapshot_contract.get("provenance")
                if isinstance(provenance, dict):
                    for field in ("captured_on", "trust"):
                        if snap.get(field) != provenance.get(field):
                            rep.error(
                                f"{p}: snapshot.{field} disagrees with registry provenance "
                                f"({snap.get(field)!r} != {provenance.get(field)!r})"
                            )

        # freshness
        fr = card["freshness"]
        lv = dt.date.fromisoformat(str(fr["last_verified"]))
        ra = dt.date.fromisoformat(str(fr["review_after"]))
        if lv > as_of:
            rep.error(f"{p}: freshness.last_verified {lv} is after validation date {as_of}")
        if ra <= lv:
            rep.error(f"{p}: freshness.review_after must be after last_verified")
        for ev in card["evidence"]:
            if dt.date.fromisoformat(str(ev["checked_at"])) > lv:
                rep.error(f"{p}: evidence checked_at {ev['checked_at']} is after last_verified {lv}")
        if cid in active and ra <= as_of:
            rep.warn(f"{p}: review window expired on {ra}; effective status is stale")
        if card["status"] == "certified":
            approved_semantic = False
            for evidence in card["evidence"]:
                contract_ref = registry.get(evidence["ref"])
                provenance = contract_ref.get("provenance") if isinstance(contract_ref, dict) else None
                if (
                    evidence["kind"] == "semantic-decision"
                    and isinstance(provenance, dict)
                    and provenance.get("state_at_capture") == "approved"
                    and provenance.get("trust") == "authoritative"
                ):
                    approved_semantic = True
                    break
            if not approved_semantic:
                rep.error(
                    f"{p}: certified card needs an approved, authoritative semantic-decision evidence contract"
                )

        # brief
        heading, brief = first_section(bodies[cid])
        if not heading:
            rep.error(f"{p}: body needs at least one '## ' section; the first one compiles into the brief")
        else:
            if not brief:
                rep.error(f"{p}: first section '{heading}' must contain a non-empty compiled brief")
            if len(brief) > BRIEF_LIMIT:
                rep.error(f"{p}: first section '{heading}' is {len(brief)} chars; brief limit is {BRIEF_LIMIT}")
            if re.search(r":\s*$", brief, re.M):
                rep.warn(f"{p}: first section has a line ending in ':' (dangling lead-in is not self-contained)")
        for alias in card.get("aliases", []):
            if len(alias.split()) >= 6:
                rep.warn(f"{p}: alias '{alias}' looks like a phrase, not a noun surface")

        # formula coverage
        if card["type"] == "metric" and cid in active:
            needed = formula_identifiers(card["definition"]["formula"]) | execution_fields(card)
            bridges = interfaces_for.get(cid, [])
            if not bridges:
                rep.info(f"{p}: no interface bridges to this metric; compiles as knowledge")
            else:
                incomplete: list[str] = []
                for b in bridges:
                    fields = {str(x).lower() for x in b["query_interface"]["logical_fields"]}
                    missing = needed - fields
                    if not missing:
                        break
                    incomplete.append(f"{b['id']} missing {sorted(missing)}")
                else:
                    rep.error(
                        f"{p}: no single interface bridge covers formula and execution fields {sorted(needed)}; "
                        + "; ".join(incomplete)
                    )

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

    return CardState(cards, bodies, digests, paths, active, interfaces_for)

def validate_lifecycle_phase(
    context: DomainContext,
    cards: dict[str, dict],
    active: set[str],
    paths: dict[str, str],
    digests: dict[str, str],
    tomb_validator: jsonschema.Draft202012Validator,
    redirect_validator: jsonschema.Draft202012Validator,
    rep: Report,
) -> LifecycleState:
    declared = context.declared
    as_of = context.as_of
    tomb_v = tomb_validator
    redirect_v = redirect_validator
    # tombstones and redirects
    tomb_path = declared["retirements"]
    tombs = read_jsonl(tomb_path, rep) if tomb_path is not None else []
    tomb_by_id: dict[str, dict] = {}
    tomb_lines: dict[str, int] = {}
    for n, row in enumerate(tombs, 1):
        tomb_errors = schema_errors(tomb_v, row)
        for e in tomb_errors:
            rep.error(f"{tomb_path}:{n}: {e}")
        if tomb_errors:
            continue
        tid = row.get("id")
        if not isinstance(tid, str):
            continue
        if tid in tomb_by_id:
            rep.error(f"{tomb_path}:{n}: duplicate tombstone id {tid} (first at line {tomb_lines[tid]})")
            continue
        tomb_by_id[tid] = row
        tomb_lines[tid] = n

        tgt = row.get("target_card")
        if tgt and tgt not in active:
            rep.error(f"{tomb_path}:{n}: target_card {tgt} is not an active card")
        if tid in active:
            rep.error(f"{tomb_path}:{n}: tombstone id {tid} is still an active card")
        if row.get("deleted_on") and tid in cards:
            rep.error(f"{tomb_path}:{n}: tombstone says deleted but the card file still exists")
        if not row.get("deleted_on") and tid not in cards:
            rep.error(f"{tomb_path}:{n}: card file is gone but deleted_on is missing")
        retired_on = dt.date.fromisoformat(row["retired_on"])
        if retired_on > as_of:
            rep.error(f"{tomb_path}:{n}: retired_on {retired_on} is after validation date {as_of}")
        if isinstance(row.get("deleted_on"), str):
            deleted_on = dt.date.fromisoformat(row["deleted_on"])
            if deleted_on < retired_on:
                rep.error(f"{tomb_path}:{n}: deleted_on must be on or after retired_on")
            if deleted_on > as_of:
                rep.error(f"{tomb_path}:{n}: deleted_on {deleted_on} is after validation date {as_of}")
        if tid in cards:
            if digests[tid] != row.get("final_sha256"):
                rep.error(f"{tomb_path}:{n}: final_sha256 does not match the current card file")
            retirement = cards[tid].get("retirement")
            if not isinstance(retirement, dict):
                rep.error(f"{tomb_path}:{n}: card {tid} has no retirement block")
            else:
                for card_field, tomb_field in (
                    ("outcome", "outcome"),
                    ("target_card", "target_card"),
                    ("reason", "reason"),
                    ("retired_on", "retired_on"),
                ):
                    if retirement.get(card_field) != row.get(tomb_field):
                        rep.error(
                            f"{tomb_path}:{n}: {tid} {tomb_field} disagrees with card.retirement "
                            f"({row.get(tomb_field)!r} != {retirement.get(card_field)!r})"
                        )
    tomb_ids = set(tomb_by_id)
    for cid in cards:
        if cards[cid]["status"] == "deprecated" and cid not in tomb_ids:
            name = tomb_path.name if tomb_path is not None else "retirements.jsonl"
            rep.error(f"{paths[cid]}: deprecated card has no tombstone in {name}")
        for superseded_id in cards[cid]["relations"]["supersedes"]:
            if superseded_id in cards:
                continue  # Existing-card reciprocity was checked above.
            tomb = tomb_by_id.get(superseded_id)
            if tomb is None:
                rep.error(f"{paths[cid]}: relations.supersedes -> {superseded_id} is neither a deprecated card nor a tombstone")
            elif tomb.get("target_card") != cid:
                rep.error(
                    f"{paths[cid]}: supersedes tombstoned id {superseded_id} but its target_card is not {cid}"
                )

    for tid, tomb in tomb_by_id.items():
        if tomb.get("outcome") not in {"replaced", "merged"}:
            continue
        target = tomb.get("target_card")
        if target not in active:
            # The target error above is the primary diagnostic.
            continue
        if tid not in cards[target]["relations"]["supersedes"]:
            rep.error(
                f"{tomb_path}:{tomb_lines[tid]}: active target {target} must list {tid} "
                "in relations.supersedes"
            )

    redirect_path = declared["redirects"]
    redirects_obj: dict = {}
    if redirect_path is not None and redirect_path.is_file():
        redirect_text = read_utf8(redirect_path, rep)
        loaded_redirects = parse_json(redirect_text, redirect_path, rep) if redirect_text is not None else None
        if isinstance(loaded_redirects, dict):
            redirects_obj = loaded_redirects
        elif loaded_redirects is not None:
            rep.error(f"{redirect_path}: redirects document must be a JSON object")
    for e in schema_errors(redirect_v, redirects_obj):
        rep.error(f"{redirect_path}: {e}")

    redirect_by_from: dict[str, dict] = {}
    redirect_rows = redirects_obj.get("redirects", [])
    if not isinstance(redirect_rows, list):
        redirect_rows = []
    for n, row in enumerate(redirect_rows, 1):
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("from"), str)
            or not isinstance(row.get("to"), str)
        ):
            continue
        source = row["from"]
        if source in redirect_by_from:
            rep.error(f"{redirect_path}: duplicate redirect from {source} at row {n}")
            continue
        redirect_by_from[source] = row
        if source in active:
            rep.error(f"{redirect_path}: redirect from active card {source}")
        if source not in tomb_by_id:
            rep.error(f"{redirect_path}: redirect from {source} has no tombstone")
        since_value = row.get("since")
        if isinstance(since_value, str):
            try:
                since = dt.date.fromisoformat(since_value)
            except ValueError:
                pass  # Redirect schema diagnostics carry the malformed date.
            else:
                if since > as_of:
                    rep.error(f"{redirect_path}: redirect from {source} starts after validation date {as_of}")

    # Redirects are deliberately one-hop: old ids resolve directly to an active card.
    reported_chains: set[tuple[str, ...]] = set()
    for source in redirect_by_from:
        chain: list[str] = []
        current = source
        while current in redirect_by_from:
            if current in chain:
                cycle = tuple(chain[chain.index(current):] + [current])
                if cycle not in reported_chains:
                    rep.error(f"{redirect_path}: redirect cycle {' -> '.join(cycle)}")
                    reported_chains.add(cycle)
                current = ""
                break
            chain.append(current)
            current = redirect_by_from[current].get("to", "")
        if len(chain) > 1:
            signature = tuple(chain + ([current] if current else []))
            if signature not in reported_chains:
                rep.error(f"{redirect_path}: multi-hop redirect {' -> '.join(signature)}; redirects must point directly to active cards")
                reported_chains.add(signature)
        if current and current not in active:
            rep.error(f"{redirect_path}: redirect from {source} resolves to non-active card {current}")

    for tid, tomb in tomb_by_id.items():
        redirect = redirect_by_from.get(tid)
        target = tomb.get("target_card")
        if target:
            if redirect is None:
                rep.error(f"{redirect_path}: tombstoned id {tid} has no redirect")
                continue
            if redirect.get("to") != target:
                rep.error(f"{redirect_path}: {tid} target disagrees with tombstone ({redirect.get('to')!r} != {target!r})")
            if redirect.get("since") != tomb.get("retired_on"):
                rep.error(
                    f"{redirect_path}: {tid} since disagrees with tombstone.retired_on "
                    f"({redirect.get('since')!r} != {tomb.get('retired_on')!r})"
                )
        elif redirect is not None:
            rep.error(f"{redirect_path}: retired-without-replacement id {tid} must not redirect")

    return LifecycleState(tombs, tomb_by_id, redirect_by_from, active)


def validate_manifest_phase(
    context: DomainContext,
    cards: dict[str, dict],
    active: set[str],
    paths: dict[str, str],
    digests: dict[str, str],
    interfaces_for: dict[str, list[dict]],
    manifest_validator: jsonschema.Draft202012Validator,
    write_manifest: bool,
    rep: Report,
) -> tuple[pathlib.Path | None, str]:
    domain_dir = context.root
    as_of = context.as_of
    manifest_v = manifest_validator
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
    if not rows:
        rep.error(f"{domain_dir}: deterministic manifest must contain at least one active card")
    manifest_path = domain_path(domain_dir, "evals/manifest.expected.jsonl", "manifest fixture", rep)
    rendered = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows)
    if write_manifest:
        if manifest_path is not None and manifest_path.exists() and not manifest_path.is_file():
            rep.error(f"{manifest_path}: manifest target must be a file")
    elif require_nonempty_file(manifest_path, "manifest", rep):
        assert manifest_path is not None
        expected_manifest = read_jsonl(manifest_path, rep)
        for n, row in enumerate(expected_manifest, 1):
            for e in schema_errors(manifest_v, row):
                rep.error(f"{manifest_path}:{n}: {e}")
        manifest_text = read_utf8(manifest_path, rep)
        if manifest_text is not None and manifest_text != rendered:
            rep.error(f"{manifest_path}: differs from deterministic build; review and run --write-manifest")
        elif manifest_text is not None:
            rep.info(f"{manifest_path}: matches build ({len(rows)} rows)")

    return manifest_path, rendered


def validate_evals_phase(
    context: DomainContext,
    cards: dict[str, dict],
    lifecycle: LifecycleState,
    routing_validator: jsonschema.Draft202012Validator,
    golden_validator: jsonschema.Draft202012Validator,
    rep: Report,
) -> None:
    domain_dir = context.root
    as_of = context.as_of
    routing_v = routing_validator
    golden_v = golden_validator
    resolve_active_ref = lifecycle.resolve_active_ref
    # evals
    def check_eval(path: pathlib.Path | None, validator, card_fields: tuple[str, ...], routing: bool = False) -> None:
        if not require_nonempty_file(path, "routing" if routing else "golden", rep):
            return
        assert path is not None
        seen = set()
        for n, row in enumerate(read_jsonl(path, rep), 1):
            row_errors = schema_errors(validator, row)
            for e in row_errors:
                rep.error(f"{path}:{n}: {e}")
            if row_errors:
                continue
            if row.get("id") in seen:
                rep.error(f"{path}:{n}: duplicate eval id {row['id']}")
            seen.add(row.get("id"))
            for field in card_fields:
                resolved_seen: set[str] = set()
                for ref in row.get(field, []):
                    resolved = resolve_active_ref(ref)
                    if resolved is None:
                        rep.error(f"{path}:{n}: {field} -> {ref} does not resolve to an active card")
                    else:
                        if resolved in resolved_seen:
                            rep.error(
                                f"{path}:{n}: {field} contains multiple ids that resolve to {resolved}"
                            )
                        resolved_seen.add(resolved)
                        if field == "required_interfaces" and cards[resolved]["knowledge_role"] != "interface":
                            rep.error(f"{path}:{n}: required_interfaces -> {ref} does not resolve to an interface card")
            if routing:
                if not row.get("paraphrases"):
                    rep.error(f"{path}:{n}: routing paraphrases must be non-empty")
                if not row.get("negative_queries"):
                    rep.error(f"{path}:{n}: routing negative_queries must be non-empty")
                if row.get("max_rank") > row.get("cutoff"):
                    rep.error(
                        f"{path}:{n}: max_rank {row['max_rank']} must be less than or equal to cutoff {row['cutoff']}"
                    )
                if len(row.get("expected_cards", [])) > row.get("max_rank"):
                    rep.error(
                        f"{path}:{n}: max_rank {row['max_rank']} cannot contain all "
                        f"{len(row['expected_cards'])} expected_cards"
                    )
                positive_surfaces = {
                    " ".join(surface.casefold().split())
                    for surface in [row["question"], *row.get("paraphrases", [])]
                }
                negative_surfaces = {
                    " ".join(surface.casefold().split()) for surface in row.get("negative_queries", [])
                }
                for duplicate_surface in sorted(positive_surfaces & negative_surfaces):
                    rep.error(
                        f"{path}:{n}: positive and negative routing surfaces overlap: {duplicate_surface!r}"
                    )
                if row.get("execution_expectation") == "interface-locate" and not any(
                    (resolved := resolve_active_ref(ref)) is not None
                    and cards[resolved]["knowledge_role"] == "interface"
                    for ref in row.get("expected_cards", [])
                ):
                    rep.error(
                        f"{path}:{n}: interface-locate must include an active interface in expected_cards"
                    )
                if row.get("execution_expectation") == "executable-if-available":
                    expected_metrics: set[str] = set()
                    required_interfaces: set[str] = set()
                    for ref in row.get("expected_cards", []):
                        resolved = resolve_active_ref(ref)
                        if resolved is not None and cards[resolved]["type"] == "metric":
                            expected_metrics.add(resolved)
                    for ref in row.get("required_interfaces", []):
                        resolved = resolve_active_ref(ref)
                        if resolved is not None and cards[resolved]["knowledge_role"] == "interface":
                            required_interfaces.add(resolved)
                    if not expected_metrics:
                        rep.error(
                            f"{path}:{n}: executable-if-available must name at least one active metric "
                            "in expected_cards"
                        )
                    for metric_ref in sorted(expected_metrics):
                        metric_contract = cards[metric_ref].get("execution_contract")
                        if not isinstance(metric_contract, dict):
                            rep.error(
                                f"{path}:{n}: executable expected metric {metric_ref} has no "
                                "execution_contract"
                            )
                            continue
                        needed_fields = (
                            formula_identifiers(cards[metric_ref]["definition"]["formula"])
                            | execution_fields(cards[metric_ref])
                        )
                        if not any(
                            metric_ref in cards[interface_ref].get("canonical_cards", [])
                            and needed_fields.issubset(
                                {
                                    str(field).lower()
                                    for field in cards[interface_ref]["query_interface"]["logical_fields"]
                                }
                            )
                            for interface_ref in required_interfaces
                        ):
                            rep.error(
                                f"{path}:{n}: expected metric {metric_ref} has no complete "
                                "required_interface covering formula and execution fields"
                            )
                    for interface_ref in sorted(required_interfaces):
                        complete_targets = set()
                        interface_fields = {
                            str(field).lower()
                            for field in cards[interface_ref]["query_interface"]["logical_fields"]
                        }
                        for metric_ref in expected_metrics.intersection(
                            cards[interface_ref].get("canonical_cards", [])
                        ):
                            if isinstance(cards[metric_ref].get("execution_contract"), dict):
                                needed_fields = (
                                    formula_identifiers(cards[metric_ref]["definition"]["formula"])
                                    | execution_fields(cards[metric_ref])
                                )
                                if needed_fields.issubset(interface_fields):
                                    complete_targets.add(metric_ref)
                        if not complete_targets:
                            rep.error(
                                f"{path}:{n}: required interface {interface_ref} is not a complete bridge "
                                "for any expected metric"
                            )
            elif isinstance(row.get("measured_on"), str):
                measured_on = dt.date.fromisoformat(row["measured_on"])
                if measured_on > as_of:
                    rep.error(f"{path}:{n}: measured_on {measured_on} is after validation date {as_of}")
            if not routing:
                disclosures = {" ".join(value.casefold().split()) for value in row.get("must_disclose", [])}
                prohibitions = {" ".join(value.casefold().split()) for value in row.get("must_not", [])}
                for contradiction in sorted(disclosures & prohibitions):
                    rep.error(
                        f"{path}:{n}: the same text appears in must_disclose and must_not: {contradiction!r}"
                    )

    routing_path = domain_path(domain_dir, "evals/routing.jsonl", "routing fixture", rep)
    golden_path = domain_path(domain_dir, "evals/golden.jsonl", "golden fixture", rep)
    check_eval(routing_path, routing_v, ("expected_cards", "required_interfaces"), routing=True)
    check_eval(golden_path, golden_v, ("expected_cards",))

def validate_gaps_phase(
    context: DomainContext,
    lifecycle: LifecycleState,
    registry: dict[str, dict],
    gap_validator: jsonschema.Draft202012Validator,
    rep: Report,
) -> None:
    domain_dir = context.root
    as_of = context.as_of
    gap_v = gap_validator
    resolve_active_ref = lifecycle.resolve_active_ref
    gaps_path = domain_path(domain_dir, "gaps.example.jsonl", "gap fixture", rep)
    if gaps_path is not None and gaps_path.exists():
        if not gaps_path.is_file():
            rep.error(f"{gaps_path}: gap fixture must be a file")
        else:
            seen_gaps: set[str] = set()
            for n, row in enumerate(read_jsonl(gaps_path, rep), 1):
                row_errors = schema_errors(gap_v, row)
                for e in row_errors:
                    rep.error(f"{gaps_path}:{n}: {e}")
                if row_errors:
                    continue
                try:
                    registered_on = parse_rfc3339(row["registered_on"]).astimezone(dt.timezone.utc).date()
                except ValueError as exc:
                    rep.error(f"{gaps_path}:{n}: malformed registered_on: {exc}")
                    continue
                if registered_on > as_of:
                    rep.error(
                        f"{gaps_path}:{n}: registered_on {registered_on} is after validation date {as_of}"
                    )
                gap_id = row.get("gap_id")
                if isinstance(gap_id, str):
                    if gap_id in seen_gaps:
                        rep.error(f"{gaps_path}:{n}: duplicate gap id {gap_id}")
                    seen_gaps.add(gap_id)
                for search in row.get("searched", []):
                    if not isinstance(search, dict):
                        continue
                    resolved_top_cards: dict[str, str] = {}
                    for ref in search.get("top_cards", []):
                        resolved = resolve_active_ref(ref)
                        if resolved is None:
                            rep.error(f"{gaps_path}:{n}: searched.top_cards -> {ref} does not resolve to an active card")
                        elif resolved in resolved_top_cards:
                            rep.error(
                                f"{gaps_path}:{n}: searched.top_cards contains multiple ids that resolve "
                                f"to {resolved}: {resolved_top_cards[resolved]} and {ref}"
                            )
                        else:
                            resolved_top_cards[resolved] = ref
                resolved_candidates: dict[str, str] = {}
                for ref in row.get("candidate_cards", []):
                    resolved = resolve_active_ref(ref)
                    if resolved is None:
                        rep.error(f"{gaps_path}:{n}: candidate_cards -> {ref} does not resolve to an active card")
                    elif resolved in resolved_candidates:
                        rep.error(
                            f"{gaps_path}:{n}: candidate_cards contains multiple ids that resolve "
                            f"to {resolved}: {resolved_candidates[resolved]} and {ref}"
                        )
                    else:
                        resolved_candidates[resolved] = ref
                for claim in row.get("claims", []):
                    if not isinstance(claim, dict):
                        continue
                    evidence_ref = claim.get("evidence_ref")
                    if evidence_ref is not None and evidence_ref not in registry:
                        rep.error(f"{gaps_path}:{n}: claims.evidence_ref -> {evidence_ref} not in registry")
                    if claim.get("confidence") == "verified_live" and evidence_ref in registry:
                        evidence_contract = registry[evidence_ref]
                        if evidence_contract.get("kind") not in TECHNICAL_EVIDENCE_KINDS:
                            rep.error(
                                f"{gaps_path}:{n}: verified_live evidence {evidence_ref} must be technical, "
                                "not semantic-decision"
                            )
                        provenance = evidence_contract.get("provenance")
                        if not isinstance(provenance, dict):
                            continue  # Registry diagnostics carry the missing provenance.
                        if provenance.get("state_at_capture") != "live":
                            rep.error(
                                f"{gaps_path}:{n}: verified_live evidence {evidence_ref} must have "
                                "provenance.state_at_capture live"
                            )
                        if provenance.get("trust") != "authoritative":
                            rep.error(
                                f"{gaps_path}:{n}: verified_live evidence {evidence_ref} must have "
                                "authoritative provenance"
                            )
                        captured_value = provenance.get("captured_on")
                        if isinstance(captured_value, str):
                            try:
                                captured_on = dt.date.fromisoformat(captured_value)
                            except ValueError:
                                pass  # Registry diagnostics carry the malformed date.
                            else:
                                if captured_on > registered_on:
                                    rep.error(
                                        f"{gaps_path}:{n}: verified_live evidence {evidence_ref} was "
                                        f"captured on {captured_on}, after gap registration {registered_on}"
                                    )


def validate_domain(
    domain_dir: pathlib.Path,
    rep: Report,
    write_manifest: bool,
    as_of_override: dt.date | None,
) -> tuple[pathlib.Path, pathlib.Path, str] | None:
    loaded_validators = load_validators(rep)
    if loaded_validators is None:
        return None
    (
        card_v,
        domain_v,
        registry_v,
        tomb_v,
        redirect_v,
        manifest_v,
        routing_v,
        golden_v,
        gap_v,
    ) = loaded_validators

    context = load_domain_phase(domain_dir, domain_v, as_of_override, rep)
    if context is None:
        return None
    domain_dir = context.root
    registry = validate_registry_phase(context, registry_v, rep)
    card_state = validate_cards_phase(context, registry, card_v, rep)
    cards = card_state.cards
    digests = card_state.digests
    paths = card_state.paths
    active = card_state.active
    interfaces_for = card_state.interfaces_for
    lifecycle = validate_lifecycle_phase(
        context,
        cards,
        active,
        paths,
        digests,
        tomb_v,
        redirect_v,
        rep,
    )
    manifest_path, rendered = validate_manifest_phase(
        context,
        cards,
        active,
        paths,
        digests,
        interfaces_for,
        manifest_v,
        write_manifest,
        rep,
    )
    validate_evals_phase(
        context,
        cards,
        lifecycle,
        routing_v,
        golden_v,
        rep,
    )
    validate_gaps_phase(context, lifecycle, registry, gap_v, rep)
    rep.info(
        f"{domain_dir}: {len(cards)} cards ({len(active)} active), "
        f"{len(registry)} contracts, {len(lifecycle.tombs)} tombstones"
    )
    if write_manifest and manifest_path is not None:
        return domain_dir, manifest_path, rendered
    return None


def iso_date_argument(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"invalid ISO date {value!r}; expected YYYY-MM-DD") from exc


@dataclass(frozen=True)
class ValidationResult:
    report: Report

    @property
    def returncode(self) -> int:
        return 1 if self.report.errors else 0

    @property
    def stdout(self) -> str:
        return self.report.render()


def run_validation(
    domains: Iterable[str | pathlib.Path] | str | pathlib.Path,
    *,
    write_manifest: bool = False,
    as_of: dt.date | None = None,
) -> ValidationResult:
    """Validate one or more domains in process with a fresh report."""
    domain_values: Iterable[str | pathlib.Path]
    if isinstance(domains, (str, pathlib.Path)):
        domain_values = (domains,)
    else:
        domain_values = domains
    rep = Report()
    manifest_plans: list[tuple[pathlib.Path, pathlib.Path, str]] = []
    for domain in domain_values:
        plan = validate_domain(pathlib.Path(domain), rep, write_manifest, as_of)
        if plan is not None:
            manifest_plans.append(plan)
    if write_manifest:
        if rep.errors:
            rep.info("manifest write skipped because validation reported errors")
        else:
            for domain_dir, manifest_path, rendered in manifest_plans:
                atomic_write_manifest(domain_dir, manifest_path, rendered, rep)
                if rep.errors:
                    rep.info("remaining manifest writes skipped because a write failed")
                    break
    return ValidationResult(rep)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("domains", nargs="+", help="domain directories containing domain.yaml")
    parser.add_argument("--write-manifest", action="store_true", help="rewrite evals/manifest.expected.jsonl (reviewed change only)")
    parser.add_argument(
        "--as-of",
        type=iso_date_argument,
        default=None,
        help="override validation date (default: domain.fixture_as_of, then today)",
    )
    args = parser.parse_args(argv)
    result = run_validation(args.domains, write_manifest=args.write_manifest, as_of=args.as_of)
    result.report.dump()
    print(f"summary: {len(result.report.errors)} errors, {len(result.report.warnings)} warnings")
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())

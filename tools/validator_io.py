"""Trusted-repository IO and parsing for the reference validator.

The validator checks a reviewed fixture repository, not an adversarial upload
surface.  This module therefore keeps the boundaries that protect repository
paths and manifest writes while using ordinary file IO for trusted inputs.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import re
import stat
import sys
import tempfile

import jsonschema
import yaml
from referencing.exceptions import Unresolvable


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.infos: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def info(self, message: str) -> None:
        self.infos.append(message)

    def lines(self) -> list[str]:
        return [
            f"{prefix} {message}"
            for prefix, messages in (
                ("ERROR", self.errors),
                ("WARN ", self.warnings),
                ("INFO ", self.infos),
            )
            for message in messages
        ]

    def render(self) -> str:
        lines = [*self.lines(), f"summary: {len(self.errors)} errors, {len(self.warnings)} warnings"]
        return "\n".join(lines) + "\n"

    def dump(self) -> None:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        for line in self.lines():
            print(line.encode(encoding, errors="backslashreplace").decode(encoding))


class DuplicateKeyError(ValueError):
    """Raised when JSON contains a duplicate object member."""


class InvalidJSONConstantError(ValueError):
    """Raised when JSON uses the non-standard NaN or Infinity constants."""


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader,
    node: yaml.MappingNode,
    deep: bool = False,
) -> dict:
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in result
        except TypeError as exc:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found unhashable key {key!r}",
                key_node.start_mark,
            ) from exc
        if duplicate:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def unique_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"duplicate key {key!r}")
        result[key] = value
    return result


def reject_json_constant(value: str) -> object:
    raise InvalidJSONConstantError(f"non-standard constant {value} is forbidden")


def validate_data_tree(value: object, path: pathlib.Path | str, rep: Report, syntax: str) -> bool:
    """Check portable scalar constraints without policing YAML alias topology."""
    valid = True
    pending = [value]
    seen_containers: set[int] = set()
    while pending:
        item = pending.pop()
        if isinstance(item, str):
            if item and not item.strip():
                rep.error(f"{path}: invalid {syntax} string: whitespace-only strings are forbidden")
                valid = False
        elif isinstance(item, float) and not math.isfinite(item):
            rep.error(f"{path}: invalid {syntax} number: non-finite values are forbidden")
            valid = False
        elif isinstance(item, (dict, list)):
            identity = id(item)
            if identity in seen_containers:
                continue
            seen_containers.add(identity)
            if isinstance(item, dict):
                pending.extend(item.keys())
                pending.extend(item.values())
            else:
                pending.extend(item)
    return valid


def parse_json(text: str, path: pathlib.Path | str, rep: Report) -> object | None:
    try:
        value = json.loads(
            text,
            object_pairs_hook=unique_json_object,
            parse_constant=reject_json_constant,
        )
    except (ValueError, RecursionError) as exc:
        rep.error(f"{path}: invalid JSON: {exc}")
        return None
    return value if validate_data_tree(value, path, rep, "JSON") else None


def read_yaml(text: str, path: pathlib.Path, rep: Report) -> object | None:
    try:
        value = yaml.load(text, Loader=UniqueKeyLoader)
    except (yaml.YAMLError, ValueError, RecursionError) as exc:
        rep.error(f"{path}: invalid YAML: {exc}")
        return None
    return value if validate_data_tree(value, path, rep, "YAML") else None


def read_bytes(path: pathlib.Path, rep: Report, label: str) -> bytes | None:
    try:
        return path.read_bytes()
    except OSError as exc:
        rep.error(f"{path}: could not read {label}: {exc}")
        return None


def read_utf8(path: pathlib.Path, rep: Report) -> str | None:
    raw = read_bytes(path, rep, "text file")
    if raw is None:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeError as exc:
        rep.error(f"{path}: could not read UTF-8 text: {exc}")
        return None


def domain_path(
    domain_dir: pathlib.Path,
    value: object,
    label: str,
    rep: Report,
    owner: pathlib.Path | None = None,
) -> pathlib.Path | None:
    """Return a lexical domain-relative path whose resolved target stays inside the domain."""
    owner = owner or (domain_dir / "domain.yaml")
    if not isinstance(value, str) or not value.strip():
        rep.error(f"{owner}: {label} must be a non-empty relative path")
        return None
    relative = pathlib.Path(value)
    if relative.is_absolute():
        rep.error(f"{owner}: {label} must be relative, got {value!r}")
        return None
    if ".." in relative.parts:
        rep.error(f"{owner}: {label} must stay inside the domain, got {value!r}")
        return None
    try:
        root = domain_dir.resolve()
        lexical = root / relative
        lexical.resolve(strict=False).relative_to(root)
    except (OSError, RuntimeError, ValueError) as exc:
        rep.error(f"{owner}: {label} resolves outside the domain or is invalid: {exc}")
        return None
    return lexical


def require_path(path: pathlib.Path | None, kind: str, label: str, rep: Report) -> bool:
    if path is None:
        return False
    if not path.exists():
        rep.error(f"{path}: required {label} {kind} is missing")
        return False
    if kind == "file" and not path.is_file():
        rep.error(f"{path}: required {label} must be a file")
        return False
    if kind == "directory" and not path.is_dir():
        rep.error(f"{path}: required {label} must be a directory")
        return False
    return True


def require_nonempty_file(path: pathlib.Path | None, label: str, rep: Report) -> bool:
    if not require_path(path, "file", label, rep):
        return False
    assert path is not None
    text = read_utf8(path, rep)
    if text is None:
        return False
    if not text.strip():
        rep.error(f"{path}: required {label} fixture is empty")
        return False
    return True


def local_schema_reference_errors(schema: dict) -> list[str]:
    errors: list[str] = []

    def resolve_pointer(reference: str) -> bool:
        if not reference.startswith("#/"):
            return False
        current: object = schema
        for raw_token in reference[2:].split("/"):
            if re.search(r"~(?:[^01]|$)", raw_token):
                return False
            token = raw_token.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict) and token in current:
                current = current[token]
            elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
                current = current[int(token)]
            else:
                return False
        return True

    def walk(item: object, location: str = "$") -> None:
        if isinstance(item, dict):
            reference = item.get("$ref")
            if reference is not None and (not isinstance(reference, str) or not resolve_pointer(reference)):
                errors.append(f"unresolvable or non-local $ref at {location}: {reference!r}")
            for key, child in item.items():
                walk(child, f"{location}.{key}")
        elif isinstance(item, list):
            for index, child in enumerate(item):
                walk(child, f"{location}[{index}]")

    walk(schema)
    return errors


def load_schema(
    schema_dir: pathlib.Path,
    name: str,
    rep: Report,
) -> jsonschema.Draft202012Validator | None:
    path = schema_dir / name
    text = read_utf8(path, rep)
    if text is None:
        return None
    error_count = len(rep.errors)
    schema = parse_json(text, path, rep)
    if not isinstance(schema, dict):
        if len(rep.errors) == error_count:
            rep.error(f"{path}: schema root must be a JSON object")
        return None
    cls = jsonschema.Draft202012Validator
    try:
        cls.check_schema(schema)
    except jsonschema.SchemaError as exc:
        rep.error(f"{path}: invalid Draft 2020-12 schema: {exc.message}")
        return None
    reference_errors = local_schema_reference_errors(schema)
    if reference_errors:
        for error in reference_errors:
            rep.error(f"{path}: {error}")
        return None
    return cls(schema, format_checker=cls.FORMAT_CHECKER)


def schema_errors(validator: jsonschema.Draft202012Validator, value: object) -> list[str]:
    try:
        return [
            f"{'/'.join(str(part) for part in error.absolute_path) or '<root>'}: {error.message}"
            for error in validator.iter_errors(value)
        ]
    except (Unresolvable, RecursionError) as exc:
        return [f"<schema>: schema evaluation failed: {exc}"]


def read_card(path: pathlib.Path, rep: Report) -> tuple[dict | None, str, str]:
    raw = read_bytes(path, rep, "card")
    if raw is None:
        return None, "", ""
    if b"\r\n" in raw:
        rep.warn(f"{path}: CRLF line endings normalized to LF for hashing")
        raw = raw.replace(b"\r\n", b"\n")
    if not raw.endswith(b"\n"):
        rep.error(f"{path}: file must end with a newline (hash contract)")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        rep.error(f"{path}: card must be UTF-8: {exc}")
        return None, "", digest
    if not text.startswith("---\n"):
        rep.error(f"{path}: missing frontmatter")
        return None, "", digest
    try:
        _, frontmatter, body = text.split("---\n", 2)
    except ValueError:
        rep.error(f"{path}: unterminated frontmatter")
        return None, "", digest
    parsed = read_yaml(frontmatter, path, rep)
    if not isinstance(parsed, dict):
        if parsed is not None:
            rep.error(f"{path}: frontmatter must be a YAML mapping")
        return None, body, digest
    return parsed, body, digest


def discover_card_paths(wiki_dir: pathlib.Path, rep: Report) -> list[pathlib.Path]:
    try:
        return sorted(path for path in wiki_dir.rglob("*.md") if path.is_file())
    except OSError as exc:
        rep.error(f"{wiki_dir}: could not enumerate wiki card directory: {exc}")
        return []


def audit_snapshot_directory(
    domain_dir: pathlib.Path,
    registry_path: pathlib.Path,
    registered_artifacts: set[str],
    rep: Report,
) -> None:
    snapshot_dir = domain_path(
        domain_dir,
        "raw/snapshots",
        "managed snapshot directory",
        rep,
        owner=registry_path,
    )
    if snapshot_dir is None or not snapshot_dir.exists():
        return
    if not snapshot_dir.is_dir():
        rep.error(f"{snapshot_dir}: managed snapshot path must be a directory")
        return
    try:
        entries = sorted(snapshot_dir.iterdir())
    except OSError as exc:
        rep.error(f"{snapshot_dir}: could not enumerate managed snapshots: {exc}")
        return
    for path in entries:
        relative = path.relative_to(domain_dir).as_posix()
        if path.is_dir():
            rep.error(f"{path}: managed snapshots must live directly under raw/snapshots/")
        elif not path.is_file():
            rep.error(f"{path}: managed snapshot must be a file")
        elif relative not in registered_artifacts:
            rep.error(f"{path}: unregistered managed snapshot; add one document-snapshot contract or remove the file")


def read_jsonl(path: pathlib.Path, rep: Report) -> list[dict]:
    if not path.exists():
        return []
    text = read_utf8(path, rep)
    if text is None:
        return []
    rows: list[dict] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        label = f"{path}:{line_number}"
        value = parse_json(line, label, rep)
        if value is None:
            continue
        if not isinstance(value, dict):
            rep.error(f"{label}: JSONL row must be an object, got {type(value).__name__}")
            continue
        rows.append(value)
    return rows


def atomic_write_manifest(
    domain_dir: pathlib.Path,
    manifest_path: pathlib.Path,
    rendered: str,
    rep: Report,
) -> None:
    try:
        relative = manifest_path.relative_to(domain_dir).as_posix()
    except ValueError:
        rep.error(f"{manifest_path}: manifest target must stay inside the domain")
        return
    checked = domain_path(domain_dir, relative, "manifest fixture", rep)
    if checked is None or checked != manifest_path:
        return
    if not manifest_path.parent.is_dir():
        rep.error(f"{manifest_path}: parent directory is missing")
        return

    descriptor = -1
    temporary: pathlib.Path | None = None
    try:
        mode = stat.S_IMODE(manifest_path.stat().st_mode) if manifest_path.exists() else 0o644
        descriptor, name = tempfile.mkstemp(prefix=f".{manifest_path.name}.", dir=manifest_path.parent)
        temporary = pathlib.Path(name)
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = -1
            os.fchmod(handle.fileno(), mode)
            handle.write(rendered)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, manifest_path)
        temporary = None
        rep.info(f"{manifest_path}: written atomically ({rendered.count(chr(10))} rows)")
    except (OSError, UnicodeError) as exc:
        rep.error(f"{manifest_path}: atomic write failed: {exc}")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

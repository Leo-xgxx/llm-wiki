from __future__ import annotations

import copy
import json
import pathlib
import re
import unittest
from urllib.parse import unquote

import jsonschema


ROOT = pathlib.Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"
EXAMPLE = ROOT / "examples" / "acme-analytics"
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def load_json(path: pathlib.Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class RepositoryContractTests(unittest.TestCase):
    def test_all_nine_schemas_are_valid_draft_2020_12(self) -> None:
        paths = sorted(SCHEMA_DIR.glob("*.schema.json"))
        self.assertEqual(len(paths), 9, [path.name for path in paths])
        for path in paths:
            with self.subTest(schema=path.name):
                jsonschema.Draft202012Validator.check_schema(load_json(path))

    def test_all_markdown_relative_links_resolve(self) -> None:
        broken: list[str] = []
        for source in sorted(ROOT.rglob("*.md")):
            for raw_target in LINK_RE.findall(source.read_text(encoding="utf-8")):
                target = raw_target.strip()
                if target.startswith("<") and target.endswith(">"):
                    target = target[1:-1]
                else:
                    target = target.split(maxsplit=1)[0]
                target = unquote(target.split("#", 1)[0].split("?", 1)[0])
                if not target or target.startswith(("http://", "https://", "mailto:", "/")):
                    continue
                destination = source.parent / target
                if not destination.exists():
                    broken.append(f"{source.relative_to(ROOT)} -> {raw_target}")
        self.assertEqual(broken, [])

    def test_reference_routing_golden_and_gap_rows_validate(self) -> None:
        fixtures = (
            ("routing-eval.schema.json", EXAMPLE / "evals" / "routing.jsonl"),
            ("golden-question.schema.json", EXAMPLE / "evals" / "golden.jsonl"),
            ("gap.schema.json", EXAMPLE / "gaps.example.jsonl"),
        )
        for schema_name, fixture in fixtures:
            schema = load_json(SCHEMA_DIR / schema_name)
            validator = jsonschema.Draft202012Validator(
                schema,
                format_checker=jsonschema.Draft202012Validator.FORMAT_CHECKER,
            )
            for line_number, row in enumerate(load_jsonl(fixture), 1):
                with self.subTest(fixture=fixture.name, line=line_number):
                    errors = sorted(validator.iter_errors(row), key=lambda error: list(error.absolute_path))
                    self.assertEqual([error.message for error in errors], [])

    def test_numeric_tolerance_golden_requires_numeric_expected(self) -> None:
        schema = load_json(SCHEMA_DIR / "golden-question.schema.json")
        validator = jsonschema.Draft202012Validator(schema)
        row = copy.deepcopy(load_jsonl(EXAMPLE / "evals" / "golden.jsonl")[0])
        row.update({
            "answer_type": "numeric",
            "scoring_method": "tolerance",
            "tolerance": 0.01,
            "expected": "not a numeric target",
        })
        self.assertTrue(list(validator.iter_errors(row)))

    def test_verified_live_gap_claim_requires_evidence_reference(self) -> None:
        schema = load_json(SCHEMA_DIR / "gap.schema.json")
        validator = jsonschema.Draft202012Validator(schema)
        row = copy.deepcopy(load_jsonl(EXAMPLE / "gaps.example.jsonl")[0])
        row["claims"] = [{"text": "Synthetic observed claim", "confidence": "verified_live"}]
        self.assertTrue(list(validator.iter_errors(row)))

    def test_execution_required_fields_may_be_explicitly_empty(self) -> None:
        schema = load_json(SCHEMA_DIR / "card.schema.json")
        execution_contract = schema["$defs"]["execution_contract"]
        validator = jsonschema.Draft202012Validator(execution_contract)
        self.assertEqual(list(validator.iter_errors({"required_fields": []})), [])

    def test_filter_operator_value_shapes_are_machine_safe(self) -> None:
        schema = load_json(SCHEMA_DIR / "card.schema.json")
        validator = jsonschema.Draft202012Validator(schema["$defs"]["filter_item"])
        valid = (
            {"field": "status", "op": "in", "value": ["ready"], "reason": "contract"},
            {"field": "deleted_at", "op": "is_null", "value": None, "reason": "contract"},
            {"field": "amount", "op": "gte", "value": 0, "reason": "contract"},
        )
        invalid = (
            {"field": "status", "op": "in", "value": True, "reason": "contract"},
            {"field": "deleted_at", "op": "is_null", "value": "none", "reason": "contract"},
            {"field": "amount", "op": "gte", "value": [0], "reason": "contract"},
            {"field": "status", "op": "eq", "value": None, "reason": "contract"},
        )
        for item in valid:
            with self.subTest(valid=item):
                self.assertEqual(list(validator.iter_errors(item)), [])
        for item in invalid:
            with self.subTest(invalid=item):
                self.assertTrue(list(validator.iter_errors(item)))

    def test_non_numeric_goldens_require_text_and_tolerance_is_exclusive(self) -> None:
        schema = load_json(SCHEMA_DIR / "golden-question.schema.json")
        validator = jsonschema.Draft202012Validator(schema)
        row = copy.deepcopy(load_jsonl(EXAMPLE / "evals" / "golden.jsonl")[0])
        row["expected"] = 123
        self.assertTrue(list(validator.iter_errors(row)))

        row = copy.deepcopy(load_jsonl(EXAMPLE / "evals" / "golden.jsonl")[0])
        row["tolerance"] = 0.1
        self.assertTrue(list(validator.iter_errors(row)))


if __name__ == "__main__":
    unittest.main()

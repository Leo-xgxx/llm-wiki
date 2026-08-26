from __future__ import annotations

import datetime as dt
import hashlib
import importlib.util
import json
import os
import pathlib
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

import yaml


ROOT = pathlib.Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate.py"
EXAMPLE = ROOT / "examples" / "acme-analytics"
AS_OF = "2026-08-26"


class ValidatorIntegrationTests(unittest.TestCase):
    maxDiff = None

    def copy_domain(self) -> pathlib.Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        domain = pathlib.Path(temporary.name) / "acme-analytics"
        shutil.copytree(EXAMPLE, domain, symlinks=True)
        return domain

    def run_validator(
        self,
        domain: pathlib.Path,
        *,
        write_manifest: bool = False,
        as_of: str = AS_OF,
    ) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(VALIDATOR), str(domain), "--as-of", as_of]
        if write_manifest:
            command.append("--write-manifest")
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=20,
        )

    def assert_invalid(self, result: subprocess.CompletedProcess[str], *fragments: str) -> None:
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertNotIn("Traceback", result.stdout, result.stdout)
        for fragment in fragments:
            self.assertIn(fragment, result.stdout)

    @staticmethod
    def replace_once(path: pathlib.Path, old: str, new: str) -> None:
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise AssertionError(f"fixture text not found in {path}: {old!r}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    @staticmethod
    def read_jsonl(path: pathlib.Path) -> list[dict]:
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @staticmethod
    def write_jsonl(path: pathlib.Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")

    def test_reference_domain_is_valid(self) -> None:
        result = self.run_validator(self.copy_domain())
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("summary: 0 errors, 0 warnings", result.stdout)

    def test_every_declared_path_rejects_absolute_values(self) -> None:
        for field in ("source_registry", "handbook", "retirements", "redirects", "changelog_dir"):
            with self.subTest(field=field):
                domain = self.copy_domain()
                descriptor = domain / "domain.yaml"
                text = descriptor.read_text(encoding="utf-8")
                text, replacements = re.subn(rf"(?m)^{field}: .+$", f"{field}: /tmp/not-allowed", text, count=1)
                self.assertEqual(replacements, 1)
                descriptor.write_text(text, encoding="utf-8")
                self.assert_invalid(self.run_validator(domain), f"{field} must be relative")

    def test_declared_path_rejects_traversal_and_symlink(self) -> None:
        domain = self.copy_domain()
        self.replace_once(domain / "domain.yaml", "source_registry: raw/source-contracts.yaml", "source_registry: ../source-contracts.yaml")
        self.assert_invalid(self.run_validator(domain), "source_registry must stay inside the domain")

        domain = self.copy_domain()
        link = domain / "raw" / "linked-contracts.yaml"
        link.symlink_to("source-contracts.yaml")
        self.replace_once(domain / "domain.yaml", "source_registry: raw/source-contracts.yaml", "source_registry: raw/linked-contracts.yaml")
        self.assert_invalid(self.run_validator(domain), "source_registry must not contain symlinks")

        domain = self.copy_domain()
        artifact = domain / "raw" / "snapshots" / "pricing-policy-memo.md"
        artifact.unlink()
        artifact.symlink_to(artifact.name)
        self.assert_invalid(self.run_validator(domain), "artifact.path is not a valid path")

    def test_self_referential_domain_symlink_is_reported_without_traceback(self) -> None:
        domain = self.copy_domain()
        loop = domain.parent / "domain-loop"
        loop.symlink_to(loop.name, target_is_directory=True)
        self.assert_invalid(self.run_validator(loop), "could not resolve domain directory")

    def test_declared_files_and_changelog_are_required(self) -> None:
        targets = {
            "source_registry": "raw/source-contracts.yaml",
            "handbook": "AGENTS.md",
            "retirements": "retirements.jsonl",
            "redirects": "redirects.json",
            "changelog_dir": "changelog",
        }
        for field, relative in targets.items():
            with self.subTest(field=field):
                domain = self.copy_domain()
                target = domain / relative
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                self.assert_invalid(self.run_validator(domain), f"required {field}")

    def test_handbook_must_be_nonempty_utf8_text(self) -> None:
        for content, fragment in (
            (b"  \n", "required handbook is empty"),
            (b"\xff\n", "could not read UTF-8 text"),
        ):
            with self.subTest(fragment=fragment):
                domain = self.copy_domain()
                (domain / "AGENTS.md").write_bytes(content)
                self.assert_invalid(self.run_validator(domain), fragment)

    def test_eval_fixtures_are_required_and_nonempty(self) -> None:
        for relative, label in (
            ("evals/routing.jsonl", "routing"),
            ("evals/golden.jsonl", "golden"),
            ("evals/manifest.expected.jsonl", "manifest"),
        ):
            with self.subTest(relative=relative, state="missing"):
                domain = self.copy_domain()
                (domain / relative).unlink()
                self.assert_invalid(self.run_validator(domain), f"required {label}")
            with self.subTest(relative=relative, state="empty"):
                domain = self.copy_domain()
                (domain / relative).write_text("\n", encoding="utf-8")
                self.assert_invalid(self.run_validator(domain), f"required {label} fixture is empty")

    def test_manifest_write_waits_for_zero_errors(self) -> None:
        domain = self.copy_domain()
        manifest = domain / "evals" / "manifest.expected.jsonl"
        before = manifest.read_bytes()
        card = domain / "wiki" / "datasets" / "orders-daily.md"
        self.replace_once(card, "title: Daily orders interface", "title: Daily orders interface\ntitle: Duplicate")

        result = self.run_validator(domain, write_manifest=True)
        self.assert_invalid(result, "found duplicate key", "manifest write skipped because validation reported errors")
        self.assertEqual(manifest.read_bytes(), before)

    def test_manifest_write_rejects_symlink_and_does_not_touch_target(self) -> None:
        domain = self.copy_domain()
        manifest = domain / "evals" / "manifest.expected.jsonl"
        manifest.unlink()
        sentinel = domain / "sentinel.txt"
        sentinel.write_text("do not overwrite\n", encoding="utf-8")
        manifest.symlink_to("../sentinel.txt")

        result = self.run_validator(domain, write_manifest=True)
        self.assert_invalid(result, "manifest fixture must not contain symlinks")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "do not overwrite\n")

    def test_manifest_write_is_atomic_and_structured_availability_drives_layer(self) -> None:
        domain = self.copy_domain()
        dataset = domain / "wiki" / "datasets" / "orders-daily.md"
        manifest = domain / "evals" / "manifest.expected.jsonl"
        original_mode = stat.S_IMODE(manifest.stat().st_mode)
        self.replace_once(dataset, "    status: unavailable", "    status: available")

        result = self.run_validator(domain, write_manifest=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("written atomically", result.stdout)
        self.assertEqual(stat.S_IMODE(manifest.stat().st_mode), original_mode)
        rows = self.read_jsonl(manifest)
        layers = {row["id"]: row["layer"] for row in rows}
        self.assertEqual(layers["acme-analytics.metric.net-revenue"], "direct")
        self.assertEqual(layers["acme-analytics.metric.gross-revenue"], "direct")

    def test_every_source_contract_requires_provenance(self) -> None:
        domain = self.copy_domain()
        registry = domain / "raw" / "source-contracts.yaml"
        text = registry.read_text(encoding="utf-8")
        text, replacements = re.subn(r"(?m)^    provenance:\n(?:      .*\n)+", "", text, count=1)
        self.assertEqual(replacements, 1)
        registry.write_text(text, encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "is missing provenance")

    def test_evidence_kind_mismatch_is_an_error(self) -> None:
        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "net-revenue.md"
        self.replace_once(card, "  - kind: interface-contract", "  - kind: observed-output")
        self.assert_invalid(self.run_validator(domain), "differs from registry kind")

    def test_active_related_and_source_index_targets_must_be_valid(self) -> None:
        domain = self.copy_domain()
        dataset = domain / "wiki" / "datasets" / "orders-daily.md"
        self.replace_once(
            dataset,
            "    - acme-analytics.dimension.order-status",
            "    - acme-analytics.metric.net-sales",
        )
        self.assert_invalid(self.run_validator(domain), "active card relations.related points to deprecated card")

        domain = self.copy_domain()
        source = domain / "wiki" / "sources" / "pricing-policy-memo.md"
        self.replace_once(
            source,
            "  - acme-analytics.metric.net-revenue",
            "  - acme-analytics.dataset.orders-daily",
        )
        self.assert_invalid(self.run_validator(domain), "is not a canonical card")

    def test_duplicate_tombstones_and_redirect_sources_are_errors(self) -> None:
        domain = self.copy_domain()
        retirements = domain / "retirements.jsonl"
        lines = retirements.read_text(encoding="utf-8").splitlines()
        retirements.write_text("\n".join(lines + [lines[0]]) + "\n", encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "duplicate tombstone id")

        domain = self.copy_domain()
        redirects_path = domain / "redirects.json"
        redirects = json.loads(redirects_path.read_text(encoding="utf-8"))
        redirects["redirects"].append(dict(redirects["redirects"][0]))
        redirects_path.write_text(json.dumps(redirects), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "duplicate redirect from")

    def test_retirement_records_and_final_hash_must_match(self) -> None:
        domain = self.copy_domain()
        retirements = domain / "retirements.jsonl"
        rows = self.read_jsonl(retirements)
        rows[1]["retired_on"] = "2026-07-31"
        self.write_jsonl(retirements, rows)
        self.assert_invalid(self.run_validator(domain), "retired_on disagrees with card.retirement", "since disagrees with tombstone.retired_on")

        domain = self.copy_domain()
        retirements = domain / "retirements.jsonl"
        rows = self.read_jsonl(retirements)
        rows[1]["final_sha256"] = "0" * 64
        self.write_jsonl(retirements, rows)
        self.assert_invalid(self.run_validator(domain), "final_sha256 does not match the current card file")

        domain = self.copy_domain()
        retirements = domain / "retirements.jsonl"
        rows = self.read_jsonl(retirements)
        rows[0]["deleted_on"] = "2026-07-19"
        self.write_jsonl(retirements, rows)
        self.assert_invalid(self.run_validator(domain), "deleted_on must be on or after retired_on")

    def test_jsonl_rows_must_be_objects(self) -> None:
        cases = (
            ("retirements.jsonl", '"not an object"'),
            ("evals/routing.jsonl", "[]"),
            ("gaps.example.jsonl", "42"),
        )
        for relative, replacement in cases:
            with self.subTest(relative=relative):
                domain = self.copy_domain()
                path = domain / relative
                lines = path.read_text(encoding="utf-8").splitlines()
                path.write_text("\n".join([replacement] + lines[1:]) + "\n", encoding="utf-8")
                self.assert_invalid(self.run_validator(domain), "JSONL row must be an object")

    def test_redirected_ids_resolve_in_evals_and_gaps(self) -> None:
        domain = self.copy_domain()
        routing = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing)
        rows[0]["expected_cards"] = ["acme-analytics.metric.net-sales"]
        self.write_jsonl(routing, rows)
        gaps = domain / "gaps.example.jsonl"
        rows = self.read_jsonl(gaps)
        rows[0]["searched"][0]["top_cards"][0] = "acme-analytics.metric.daily-sales"
        rows[0]["candidate_cards"] = ["acme-analytics.metric.net-sales"]
        self.write_jsonl(gaps, rows)

        result = self.run_validator(domain)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_gap_card_lists_cannot_duplicate_after_redirect_resolution(self) -> None:
        domain = self.copy_domain()
        gaps = domain / "gaps.example.jsonl"
        rows = self.read_jsonl(gaps)
        rows[0]["searched"][0]["top_cards"] = [
            "acme-analytics.metric.net-revenue",
            "acme-analytics.metric.net-sales",
        ]
        self.write_jsonl(gaps, rows)
        self.assert_invalid(self.run_validator(domain), "searched.top_cards contains multiple ids that resolve")

        domain = self.copy_domain()
        gaps = domain / "gaps.example.jsonl"
        rows = self.read_jsonl(gaps)
        rows[0]["candidate_cards"] = [
            "acme-analytics.metric.net-revenue",
            "acme-analytics.metric.net-sales",
        ]
        self.write_jsonl(gaps, rows)
        self.assert_invalid(self.run_validator(domain), "candidate_cards contains multiple ids that resolve")

    def test_redirect_cycles_and_multi_hops_are_errors(self) -> None:
        domain = self.copy_domain()
        path = domain / "redirects.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["redirects"][0]["to"] = "acme-analytics.metric.net-sales"
        obj["redirects"][1]["to"] = "acme-analytics.metric.daily-sales"
        path.write_text(json.dumps(obj), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "redirect cycle")

        domain = self.copy_domain()
        path = domain / "redirects.json"
        obj = json.loads(path.read_text(encoding="utf-8"))
        obj["redirects"][0]["to"] = "acme-analytics.metric.net-sales"
        path.write_text(json.dumps(obj), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "multi-hop redirect")

    def test_gap_card_and_evidence_references_must_resolve(self) -> None:
        domain = self.copy_domain()
        gaps = domain / "gaps.example.jsonl"
        rows = self.read_jsonl(gaps)
        rows[0]["searched"][0]["top_cards"][0] = "acme-analytics.metric.missing"
        rows[0]["candidate_cards"] = ["acme-analytics.metric.also-missing"]
        rows[0]["claims"][0]["evidence_ref"] = "acme-analytics.synthetic.missing"
        self.write_jsonl(gaps, rows)
        self.assert_invalid(
            self.run_validator(domain),
            "searched.top_cards -> acme-analytics.metric.missing",
            "candidate_cards -> acme-analytics.metric.also-missing",
            "claims.evidence_ref -> acme-analytics.synthetic.missing",
        )

    def test_formula_and_filter_fields_must_coexist_on_one_bridge(self) -> None:
        domain = self.copy_domain()
        original = domain / "wiki" / "datasets" / "orders-daily.md"
        source = original.read_text(encoding="utf-8")

        first_fields = """  logical_fields:
    - recognition_date
    - order_status
    - refund_status
    - gross_amount
"""
        source, replacements = re.subn(r"(?ms)^  logical_fields:\n(?:    - .*\n)+", first_fields, source, count=1)
        self.assertEqual(replacements, 1)
        original.write_text(source, encoding="utf-8")

        second = source
        second = second.replace("id: acme-analytics.dataset.orders-daily", "id: acme-analytics.dataset.orders-refunds", 1)
        second = second.replace("title: Daily orders interface", "title: Refunds interface", 1)
        second = second.replace("summary: Synthetic logical dataset used to demonstrate a thin interface card.", "summary: Synthetic complementary interface used only for a negative validator test.", 1)
        second = second.replace("  - demo daily orders\n  - orders_daily", "  - demo refund orders\n  - orders_refunds", 1)
        second = second.replace("  - acme-analytics.metric.gross-revenue\n", "", 1)
        second = second.replace("asset_key: acme-analytics.demo.orders-daily", "asset_key: acme-analytics.demo.orders-refunds", 1)
        second_fields = """  logical_fields:
    - recognition_date
    - order_status
    - refund_status
    - refund_amount
"""
        second, replacements = re.subn(r"(?ms)^  logical_fields:\n(?:    - .*\n)+", second_fields, second, count=1)
        self.assertEqual(replacements, 1)
        (domain / "wiki" / "datasets" / "orders-refunds.md").write_text(second, encoding="utf-8")

        self.assert_invalid(self.run_validator(domain), "no single interface bridge covers formula and execution fields")

    def test_routing_examples_must_have_paraphrases_and_negatives(self) -> None:
        for field in ("paraphrases", "negative_queries"):
            with self.subTest(field=field):
                domain = self.copy_domain()
                path = domain / "evals" / "routing.jsonl"
                rows = self.read_jsonl(path)
                rows[0][field] = []
                self.write_jsonl(path, rows)
                self.assert_invalid(self.run_validator(domain), f"{field}: [] should be non-empty")

    def test_freshness_dates_and_explicit_stale_note_are_objective(self) -> None:
        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        self.replace_once(card, 'last_verified: "2026-08-25"', 'last_verified: "2026-08-27"')
        self.assert_invalid(self.run_validator(domain), "freshness.last_verified 2026-08-27 is after validation date")

        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        self.replace_once(card, 'checked_at: "2026-08-25"', 'checked_at: "2026-08-26"')
        self.assert_invalid(self.run_validator(domain), "evidence checked_at 2026-08-26 is after last_verified")

        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        self.replace_once(card, "status: certified", 'status: stale\nstatus_note: " "')
        self.assert_invalid(self.run_validator(domain), "whitespace-only strings are forbidden")

    def test_active_evidence_cannot_precede_the_current_registry_capture(self) -> None:
        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        self.replace_once(card, 'checked_at: "2026-08-25"', 'checked_at: "2026-08-24"')
        self.assert_invalid(
            self.run_validator(domain),
            "active-card evidence acme-analytics.synthetic.orders-v1 checked_at 2026-08-24 "
            "is before registry provenance.captured_on 2026-08-25",
        )

    def test_machine_significant_text_and_compiled_briefs_must_be_nonblank(self) -> None:
        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        self.replace_once(card, "formula: sum(gross_amount)", 'formula: " "')
        self.assert_invalid(self.run_validator(domain), "whitespace-only strings are forbidden")

        domain = self.copy_domain()
        card = domain / "wiki" / "datasets" / "orders-daily.md"
        self.replace_once(
            card,
            "reason: the demo adapter is fictional and has no executable connection in this repository",
            'reason: " "',
        )
        self.assert_invalid(self.run_validator(domain), "whitespace-only strings are forbidden")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[0]["question"] = " "
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "whitespace-only strings are forbidden")

        domain = self.copy_domain()
        tombstone_path = domain / "retirements.jsonl"
        rows = self.read_jsonl(tombstone_path)
        rows[0]["reason"] = " "
        self.write_jsonl(tombstone_path, rows)
        self.assert_invalid(self.run_validator(domain), "whitespace-only strings are forbidden")

        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        text = card.read_text(encoding="utf-8")
        text, replacements = re.subn(r"(?s)(## Definition\n)\n.*?(?=\n## )", r"\1\n", text, count=1)
        self.assertEqual(replacements, 1)
        card.write_text(text, encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "must contain a non-empty compiled brief")

    def test_yaml_duplicate_keys_are_rejected(self) -> None:
        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        self.replace_once(card, "title: Gross revenue", "title: Gross revenue\ntitle: Hidden replacement")
        self.assert_invalid(self.run_validator(domain), "found duplicate key 'title'")

    def test_yaml_unhashable_keys_are_reported_without_tracebacks(self) -> None:
        domain = self.copy_domain()
        descriptor = domain / "domain.yaml"
        descriptor.write_text("? [compound, key]\n: value\n" + descriptor.read_text(encoding="utf-8"), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "found unhashable key")

    def test_non_utf8_domain_inputs_are_reported_without_tracebacks(self) -> None:
        cases = (
            "domain.yaml",
            "raw/source-contracts.yaml",
            "redirects.json",
            "retirements.jsonl",
            "evals/manifest.expected.jsonl",
            "evals/routing.jsonl",
            "evals/golden.jsonl",
            "gaps.example.jsonl",
        )
        for relative in cases:
            with self.subTest(relative=relative):
                domain = self.copy_domain()
                (domain / relative).write_bytes(b"\xff\xfe\n")
                self.assert_invalid(self.run_validator(domain), "could not read UTF-8 text")

        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        card.write_bytes(b"\xff\xfe\n")
        self.assert_invalid(self.run_validator(domain), "card must be UTF-8")

    def test_non_regular_card_is_rejected_without_blocking(self) -> None:
        domain = self.copy_domain()
        fifo = domain / "wiki" / "metrics" / "blocking.md"
        os.mkfifo(fifo)
        self.assert_invalid(self.run_validator(domain), "card must be a regular file")

    def test_non_utf8_card_filename_is_rejected_before_manifest_write(self) -> None:
        domain = self.copy_domain()
        manifest = domain / "evals" / "manifest.expected.jsonl"
        before = manifest.read_bytes()
        original = domain / "wiki" / "metrics" / "gross-revenue.md"
        invalid_name = os.fsencode(original.parent) + b"/gross-\xff.md"
        os.rename(os.fsencode(original), invalid_name)
        result = self.run_validator(domain, write_manifest=True)
        self.assert_invalid(result, "Unicode surrogate code points are forbidden", "manifest write skipped")
        self.assertEqual(manifest.read_bytes(), before)

    def test_surrogates_and_non_finite_numbers_are_rejected(self) -> None:
        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        routing_text = routing_path.read_text(encoding="utf-8")
        routing_path.write_text(
            routing_text.replace("acme-analytics.metric.net-revenue", r"\ud800", 1),
            encoding="utf-8",
        )
        self.assert_invalid(self.run_validator(domain), "Unicode surrogate code points are forbidden")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[0]["max_rank"] = float("nan")
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "non-standard constant NaN is forbidden")

        domain = self.copy_domain()
        card = domain / "wiki" / "metrics" / "gross-revenue.md"
        self.replace_once(card, "summary: Daily recognized order value before any refund is subtracted.", "summary: .nan")
        self.assert_invalid(self.run_validator(domain), "non-finite values are forbidden")

    def test_excessive_nesting_and_huge_integers_are_parse_errors(self) -> None:
        domain = self.copy_domain()
        (domain / "redirects.json").write_text("[" * 2000 + "]" * 2000, encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "invalid JSON")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        routing_path.write_text("[" * 2000 + "]" * 2000 + "\n", encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "invalid JSON")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        routing_path.write_text("{\"id\":" + "9" * 5000 + "}\n", encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "invalid JSON")

        domain = self.copy_domain()
        descriptor = domain / "domain.yaml"
        descriptor.write_text("node:\n" + "  -" * 2000 + " value\n", encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "invalid YAML")

    def test_schema_invalid_shapes_report_errors_without_tracebacks(self) -> None:
        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry["contracts"] = None
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "contracts: None is not of type 'array'")

        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry["contracts"][0].pop("kind")
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "'kind' is a required property")

        domain = self.copy_domain()
        (domain / "redirects.json").write_text("null\n", encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "'redirects' is a required property")

        domain = self.copy_domain()
        redirects_path = domain / "redirects.json"
        redirects = json.loads(redirects_path.read_text(encoding="utf-8"))
        redirects["redirects"][0]["to"] = 7
        redirects_path.write_text(json.dumps(redirects), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "redirects/0/to: 7 is not of type 'string'")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        routing = self.read_jsonl(routing_path)
        routing[0]["paraphrases"] = None
        self.write_jsonl(routing_path, routing)
        self.assert_invalid(self.run_validator(domain), "paraphrases: None is not of type 'array'")

        domain = self.copy_domain()
        gaps_path = domain / "gaps.example.jsonl"
        gaps = self.read_jsonl(gaps_path)
        gaps[0]["searched"] = None
        self.write_jsonl(gaps_path, gaps)
        self.assert_invalid(self.run_validator(domain), "searched: None is not of type 'array'")

        domain = self.copy_domain()
        self.assert_invalid(self.run_validator(domain, as_of="not-a-date"), "invalid ISO date")

    def test_json_duplicate_keys_are_rejected_at_any_depth(self) -> None:
        domain = self.copy_domain()
        redirects_path = domain / "redirects.json"
        text = redirects_path.read_text(encoding="utf-8")
        old = '"to": "acme-analytics.metric.net-revenue"'
        new = old + ',\n      "to": "acme-analytics.metric.gross-revenue"'
        self.replace_once(redirects_path, old, new)
        self.assert_invalid(self.run_validator(domain), "duplicate key 'to'")

        domain = self.copy_domain()
        gaps_path = domain / "gaps.example.jsonl"
        text = gaps_path.read_text(encoding="utf-8")
        old = '"confidence":"narrated"'
        new = '"confidence":"narrated","confidence":"verified_live"'
        self.replace_once(gaps_path, old, new)
        self.assert_invalid(self.run_validator(domain), "duplicate key 'confidence'")

    def test_tombstone_targets_and_card_retirements_are_reciprocal(self) -> None:
        domain = self.copy_domain()
        metric = domain / "wiki" / "metrics" / "net-revenue.md"
        self.replace_once(metric, "    - acme-analytics.metric.daily-sales\n", "")
        self.assert_invalid(self.run_validator(domain), "must list acme-analytics.metric.daily-sales")

        domain = self.copy_domain()
        metric = domain / "wiki" / "metrics" / "net-revenue.md"
        self.replace_once(
            metric,
            "    - acme-analytics.metric.daily-sales",
            "    - acme-analytics.metric.unknown-retirement",
        )
        self.assert_invalid(self.run_validator(domain), "is neither a deprecated card nor a tombstone")

        domain = self.copy_domain()
        retirements = domain / "retirements.jsonl"
        rows = self.read_jsonl(retirements)
        rows[1]["reason"] = "A contradictory synthetic reason."
        self.write_jsonl(retirements, rows)
        self.assert_invalid(self.run_validator(domain), "reason disagrees with card.retirement")

    def test_execution_contract_references_and_interface_fields_must_resolve(self) -> None:
        domain = self.copy_domain()
        dashboard = domain / "wiki" / "dashboards" / "commerce-overview.md"
        self.replace_once(
            dashboard,
            "        - acme-analytics.metric.net-revenue",
            "        - acme-analytics.dimension.order-status",
        )
        self.assert_invalid(self.run_validator(domain), "is not an active metric card")

        domain = self.copy_domain()
        dashboard = domain / "wiki" / "dashboards" / "commerce-overview.md"
        self.replace_once(
            dashboard,
            "    - recognition_date",
            "    - field_not_exposed_by_interface",
        )
        self.assert_invalid(self.run_validator(domain), "not present in query_interface.logical_fields")

        domain = self.copy_domain()
        metric = domain / "wiki" / "metrics" / "net-revenue.md"
        self.replace_once(
            metric,
            "    - recognition_date",
            "    - field_not_exposed_by_any_bridge",
        )
        self.assert_invalid(self.run_validator(domain), "no single interface bridge covers formula and execution fields")

        domain = self.copy_domain()
        dashboard = domain / "wiki" / "dashboards" / "commerce-overview.md"
        self.replace_once(dashboard, "  - acme-analytics.metric.gross-revenue\n", "")
        self.assert_invalid(self.run_validator(domain), "is not bridged by this interface's canonical_cards")

    def test_executable_playbooks_require_real_interface_bridges(self) -> None:
        domain = self.copy_domain()
        playbook = domain / "wiki" / "playbooks" / "net-revenue-by-region.md"
        self.replace_once(playbook, "    - acme-analytics.dataset.orders-daily\n", "")
        self.assert_invalid(
            self.run_validator(domain),
            "executable playbook must depend on at least one active interface card",
            "is not bridged by any interface dependency",
        )

        domain = self.copy_domain()
        dataset = domain / "wiki" / "datasets" / "orders-daily.md"
        self.replace_once(dataset, "  - acme-analytics.metric.net-revenue\n", "")
        self.assert_invalid(self.run_validator(domain), "is not bridged by any interface dependency")

        domain = self.copy_domain()
        dataset = domain / "wiki" / "datasets" / "orders-daily.md"
        self.replace_once(dataset, "    - refund_amount\n", "")
        self.assert_invalid(
            self.run_validator(domain),
            "is not bridged by any interface dependency with complete formula and execution field coverage",
        )

    def test_required_fields_cannot_repeat_formula_or_filter_fields(self) -> None:
        for replacement in ("gross_amount", "order_status"):
            with self.subTest(replacement=replacement):
                domain = self.copy_domain()
                metric = domain / "wiki" / "metrics" / "net-revenue.md"
                self.replace_once(metric, "    - recognition_date\n", f"    - {replacement}\n")
                self.assert_invalid(
                    self.run_validator(domain),
                    "execution_contract.required_fields repeats formula or filter fields",
                )

    def test_execution_layers_cannot_duplicate_or_contradict_filters(self) -> None:
        domain = self.copy_domain()
        dashboard = domain / "wiki" / "dashboards" / "commerce-overview.md"
        self.replace_once(
            dashboard,
            "source_refs:",
            "    - layer: revenue-trend-chart\nsource_refs:",
        )
        self.assert_invalid(self.run_validator(domain), "duplicate execution_contract.by_layer name")

        domain = self.copy_domain()
        dashboard = domain / "wiki" / "dashboards" / "commerce-overview.md"
        self.replace_once(
            dashboard,
            "source_refs:",
            """      forbid_filter:
        - field: region
          op: neq
          value: sample
          reason: contradictory synthetic test
source_refs:""",
        )
        self.assert_invalid(self.run_validator(domain), "both requires and forbids filter region neq")

    def test_routing_max_rank_cannot_exceed_cutoff(self) -> None:
        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[0]["max_rank"] = rows[0]["cutoff"] + 1
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "must be less than or equal to cutoff")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[2]["max_rank"] = 1
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "cannot contain all 2 expected_cards")

    def test_routing_execution_interfaces_are_complete_and_relevant(self) -> None:
        domain = self.copy_domain()
        metric = domain / "wiki" / "metrics" / "net-revenue.md"
        text = metric.read_text(encoding="utf-8")
        text, replacements = re.subn(
            r"(?ms)^execution_contract:\n.*?(?=^source_refs:)",
            "",
            text,
            count=1,
        )
        self.assertEqual(replacements, 1)
        metric.write_text(text, encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "has no execution_contract")

        domain = self.copy_domain()
        dataset = domain / "wiki" / "datasets" / "orders-daily.md"
        self.replace_once(dataset, "    - refund_amount\n", "")
        dashboard = domain / "wiki" / "dashboards" / "commerce-overview.md"
        self.replace_once(dashboard, "    - refund_amount\n", "    - refund_amount\n    - product_category\n")
        self.assert_invalid(self.run_validator(domain), "has no complete required_interface")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[2]["expected_cards"] = ["acme-analytics.trap.pending-refund-double-count"]
        rows[2]["max_rank"] = 1
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "must name at least one active metric")

    def test_routing_surfaces_and_resolved_ids_cannot_contradict(self) -> None:
        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[0]["negative_queries"][0] = "  HOW is NET revenue calculated? "
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "positive and negative routing surfaces overlap")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[0]["expected_cards"] = [
            "acme-analytics.metric.net-revenue",
            "acme-analytics.metric.net-sales",
        ]
        rows[0]["max_rank"] = 2
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "multiple ids that resolve to acme-analytics.metric.net-revenue")

        domain = self.copy_domain()
        routing_path = domain / "evals" / "routing.jsonl"
        rows = self.read_jsonl(routing_path)
        rows[1]["expected_cards"] = ["acme-analytics.metric.net-revenue"]
        self.write_jsonl(routing_path, rows)
        self.assert_invalid(self.run_validator(domain), "interface-locate must include an active interface")

    def test_source_snapshot_contract_and_provenance_must_agree(self) -> None:
        domain = self.copy_domain()
        source = domain / "wiki" / "sources" / "pricing-policy-memo.md"
        self.replace_once(source, '  captured_on: "2026-08-25"', '  captured_on: "2026-08-24"')
        self.assert_invalid(self.run_validator(domain), "snapshot.captured_on disagrees with registry provenance")

        domain = self.copy_domain()
        source = domain / "wiki" / "sources" / "pricing-policy-memo.md"
        self.replace_once(source, "  trust: authoritative", "  trust: low")
        self.assert_invalid(self.run_validator(domain), "snapshot.trust disagrees with registry provenance")

        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        snapshot_contract = next(c for c in registry["contracts"] if c["kind"] == "document-snapshot")
        snapshot_contract["kind"] = "observed-output"
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "must be a document-snapshot contract")

    def test_document_snapshot_artifact_is_safe_present_and_hashed(self) -> None:
        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        contract = next(c for c in registry["contracts"] if c["kind"] == "document-snapshot")
        contract["artifact"]["sha256"] = "0" * 64
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "artifact.sha256 does not match")

        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        contract = next(c for c in registry["contracts"] if c["kind"] == "document-snapshot")
        contract["artifact"]["path"] = "/tmp/outside.md"
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "artifact.path must be relative")

        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        contract = next(c for c in registry["contracts"] if c["kind"] == "document-snapshot")
        contract["artifact"]["path"] = "domain.yaml"
        contract["artifact"]["sha256"] = hashlib.sha256((domain / "domain.yaml").read_bytes()).hexdigest()
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "artifact.path must live under raw/snapshots/")

        domain = self.copy_domain()
        artifact = domain / "raw" / "snapshots" / "pricing-policy-memo.md"
        linked_target = artifact.with_name("linked-target.md")
        artifact.rename(linked_target)
        artifact.symlink_to(linked_target.name)
        self.assert_invalid(self.run_validator(domain), "artifact.path must not contain symlinks")

        domain = self.copy_domain()
        (domain / "raw" / "snapshots" / "pricing-policy-memo.md").unlink()
        self.assert_invalid(self.run_validator(domain), "required contract", "artifact file is missing")

    def test_registry_contract_shape_and_artifact_kind_are_closed(self) -> None:
        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        snapshot = next(c for c in registry["contracts"] if c["kind"] == "document-snapshot")
        contract = next(c for c in registry["contracts"] if c["kind"] != "document-snapshot")
        contract["artifact"] = json.loads(json.dumps(snapshot["artifact"]))
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "artifact")

        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry["contracts"][0]["unexpected_field"] = "not part of the contract"
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "unexpected_field")

    def test_snapshot_artifacts_are_nonempty_unique_and_fully_registered(self) -> None:
        for content, fragment in (
            (b"", "artifact must not be empty"),
            (b"  \n", "artifact must contain non-blank Markdown"),
            (b"\xff\n", "artifact must be UTF-8 Markdown"),
        ):
            with self.subTest(fragment=fragment):
                domain = self.copy_domain()
                artifact = domain / "raw" / "snapshots" / "pricing-policy-memo.md"
                artifact.write_bytes(content)
                registry_path = domain / "raw" / "source-contracts.yaml"
                registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
                contract = next(c for c in registry["contracts"] if c["kind"] == "document-snapshot")
                contract["artifact"]["sha256"] = hashlib.sha256(content).hexdigest()
                registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
                self.assert_invalid(self.run_validator(domain), fragment)

        domain = self.copy_domain()
        orphan = domain / "raw" / "snapshots" / "orphan.md"
        orphan.write_text("Synthetic orphan.\n", encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "unregistered managed snapshot")

        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        contract = next(c for c in registry["contracts"] if c["kind"] == "document-snapshot")
        duplicate = json.loads(json.dumps(contract))
        duplicate["id"] = "acme-analytics.synthetic.duplicate-snapshot-v1"
        registry["contracts"].append(duplicate)
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "share artifact.path", "paths must be unique")

    def test_registry_provenance_cannot_be_from_the_future(self) -> None:
        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        registry["contracts"][0]["provenance"]["captured_on"] = "2026-08-27"
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "provenance.captured_on 2026-08-27 is after validation date")

    def test_all_dated_records_respect_the_validation_date(self) -> None:
        domain = self.copy_domain()
        consistency = domain / "wiki" / "consistency" / "revenue-term.md"
        self.replace_once(consistency, 'ruled_on: "2026-08-25"', 'ruled_on: "2026-08-27"')
        self.assert_invalid(self.run_validator(domain), "arbitration.ruled_on 2026-08-27")

        domain = self.copy_domain()
        retirements = domain / "retirements.jsonl"
        rows = self.read_jsonl(retirements)
        rows[0]["retired_on"] = "2026-08-27"
        rows[0]["deleted_on"] = "2026-08-28"
        self.write_jsonl(retirements, rows)
        redirects_path = domain / "redirects.json"
        redirects = json.loads(redirects_path.read_text(encoding="utf-8"))
        redirects["redirects"][0]["since"] = "2026-08-27"
        redirects_path.write_text(json.dumps(redirects), encoding="utf-8")
        self.assert_invalid(
            self.run_validator(domain),
            "retired_on 2026-08-27 is after validation date",
            "deleted_on 2026-08-28 is after validation date",
            "starts after validation date",
        )

        domain = self.copy_domain()
        golden_path = domain / "evals" / "golden.jsonl"
        rows = self.read_jsonl(golden_path)
        rows[0]["ground_truth_type"] = "measured_live"
        rows[0]["layer"] = "volatile"
        rows[0]["measured_on"] = "2026-08-27"
        self.write_jsonl(golden_path, rows)
        self.assert_invalid(self.run_validator(domain), "measured_on 2026-08-27 is after validation date")

        domain = self.copy_domain()
        gaps_path = domain / "gaps.example.jsonl"
        rows = self.read_jsonl(gaps_path)
        rows[0]["registered_on"] = "2026-08-27T00:00:00Z"
        self.write_jsonl(gaps_path, rows)
        self.assert_invalid(self.run_validator(domain), "registered_on 2026-08-27 is after validation date")

        domain = self.copy_domain()
        dimension = domain / "wiki" / "dimensions" / "order-status.md"
        self.replace_once(dimension, '  captured_on: "2026-08-25"', '  captured_on: "2026-08-27"')
        self.assert_invalid(self.run_validator(domain), "value_domain.captured_on 2026-08-27")

    def test_gap_dates_are_rfc3339_and_verified_live_evidence_is_strong(self) -> None:
        domain = self.copy_domain()
        gaps_path = domain / "gaps.example.jsonl"
        rows = self.read_jsonl(gaps_path)
        rows[0]["registered_on"] = "2026-08-25t10:00:00z"
        self.write_jsonl(gaps_path, rows)
        result = self.run_validator(domain)
        self.assertEqual(result.returncode, 0, result.stdout)

        for malformed in (
            "2026-08-25T23:59:60Z",
            "2026-08-25T10:00:00+24:00",
            "2026-08-25T10:00:00",
        ):
            with self.subTest(malformed=malformed):
                domain = self.copy_domain()
                gaps_path = domain / "gaps.example.jsonl"
                rows = self.read_jsonl(gaps_path)
                rows[0]["registered_on"] = malformed
                self.write_jsonl(gaps_path, rows)
                self.assert_invalid(self.run_validator(domain), "malformed registered_on")

        domain = self.copy_domain()
        gaps_path = domain / "gaps.example.jsonl"
        rows = self.read_jsonl(gaps_path)
        rows[1]["claims"][0]["evidence_ref"] = "acme-analytics.synthetic.net-revenue-v1"
        self.write_jsonl(gaps_path, rows)
        self.assert_invalid(self.run_validator(domain), "must be technical, not semantic-decision")

        for field, value, fragment in (
            ("state_at_capture", "published", "provenance.state_at_capture live"),
            ("trust", "low", "authoritative provenance"),
            ("captured_on", "2026-08-26", "after gap registration"),
        ):
            with self.subTest(field=field):
                domain = self.copy_domain()
                registry_path = domain / "raw" / "source-contracts.yaml"
                registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
                contract = next(
                    c for c in registry["contracts"]
                    if c["id"] == "acme-analytics.synthetic.commerce-overview-v1"
                )
                contract["provenance"][field] = value
                registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
                self.assert_invalid(self.run_validator(domain), fragment)

    def test_certification_and_value_domains_are_cross_record_consistent(self) -> None:
        domain = self.copy_domain()
        registry_path = domain / "raw" / "source-contracts.yaml"
        registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
        contract = next(
            c for c in registry["contracts"] if c["id"] == "acme-analytics.synthetic.gross-revenue-v1"
        )
        contract["provenance"]["state_at_capture"] = "draft"
        contract["provenance"]["trust"] = "low"
        registry_path.write_text(yaml.safe_dump(registry, sort_keys=False), encoding="utf-8")
        self.assert_invalid(self.run_validator(domain), "needs an approved, authoritative semantic-decision")

        domain = self.copy_domain()
        dimension = domain / "wiki" / "dimensions" / "order-status.md"
        self.replace_once(
            dimension,
            "    - value: cancelled",
            "    - value: completed\n      meaning: contradictory duplicate\n    - value: cancelled",
        )
        self.assert_invalid(self.run_validator(domain), "duplicate value_domain value 'completed'")

        domain = self.copy_domain()
        dimension = domain / "wiki" / "dimensions" / "order-status.md"
        self.replace_once(dimension, '  captured_on: "2026-08-25"', '  captured_on: "2026-08-24"')
        self.assert_invalid(self.run_validator(domain), "value_domain.captured_on disagrees with registry provenance")

    def test_golden_positive_and_negative_requirements_cannot_overlap(self) -> None:
        domain = self.copy_domain()
        golden_path = domain / "evals" / "golden.jsonl"
        rows = self.read_jsonl(golden_path)
        rows[0]["must_not"] = ["  RECOGNITION date IS the TIME axis "]
        self.write_jsonl(golden_path, rows)
        self.assert_invalid(self.run_validator(domain), "same text appears in must_disclose and must_not")


class ValidatorUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location("llm_wiki_validate", VALIDATOR)
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load validator module")
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_derive_layer_never_interprets_availability_as_a_string_prefix(self) -> None:
        card = {
            "id": "acme.metric.example",
            "type": "metric",
            "knowledge_role": "canonical",
            "definition": {"formula": "sum(gross_amount) - sum(refund_amount)"},
            "execution_contract": {
                "always_filter": [{"field": "order_status"}],
            },
        }
        interfaces = {
            card["id"]: [{
                "query_interface": {
                    "availability": "available: false",
                    "logical_fields": ["gross_amount", "refund_amount", "order_status"],
                }
            }]
        }
        self.assertEqual(self.module.derive_layer(card, interfaces), "guided")

        interfaces[card["id"]][0]["query_interface"]["availability"] = {
            "status": "available",
            "reason": "test adapter is ready",
        }
        self.assertEqual(self.module.derive_layer(card, interfaces), "direct")

    def test_only_active_interface_cards_are_indexed_as_bridges(self) -> None:
        cards = {
            "active": {
                "id": "active",
                "status": "certified",
                "knowledge_role": "interface",
                "canonical_cards": ["metric"],
            },
            "deprecated": {
                "id": "deprecated",
                "status": "deprecated",
                "knowledge_role": "interface",
                "canonical_cards": ["metric"],
            },
            "canonical": {
                "id": "canonical",
                "status": "certified",
                "knowledge_role": "canonical",
                "canonical_cards": ["metric"],
            },
        }
        indexed = self.module.active_interfaces_by_canonical(cards)
        self.assertEqual([card["id"] for card in indexed["metric"]], ["active"])

    def test_direct_layer_requires_one_available_complete_interface(self) -> None:
        card = {
            "id": "acme.metric.example",
            "type": "metric",
            "knowledge_role": "canonical",
            "definition": {"formula": "sum(gross_amount) - sum(refund_amount)"},
            "execution_contract": {"always_filter": [{"field": "order_status"}]},
        }
        interfaces = {
            card["id"]: [
                {
                    "query_interface": {
                        "availability": {"status": "available", "reason": "partial adapter"},
                        "logical_fields": ["gross_amount", "order_status"],
                    }
                },
                {
                    "query_interface": {
                        "availability": {"status": "unavailable", "reason": "complete adapter is offline"},
                        "logical_fields": ["gross_amount", "refund_amount", "order_status"],
                    }
                },
            ]
        }
        self.assertEqual(self.module.derive_layer(card, interfaces), "guided")

    def test_direct_layer_includes_declared_required_fields(self) -> None:
        card = {
            "id": "acme.metric.example",
            "type": "metric",
            "knowledge_role": "canonical",
            "definition": {"formula": "sum(gross_amount)"},
            "execution_contract": {
                "required_fields": ["recognition_date"],
                "always_filter": [],
            },
        }
        bridge = {
            "query_interface": {
                "availability": {"status": "available", "reason": "test adapter"},
                "logical_fields": ["gross_amount"],
            }
        }
        self.assertEqual(self.module.derive_layer(card, {card["id"]: [bridge]}), "guided")
        bridge["query_interface"]["logical_fields"].append("recognition_date")
        self.assertEqual(self.module.derive_layer(card, {card["id"]: [bridge]}), "direct")

    def test_review_after_date_is_stale_on_the_date_it_arrives(self) -> None:
        card = {
            "status": "certified",
            "freshness": {"review_after": "2026-08-26"},
        }
        self.assertEqual(self.module.effective_status(card, dt.date(2026, 8, 26)), "stale")

    def test_schema_loader_reports_malformed_and_non_regular_inputs(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        schema_dir = pathlib.Path(temporary.name)
        previous = self.module.SCHEMA_DIR
        self.module.SCHEMA_DIR = schema_dir
        try:
            cases = (
                ("non-utf.schema.json", b"\xff\xfe", "could not read UTF-8 text"),
                ("syntax.schema.json", b"{", "invalid JSON"),
                (
                    "duplicate.schema.json",
                    b'{"type":"object","type":"string"}',
                    "duplicate key 'type'",
                ),
                ("meta.schema.json", b'{"type":7}', "invalid Draft 2020-12 schema"),
                ("missing-ref.schema.json", b'{"$ref":"#/missing"}', "unresolvable or non-local $ref"),
                ("external-ref.schema.json", b'{"$ref":"missing.json"}', "unresolvable or non-local $ref"),
                ("root-ref.schema.json", b'{"$ref":"#"}', "unresolvable or non-local $ref"),
            )
            for name, content, fragment in cases:
                with self.subTest(name=name):
                    (schema_dir / name).write_bytes(content)
                    report = self.module.Report()
                    self.assertIsNone(self.module.load_schema(name, report))
                    self.assertTrue(any(fragment in error for error in report.errors), report.errors)

            fifo_name = "fifo.schema.json"
            os.mkfifo(schema_dir / fifo_name)
            report = self.module.Report()
            self.assertIsNone(self.module.load_schema(fifo_name, report))
            self.assertTrue(any("must be a regular file" in error for error in report.errors), report.errors)
        finally:
            self.module.SCHEMA_DIR = previous

    def test_recursive_yaml_alias_is_rejected(self) -> None:
        report = self.module.Report()
        value = self.module.read_yaml("root: &root [*root]\n", pathlib.Path("cycle.yaml"), report)
        self.assertIsNone(value)
        self.assertTrue(any("recursive aliases are forbidden" in error for error in report.errors), report.errors)

        report = self.module.Report()
        value = self.module.read_yaml(
            "original: &shared [one, two]\ncopy: *shared\n",
            pathlib.Path("shared.yaml"),
            report,
        )
        self.assertIsNone(value)
        self.assertTrue(any("shared container aliases are forbidden" in error for error in report.errors), report.errors)

    def test_schema_evaluation_cycles_are_reported(self) -> None:
        schema = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$ref": "#/$defs/a",
            "$defs": {
                "a": {"$ref": "#/$defs/b"},
                "b": {"$ref": "#/$defs/a"},
            },
        }
        validator = self.module.jsonschema.Draft202012Validator(schema)
        errors = self.module.schema_errors(validator, {})
        self.assertTrue(any("schema evaluation failed" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

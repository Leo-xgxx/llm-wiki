#!/usr/bin/env python3
"""llm-wiki 一致性校验：防止漏写索引、漏建文件、frontmatter 缺字段。

用法:
    python3 validate_wiki.py

检查项:
  1. index.json 为合法 JSON，条目字段完整（path/title/type/keywords/status/updated/incomplete）
  2. index.json 中每个 path 对应的文件存在，且 type 与所在目录一致
  3. 各类型目录下的每个条目文件都已登记进 index.json（防漏写索引）
  4. 条目 frontmatter 必填字段齐全（title/type/keywords/status/created/updated/source）
  5. INDEX.md 包含所有 active 条目的文件名（防漏写人读索引）
  6. 文件命名为 kebab-case

退出码: 0 = 全部通过; 1 = 有错误。
"""
import json
import re
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).resolve().parents[3] / "llm-wiki"
INDEX_JSON = WIKI_ROOT / "index.json"
INDEX_MD = WIKI_ROOT / "INDEX.md"

TYPE_DIRS = {"dataset": "datasets", "concept": "concepts", "faq": "faq", "runbook": "runbooks"}
INDEX_FIELDS = ["path", "title", "type", "keywords", "status", "updated", "incomplete"]
FM_FIELDS = ["title", "type", "keywords", "status", "created", "updated", "source"]
KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")

errors = []


def err(msg: str) -> None:
    errors.append(msg)


def parse_frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        err(f"{path.relative_to(WIKI_ROOT)}: 缺少 frontmatter（--- 包裹的头部）")
        return {}
    fm = {}
    for line in m.group(1).splitlines():
        kv = re.match(r"^(\w+):\s*(.*)$", line)
        if kv:
            fm[kv.group(1)] = kv.group(2).strip()
    return fm


def main() -> int:
    if not INDEX_JSON.is_file():
        print(f"错误: 找不到 {INDEX_JSON}", file=sys.stderr)
        return 1
    try:
        index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"错误: index.json 不是合法 JSON: {e}", file=sys.stderr)
        return 1

    entries = index.get("entries", [])
    indexed_paths = set()

    for i, entry in enumerate(entries):
        label = entry.get("path", f"entries[{i}]")
        for f in INDEX_FIELDS:
            if f not in entry:
                err(f"index.json {label}: 缺少字段 '{f}'")
        p = entry.get("path")
        if not p:
            continue
        indexed_paths.add(p)
        file_path = WIKI_ROOT / p
        if not file_path.is_file():
            err(f"index.json {label}: 文件不存在（索引指向了不存在的条目）")
            continue
        etype = entry.get("type")
        expected_dir = TYPE_DIRS.get(etype)
        if expected_dir and not p.startswith(expected_dir + "/"):
            err(f"{label}: type '{etype}' 应位于 '{expected_dir}/' 目录下")
        fm = parse_frontmatter(file_path)
        if fm:
            for f in FM_FIELDS:
                if f not in fm or not fm[f]:
                    err(f"{p}: frontmatter 缺少必填字段 '{f}'")
            if fm.get("type") and etype and fm["type"] != etype:
                err(f"{p}: frontmatter type '{fm['type']}' 与 index.json type '{etype}' 不一致")
            if fm.get("status") and entry.get("status") and fm["status"] != entry["status"]:
                err(f"{p}: frontmatter status 与 index.json status 不一致")

    # 目录中的条目文件必须都在索引里
    for dirname in TYPE_DIRS.values():
        d = WIKI_ROOT / dirname
        if not d.is_dir():
            err(f"缺少目录 llm-wiki/{dirname}/")
            continue
        for f in d.glob("*.md"):
            if f.name == "README.md":
                continue
            rel = f"{dirname}/{f.name}"
            if rel not in indexed_paths:
                err(f"{rel}: 条目文件未登记进 index.json（漏写索引）")
            if not KEBAB_RE.match(f.name):
                err(f"{rel}: 文件名必须为 kebab-case（小写字母/数字/连字符）")

    # INDEX.md 必须包含所有 active 条目
    if INDEX_MD.is_file():
        index_md = INDEX_MD.read_text(encoding="utf-8")
        for entry in entries:
            if entry.get("status") == "active" and entry.get("path"):
                if entry["path"] not in index_md:
                    err(f"INDEX.md: 缺少 active 条目 {entry['path']}（漏写人读索引）")
    else:
        err("缺少 llm-wiki/INDEX.md")

    if errors:
        print(f"校验失败，共 {len(errors)} 个问题：\n")
        for e in errors:
            print(f"  ✗ {e}")
        return 1
    print(f"校验通过：{len(entries)} 个索引条目，索引与文件一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""写入前冲突检索：在 llm-wiki/index.json 中按关键词匹配候选冲突条目。

用法:
    python3 check_conflicts.py "关键词1" "关键词2" ...

匹配规则: 对每个输入关键词，与条目的 title 和 keywords 做大小写不敏感的
双向包含匹配（输入包含于字段，或字段包含于输入）。
退出码: 0 = 无命中（可直接新增）; 1 = 有命中（需人工比对）; 2 = 参数/环境错误。
"""
import json
import sys
from pathlib import Path

WIKI_ROOT = Path(__file__).resolve().parents[3] / "llm-wiki"
INDEX_JSON = WIKI_ROOT / "index.json"


def matches(term: str, text: str) -> bool:
    t, x = term.lower(), text.lower()
    return t in x or x in t


def main() -> int:
    terms = [t.strip() for t in sys.argv[1:] if t.strip()]
    if not terms:
        print("用法: check_conflicts.py <关键词1> [关键词2] ...", file=sys.stderr)
        return 2
    if not INDEX_JSON.is_file():
        print(f"错误: 找不到索引 {INDEX_JSON}", file=sys.stderr)
        return 2
    try:
        index = json.loads(INDEX_JSON.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"错误: index.json 不是合法 JSON: {e}", file=sys.stderr)
        return 2

    hits = []
    for entry in index.get("entries", []):
        fields = [entry.get("title", "")] + list(entry.get("keywords", []))
        matched = sorted({t for t in terms for f in fields if f and matches(t, f)})
        if matched:
            hits.append((entry, matched))

    if not hits:
        print("无命中条目，可作为新知识直接新增（仍建议用同义词/中英互译再检索一次）。")
        return 0

    print(f"命中 {len(hits)} 个候选冲突条目，写入前必须逐一打开比对：\n")
    for entry, matched in hits:
        print(f"- {entry.get('path')} [{entry.get('status', '?')}]")
        print(f"  title: {entry.get('title')}")
        print(f"  命中关键词: {', '.join(matched)}")
    print("\n处理规则见 references/conflict-handling.md")
    return 1


if __name__ == "__main__":
    sys.exit(main())

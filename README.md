# lda-llm-wiki

面向 LLM 的知识库（LLM Wiki）：知识以结构化 Markdown 条目存放，配备机器可读索引与新增知识 Skill，使 AI 能在用户提交新内容时自动、规范地写入知识并维护索引。

## 目录结构

```
.
├── skills/                           # skill 目录，后续可持续新增其他 skill
│   └── llm-wiki-knowledge-add/       # 新增知识 skill
│       ├── SKILL.md                  # 流程：分类、冲突检测、依赖补全、索引维护、自检
│       ├── scripts/
│       │   ├── check_conflicts.py    # 写入前：按关键词检索潜在冲突条目
│       │   └── validate_wiki.py      # 写入后：校验条目格式与索引一致性（防漏写/错写）
│       └── references/
│           ├── entry-format.md       # 条目格式规范（frontmatter、命名、小节）
│           └── conflict-handling.md  # 冲突场景判定与处理示例
└── llm-wiki/
    ├── INDEX.md                      # 人类可读总索引
    ├── index.json                    # 机器索引（AI 检索与冲突检测入口）
    ├── _templates/                   # 各类型条目模板
    │   ├── dataset.md
    │   ├── concept.md
    │   ├── faq.md
    │   └── runbook.md
    ├── datasets/                     # 数据集知识（数据集ID、口径、上游表等）
    ├── concepts/                     # 业务/领域概念、指标定义
    ├── faq/                          # 常见问题
    └── runbooks/                     # 操作步骤、排障流程
```

## 核心约定

1. **一条知识一个文件**，按类型分目录存放，文件名用 kebab-case。
2. **双索引**：`INDEX.md`（人读）+ `index.json`（机读），任何写入必须同步更新两者。
3. **写入前冲突检测**：运行 `check_conflicts.py` 检索；矛盾知识必须确认后更新并留变更记录，过期条目标记 `deprecated` 而非删除。
4. **写入后脚本校验**：运行 `validate_wiki.py`，自动检查索引与文件一致、frontmatter 完整，防止漏写漏维护。
5. **依赖信息补全**：dataset 类条目需查数据集 ID、上游表等；内部工具未接入时在 SKILL.md Step 4 有占位约定。
6. 全部流程与自检清单见 [`skills/llm-wiki-knowledge-add/SKILL.md`](skills/llm-wiki-knowledge-add/SKILL.md)。

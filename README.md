# lda-llm-wiki

面向 LLM 的知识库（LLM Wiki）：知识以结构化 Markdown 条目存放，配备机器可读索引与新增知识 Skill，使 AI 能在用户提交新内容时自动、规范地写入知识并维护索引。

## 目录结构

```
lda-agent/
├── SKILL.md                  # 新增知识 Skill：分类、冲突检测、依赖补全、索引维护、自检
└── llm-wiki/
    ├── INDEX.md              # 人类可读总索引
    ├── index.json            # 机器索引（AI 检索与冲突检测入口）
    ├── _templates/           # 各类型条目模板
    │   ├── dataset.md
    │   ├── concept.md
    │   ├── faq.md
    │   └── runbook.md
    ├── datasets/             # 数据集知识（数据集ID、口径、上游表等）
    ├── concepts/             # 业务/领域概念、指标定义
    ├── faq/                  # 常见问题
    └── runbooks/             # 操作步骤、排障流程
```

## 核心约定

1. **一条知识一个文件**，按类型分目录存放，文件名用 kebab-case。
2. **双索引**：`INDEX.md`（人读）+ `index.json`（机读），任何写入必须同步更新两者。
3. **写入前冲突检测**：以 `index.json` 的 keywords 做检索，矛盾知识必须确认后更新并留变更记录，过期条目标记 `deprecated` 而非删除。
4. **依赖信息补全**：dataset 类条目需查数据集 ID、上游表等；内部工具未接入时在 `SKILL.md` Step 4 有占位约定。
5. 全部流程与自检清单见 [`lda-agent/SKILL.md`](lda-agent/SKILL.md)。

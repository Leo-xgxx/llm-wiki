---
name: llm-wiki-knowledge-add
description: >
  当用户提交新知识、纠错、或发消息要求"记录/添加/更新"某条知识时，
  使用本 skill 将知识规范化写入 llm-wiki，包括：知识分类、冲突检测、
  依赖信息补全（数据集ID/上游表等）、条目写入、索引维护、脚本校验、自检。
keywords: ["新增知识", "添加知识", "更新wiki", "记录", "knowledge add", "wiki update"]
---

# Skill：向 llm-wiki 新增/更新知识

> 触发条件：用户提交新内容，或消息中包含"记录一下 / 加到 wiki / 这个知识要更新 / 之前的说法不对"等意图。
> 目标：任何一次知识写入都必须**同时**完成：条目文件 + 两个索引 + 冲突处理，并通过脚本校验。缺一不可。
>
> 本 skill 附带资源：
> - `scripts/check_conflicts.py`：写入前按关键词检索潜在冲突条目
> - `scripts/validate_wiki.py`：写入后校验条目格式、索引一致性，防止漏写/错写
> - `references/entry-format.md`：条目 frontmatter 与正文小节的完整格式规范
> - `references/conflict-handling.md`：冲突场景判定与处理示例
>
> wiki 根目录为仓库一级目录 `llm-wiki/`。

## 总流程（必须按顺序执行）

```
1. 解析意图 → 2. 分类 → 3. 冲突检测(脚本) → 4. 依赖信息补全 → 5. 写入条目 → 6. 维护索引 → 7. 脚本校验 + 自检
```

---

## Step 1：解析用户输入

从用户消息中提取：

| 字段 | 说明 | 缺失时的处理 |
|---|---|---|
| 知识主题 (title) | 一句话概括 | 向用户确认 |
| 知识内容 (body) | 事实/结论/操作步骤 | 向用户确认 |
| 知识类型 | dataset / concept / faq / runbook | 按 Step 2 规则推断 |
| 关键词 (keywords) | 3~8 个，中英文均可 | 由 AI 从内容中提取 |
| 时效性 | 是否会过期（如表结构、口径） | 默认长期有效 |
| 来源 (source) | 用户口述 / 文档链接 / 工具查询结果 | 标注 `用户口述` |

## Step 2：分类规则

| 类型 | 目录 | 判断标准 |
|---|---|---|
| dataset | `llm-wiki/datasets/` | 涉及具体数据集、表、字段、口径、上下游血缘 |
| concept | `llm-wiki/concepts/` | 业务/领域概念、指标定义、术语解释 |
| faq | `llm-wiki/faq/` | 问答形式、常见疑问、"为什么/怎么办"类 |
| runbook | `llm-wiki/runbooks/` | 操作步骤、排障流程、SOP |

一条知识如果跨类型，以**主体内容**归类，并在其他类型条目中用相对链接引用，禁止复制内容造成双份维护。

## Step 3：冲突知识检测（写入前必做）

1. 运行冲突检索脚本：

   ```bash
   python3 skills/llm-wiki-knowledge-add/scripts/check_conflicts.py "关键词1" "关键词2" ...
   ```

   脚本会在 `llm-wiki/index.json` 中按 title/keywords 匹配并列出候选冲突条目。AI 还应额外考虑同义词、中英文互译后再检索一次。
2. 对命中的每个条目，打开对应文件比对内容（详细判定见 `references/conflict-handling.md`）：
   - **无冲突（纯新增）**：继续 Step 4。
   - **补充**：新知识是既有条目的扩展 → 更新既有条目，不新建文件。
   - **矛盾**：新知识与既有条目结论相反 →
     a. 优先以带来源/更新时间较新的一方为准；
     b. 无法判断时，**必须向用户确认**，不得擅自覆盖；
     c. 确认后更新条目，并在条目的 `变更记录` 中写明旧结论、新结论、变更原因和日期。
   - **过期**：既有条目已失效 → 将其 frontmatter 的 `status` 改为 `deprecated`，在正文顶部注明替代条目链接，不物理删除文件。
3. 冲突处理结果必须体现在条目的 `变更记录` 小节中。

## Step 4：依赖信息补全（内部工具占位）

dataset 类知识写入前，需通过内部工具补全以下字段。**当前环境未接入这些工具，以下为占位约定**——接入后替换为真实调用；未接入时向用户索取，用户未提供则字段填 `TODO(待查)` 并在 index.json 中标记 `"incomplete": true`：

| 待查信息 | 内部工具（占位） | 说明 |
|---|---|---|
| 数据集 ID | `TODO: dataset-id-lookup(名称) → dataset_id` | 用数据集名称/表名查询唯一 ID |
| 上游表/血缘 | `TODO: lineage-query(dataset_id) → upstream_tables[]` | 查询上游依赖表列表 |
| 下游消费方 | `TODO: lineage-query(dataset_id, direction=down)` | 可选，评估变更影响面 |
| 字段 schema | `TODO: schema-fetch(dataset_id) → columns[]` | 字段名、类型、注释 |
| 负责人/Owner | `TODO: owner-lookup(dataset_id)` | 归属团队或负责人 |

> ⚠️ 接入真实工具后：更新本表为实际工具名与调用方式，并删除 `TODO` 前缀。

## Step 5：写入条目

1. 从 `llm-wiki/_templates/` 选择对应类型的模板复制；格式规范详见 `references/entry-format.md`。
2. 文件命名：`<类型目录>/<kebab-case-英文或拼音主题名>.md`，禁止空格与中文文件名。
3. 填写 frontmatter（title / type / keywords / status / created / updated / source）和正文全部小节；模板中不适用的小节写 `N/A`，不得直接删除。
4. 首次创建时 `变更记录` 写一行"初始创建"。

## Step 6：维护索引（每次写入/更新/废弃后必做，不得遗漏）

必须同步更新**两个**索引：

1. **`llm-wiki/index.json`**（机器索引，供 AI 检索与冲突检测）：
   - 新增/更新对应条目对象：`path`、`title`、`type`、`keywords`、`status`、`updated`、`incomplete`；
   - 废弃条目将 `status` 设为 `deprecated`，不删除。
2. **`llm-wiki/INDEX.md`**（人类可读目录）：
   - 在对应类型小节的表格中新增/更新一行（标题、链接、关键词、更新时间）；
   - 废弃条目移入"已废弃"小节。

## Step 7：脚本校验 + 自检清单

写入完成后**必须**运行校验脚本，退出码为 0 才算通过：

```bash
python3 skills/llm-wiki-knowledge-add/scripts/validate_wiki.py
```

脚本会检查：index.json 合法性与字段完整性、索引条目与实际文件一一对应（防漏写索引/漏建文件）、条目 frontmatter 必填字段、INDEX.md 是否包含所有 active 条目。**任何报错必须修复后重跑，直至通过。**

最后核对自检清单（全部为 ✅ 才算完成）：

- [ ] 条目文件已创建/更新，frontmatter 完整
- [ ] 已运行 `check_conflicts.py` 检索冲突，冲突已按 Step 3 处理
- [ ] dataset 类条目已补全（或标记 TODO）数据集 ID、上游表等依赖信息
- [ ] `index.json` 已更新且为合法 JSON
- [ ] `INDEX.md` 已更新
- [ ] 变更记录小节已写明本次变更
- [ ] 未产生重复条目、未物理删除历史条目
- [ ] `validate_wiki.py` 已通过（退出码 0）

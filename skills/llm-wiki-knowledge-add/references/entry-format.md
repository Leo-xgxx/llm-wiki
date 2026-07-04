# 条目格式规范（entry-format）

llm-wiki 每个知识条目为一个 Markdown 文件，由 **YAML frontmatter** + **固定小节正文** 组成。
写入时从 `llm-wiki/_templates/<type>.md` 复制模板，按本规范填写。

## 1. Frontmatter（全部必填）

```yaml
---
title: 条目标题（一句话，允许中文）
type: dataset | concept | faq | runbook
keywords: ["关键词1", "关键词2"]   # 3~8 个，JSON 数组格式，中英文均可
status: active | deprecated
created: YYYY-MM-DD
updated: YYYY-MM-DD               # 每次修改必须刷新
source: 用户口述 | 文档链接 | 工具查询
---
```

约束：

- `type` 必须与所在目录一致（如 `datasets/` 下必须是 `dataset`）。
- `keywords` 必须是合法的行内 JSON 数组写法（校验脚本会检查）。
- 废弃条目：`status: deprecated`，并在正文标题下方第一行加 `> ⚠️ 已废弃，替代条目：[<标题>](<相对链接>)`。

## 2. 文件命名

- 路径：`llm-wiki/<类型目录>/<kebab-case-名称>.md`
- 只允许小写字母、数字、连字符；禁止空格、下划线、中文文件名。
- 例：`llm-wiki/datasets/user-daily-active.md`

## 3. 正文小节（按类型）

各类型必需小节（顺序固定，不适用的小节保留标题并写 `N/A`，不得删除）：

| 类型 | 必需小节 |
|---|---|
| dataset | 基本信息（含数据集 ID、Owner、更新频率）/ 口径与说明 / 上游依赖 / 关键字段 / 相关条目 / 变更记录 |
| concept | 定义 / 计算口径 \| 判定规则 / 示例 / 相关条目 / 变更记录 |
| faq | 问题描述 / 答案 / 相关条目 / 变更记录 |
| runbook | 适用场景 / 前置条件 / 操作步骤 / 回滚 \| 异常处理 / 相关条目 / 变更记录 |

## 4. 变更记录格式

```markdown
## 变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-07-04 | 初始创建 | |
| 2026-08-01 | 口径由 A 改为 B | 上游表切换 |
```

- 每次修改追加一行，不改写历史行。
- 冲突覆盖时必须写明：旧结论、新结论、变更原因。

## 5. index.json 条目格式

```json
{
  "path": "datasets/user-daily-active.md",
  "title": "用户日活数据集",
  "type": "dataset",
  "keywords": ["日活", "DAU", "user-daily-active"],
  "status": "active",
  "updated": "2026-07-04",
  "incomplete": false
}
```

- `path` 为相对 `llm-wiki/` 的路径。
- `incomplete: true` 表示存在 `TODO(待查)` 字段（如数据集 ID 未查到），后续补全后改回 `false`。

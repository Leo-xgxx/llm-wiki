# lda-llm-wiki

一个私人维护的 LLM Wiki 设计记录：把口径当代码管、机器只做可验证的事、缺口由系统自己闭环。记录的是**方法**——知识怎么建模、怎么进来、怎么被检索和执行、怎么评测、怎么自维护——以及沿途做过和推翻过的决定。

这里不是任何现有系统的镜像，也不保存真实业务知识、内部代码、生产配置、用户身份或运行数据。仓库中的名称、数字、问题和数据源均为虚构示例（`acme` 命名空间）。导读用中文，正文文档用英文。

## 核心思路

1. 知识源、知识卡、生成物和运行态彼此分层，权威归属明确。
2. 机器负责提取与验证可判定事实，人负责确认语义和边界；没有机器判据就不做批量改动。
3. 卡片描述稳定的计算方法与适用范围，不围绕某一次提问组织内容。
4. 同一知识只有一个权威归属；共享的词面由一致性卡仲裁；跨域通过引用连接，不复制正文。
5. 结构层（执行契约、域手册、接口桥）先于正文；契约与正文冲突时契约胜出。
6. 生成物由源卡编译而来，禁止手工修改；构建顺序固定。
7. 结构、图谱、构建、检索、排位回归、规划、答题、新鲜度分别设门，不能用一个"测试通过"代替全部。
8. 运行时信模型、喂硬事实、fail closed：空结果不是零，检索失败不是知识不存在。
9. 缺口先登记、再过三选一门槛、再派单；无权威源不产卡。
10. 不叠机制：先删后加，一次性事故不立门禁；吞吐只受正确性门禁和 owner 裁决限制。

## 目录

```text
docs/                         设计说明（英文）
schemas/                      机器可读契约：卡片、域、来源登记、路由评测、金题、manifest、墓碑、跳转、缺口
templates/                    九类卡模板 + 域手册 + 变更日志模板
tools/validate.py             参考校验器：schema + 跨记录规则 + 确定性 manifest
examples/acme-analytics/      完全虚构的示例域，覆盖每一种契约
  domain.yaml                 域描述：登记表、手册、边界、路由提示
  AGENTS.md                   域手册：先于卡片读取的硬规则
  raw/source-contracts.yaml   带来源信息的证据登记表
  wiki/<type>/                九类卡各至少一张，含一张已废弃卡
  retirements.jsonl           墓碑；redirects.json 旧 id 跳转；changelog/ 变更记录
  evals/                      路由评测、金题、预期 manifest
  gaps.example.jsonl          缺口记录示例
```

数据流：

```text
source evidence (with provenance)
      -> normalized cards (contract + prose)
      -> structural + cross-record validation
      -> deterministic build (manifest, layers, capsules)
      -> rank regression against base
      -> route -> resolve -> plan
      -> execution under contract, or disclosed refusal
      -> gap record -> eligibility -> ticket -> machine change -> review -> three locks -> merge
```

## 阅读顺序

先读方法，再读例子，最后读决定：

1. [整体架构](docs/architecture.md) — 五层、域布局、三种角色、构建产物、消费出口、分发形态
2. [卡片模型](docs/card-model.md) — 九类卡、正文分节的编译语义、执行契约、别名纪律、生命周期
3. [处理流水线](docs/processing-pipeline.md) — 从录入到退役的九步，含变更评审清单
4. [录入与挖域](docs/intake-and-mining.md) — 收录判据、两条输入链、七问探查、九步挖域、按源类型的打法
5. [证据与 raw 层](docs/evidence-and-raw.md) — KEEP/DELETE、来源头、血缘策略、探针规则
6. [检索与评测](docs/retrieval-and-evaluation.md) — 三层编译、胶囊、回退阶梯、排位预算、门禁分设
7. [金题](docs/golden-questions.md) — 端到端评测的分类体系、拒答即正确、双指标
8. [答题运行时](docs/answering-runtime.md) — 信模型/喂事实/fail closed、执行规则、降级与拒答、缺口登记
9. [治理](docs/governance.md) — 机器/人分工、元规则、状态权限、评审与合入
10. [自维护闭环](docs/self-maintenance-loop.md) — 三选一门槛、六角色、机器 MR、三把锁、监工、验收
11. [可观测性](docs/observability.md) — 四类数据源、探测器、两个看板
12. [命名、决策框架与反模式](docs/anti-patterns.md)
13. [决策日志](docs/decision-log.md) — 做过和推翻过的决定，含刻意搁置项
14. [实现状态](docs/implementation-status.md) — 哪些实战过、哪些只是设计、哪些建了又删
15. [术语表](docs/glossary.md)
16. [虚构示例域](examples/acme-analytics/README.md)

## 校验

```bash
pip install pyyaml jsonschema
python3 tools/validate.py examples/acme-analytics
```

零错误是提交的前提。修改示例卡后，经评审用 `--write-manifest` 重新生成预期 manifest，diff 是评审的一部分。

## 明确不记录的内容

- 真实组织、产品、人员、客户、账号或身份标识
- 真实表名、数据集、看板、文档 token 或内部 URL
- 查询结果、生产日志、会话、凭证和临时下载地址
- 现有项目源码、部署脚本、运行 prompt 或 Git 历史
- 从其他仓库逐字复制的实现或文档

每次推送前按 `AGENTS.md` 的四类扫描检查一遍。

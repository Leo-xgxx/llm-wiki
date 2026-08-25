# lda-llm-wiki

一个私人维护的 LLM Wiki 设计骨架，用来记录可复用的知识组织方法、卡片契约、构建链路和检索治理原则。

这里不是任何现有系统的镜像，也不保存真实业务知识、内部代码、生产配置、用户身份或运行数据。仓库中的名称、数字、问题和数据源均为虚构示例。

## 核心思路

1. 知识源、知识卡、生成物和运行态彼此分层。
2. 机器负责提取与验证可判定事实，人负责确认语义和边界。
3. 卡片描述稳定的计算方法与适用范围，不围绕某一次提问组织内容。
4. 同一知识只有一个权威归属，跨域通过引用连接，不复制正文。
5. 生成物由源卡编译而来，禁止手工修改。
6. 结构正确、检索稳定、答案可靠分别设门，不能用一个“测试通过”代替全部。

## 目录

```text
docs/                         设计说明与治理方法
schemas/                      机器可读契约
templates/                    新建卡片时使用的空模板
examples/acme-analytics/      完全虚构的最小示例域
  domain.yaml                 虚构域的路由提示
  raw/                        最小充分的来源说明
  wiki/                       人读与机读合一的源卡
  evals/                      合成检索样例与预期构建清单 fixture
```

真实实现可以在仓库外增加编译器和运行时，但建议继续保持以下数据流：

```text
source evidence
      -> normalized cards
      -> structural validation
      -> immutable build artifacts
      -> route
      -> resolve
      -> execution plan
      -> evidence-backed answer
```

## 阅读顺序

1. [整体架构](docs/architecture.md)
2. [卡片模型](docs/card-model.md)
3. [处理流水线](docs/processing-pipeline.md)
4. [检索与评测](docs/retrieval-and-evaluation.md)
5. [治理与边界](docs/governance.md)
6. [虚构示例域](examples/acme-analytics/README.md)

## 明确不记录的内容

- 真实组织、人员、客户、账号或身份标识
- 真实表名、数据集、看板、文档 token 或内部 URL
- 查询结果、生产日志、会话、凭证和临时下载地址
- 现有项目源码、部署脚本、运行 prompt 或 Git 历史
- 从其他仓库逐字复制的实现或文档

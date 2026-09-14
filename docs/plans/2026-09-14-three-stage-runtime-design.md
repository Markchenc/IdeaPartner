# IdeaPartner 三阶段运行时修改设计

**Goal:** 将 13 个认知任务重构为三个独立代理阶段，取消用户确认，按问题驱动证据获取，保留最终 M4 六部分结构化输出。

**Architecture:** Python 保持确定性的文件运行时，负责任务包、版本、来源身份验证、交接和导出；宿主 Codex 负责启动三个代理、调研与判断。阶段二在同一代理上下文中循环检索和审查，可以多次保存证据增量，不把每轮检索变成独立代理。

**Tech Stack:** 保持 Python 标准库、argparse、JSON、unittest；不增加数据库、工作流框架或模型 SDK。

**状态：**已在本地仓库实现三阶段运行时，版本 2.0.0。28 项自动化测试通过，包含中文路径下的打包 CLI 三阶段端到端流程、证据版本、补查、并发和失败恢复；skill 格式校验通过。尚未发布 GitHub 版本、更新已安装副本，或完成真实研究案例的质量与 token 基准测试。

## 1. 已确定的需求与取舍

必须满足：

1. 正常流程没有用户确认、没有伪造的自动确认记录。
2. 三个主要代理任务：定位规划、综合审查、结构化报告。
3. M3 不再是必须完成的前置领域地图；每次检索对应一个会影响判断的问题。
4. M4 六部分结构保留在最终结果，不能把审查建议混入用户原始方案。
5. 任务交接传递当前结论和必要证据，不传递全部搜索轨迹及多版描述。
6. 允许有界补查，保留版本一致性、来源真实性与引用可追溯性。

ADR 决策摘要：

| 选择 | 决策与理由 | 代价 |
|---|---|---|
| 在旧图上跳过节点 / 重写三阶段协议 / 去掉运行时 | 选择三阶段协议；旧图的 checkpoint、M3 证据入口、M5 合约与状态机相互耦合，简单跳过不可靠 | 需要主版本升级和替换流程测试 |
| 一次大提交 / 每轮完整产物 / 增量证据＋阶段提交 | 选择后者；迭代可恢复，同时不放大代理数与上下文 | 增加一个证据批次接口 |
| 泛化细粒度依赖引擎 / 小规模显式版本依赖 | 选择显式版本依赖；三阶段没有必要引入任意 DAG 引擎 | 阶段一核心定位更改时仍整体重审 |
| 双运行时兼容 / 旧数据只读 | 选择旧数据只读，必要时用旧发布版本继续旧 run | 不支持直接续跑 v1 中途产物 |

## 2. 现有代码锚点

文件均相对仓库根目录：

- `skills/ideapartner/scripts/idea_review_runtime/tasks.py`：13 个 TaskSpec、M3_DISCOVERY_TASKS、M5_TASKS、checkpoint 字段。
- `pipeline.py::create`：schema_version=1、硬编码 runtime_version、两个 checkpoint。
- `pipeline.py::_ensure_checkpoint`、两个 confirm 方法、`compute_state`：确认关卡与固定 M1–M7 顺序。
- `pipeline.py::source_ledger/canonical_evidence_claims/_prepare_payload`：来源与有效证据依附三个 M3 发现任务和 synthesis。
- `pipeline.py::_emit_task_unlocked/_ingest_unlocked`：完整输入包、模型生成 consumed_inputs.used_for、版本绑定和最终报告导出。
- `validation.py`：M3 专属文案与 M5 专属合约；有可复用的来源、定位和 provenance 校验。
- `evidence.py`：来源身份验证可复用；现有 merge_source_ledgers 主要按 source_id 合并，不能当成 DOI 去重缓存。
- `artifacts.py`、`locking.py`：已有原子文件写入与进程文件锁，继续复用。
- `.codex-plugin/plugin.json` 与 `agents/openai.yaml`：默认提示明确要求 checkpoint，也必须更新。

## 3. 新任务图及自动编排

任务 ID 固定为：

```python
STAGES = ("s1-plan", "s2-review", "s3-report")
DEPENDENCIES = {
    "s1-plan": ("input",),
    "s2-review": ("input", "plan"),
    "s3-report": ("input", "plan", "review"),
}
```

证据视图作为 s3 的运行时派生输入，绑定所选证据版本，不将整个证据台账作为必读正文。

基本状态：`PLANNING → REVIEWING → REPORTING → FINALIZED`。补查增加 `RECHECKING`，不增加第四种主要代理职责。校验失败保持原状态并返回错误，不创建用户确认状态。

宿主编排说明：读取 status.ready_tasks → emit-task → 在新代理上下文执行 → ingest → 自动进入下一阶段。Python 不调用模型，不把 emit-task 成功误报为代理已启动。阶段二内部不重新 spawn；补查优先继续原阶段二代理，代理不可恢复时使用恢复包重建同一职责。

没有代理能力时明确标注 isolation_mode=unavailable，不静默声称完成了独立代理隔离。正常目标环境使用三个独立上下文；这项能力检查不改变科学结论的证据标准。

## 4. 运行目录和版本

```text
<run>/
  input.md
  manifest.json
  artifacts/
    plan-v1.json
    review-v1.json
    report-v1.json
  evidence/
    ledger-v1.json
    ledger-v2.json
  tasks/<packet_id>.json
  views/<packet_id>-evidence.json
  submissions/                 # 代理暂存输出，不作下游必读输入
  rechecks/<request_id>.json
  final-report.md
```

产物采用不可变版本文件；manifest 指向当前有效版本。每个写入操作先写新文件，最后原子更新 manifest。崩溃时未被 manifest 引用的文件不算提交成功，不能通过目录扫描自动纳入台账。继续使用一个运行级锁，不引入数据库事务。

manifest schema_version=2；runtime_version 引用 `__version__`，建议新发布为 2.0.0。主要字段：run_id、state、artifacts、evidence_snapshot、task_packets、budget、recheck、exports。不再含 checkpoints。

只有原始输入、三个阶段结果和证据台账具有权威内容；报告 Markdown 是渲染结果。不要同时维护同义 summary、attention_items、conclusion、report_markdown 四套完整文字。

## 5. 三阶段输出合约

通用提交 envelope：

```json
{"task_id":"s1-plan","packet_id":"<runtime-issued-id>","payload":{}}
```

运行时从 packet 记录输入版本及来源，删除模型手写的 consumed_inputs.used_for。packet_id 绑定运行、阶段、输入版本与尝试；提交前核查其仍有效。该机制证明输入供应与版本绑定，不声称证明模型真正阅读或正确理解。

### 5.1 s1-plan

```text
idea_claims: [{id, text, input_locator}]
boundaries: [text]
maturity: early | middle | developed
contribution_type: text
constraints: [text]
working_assumptions: [{text, consequence_if_wrong}]
review_questions: [{id, question, decision_impact, priority}]
```

任务书默认建议 500–800 中文字，代码只告警，不截断、不要求为压字数损失重要边界。字段允许明确未知；不要求方法细节齐全。s1 不调研、不写领域背景；input_locator 可用原文行号，输入快照固定后由运行时检查范围。

### 5.2 s2-review

四维度固定枚举：`value`、`contribution`、`mechanism`、`testability`。

```text
questions: [{id, question, decision_impact, outcome, evidence_refs}]
judgments: [{id, dimension, statement, applicability,
            basis, evidence_refs, rationale,
            strongest_counterargument, uncertainty, next_action}]
closest_work: [{source_ref, overlaps, differences, consequence, evidence_refs}]
decision: {status, rationale, scope, decisive_judgment_ids}
stop: {reason, unresolved_question_ids, coverage_limits}
```

`applicability`：assessable/provisional/not_yet_assessable/not_applicable。
`basis`：literature/researcher_input/inference；literature 必须绑定有效证据。输入自相矛盾的判断可绑定 input_locator 并解释推理，不强制编造论文作为依据。
`decision.status`：continue/revise/subsumed/not_viable/insufficient_evidence。
`stop.reason`：decision_supported/budget_exhausted/retrieval_unavailable。

M6 挑战体现在最强反驳及判断更新中；不再要求单独挑战报告或每个判断都生成三项挑战。s2 可新增 questions，但必须说明决策用途；不能绕回阶段一无限扩展路线。若证据显示原定位有偏差，保留原意并在判断中标注，修订建议归入建议部分。

### 5.3 s3-report

```text
structured_idea: {
  problem_definition: [Item],
  limitations_and_core_difficulty: [Item],
  contribution_design: [Item],
  method_construction: [Item],
  experimental_setting: [Item],
  expected_difficulties: [Item]
}
assessment: [{dimension, blocks: [Block]}]
recommendations: [Block]
decision: Block
limitations: [Block]
```

Item 保存 text、provenance、input_locators、evidence_refs。用户原述必须可追溯至原文；推断与缺失显式标注。六部分均存在，缺失部分说明缺失，不能补造实验。

Block 保存 text、judgment_ids、evidence_refs。程序用结构化块渲染 Markdown，自动附对应来源链接，避免代理同时提交整份 Markdown 和等价 JSON。程序校验所有引用存在且版本有效、四维度被覆盖、M4 六部分存在。语义上引用是否支持主张、是否篡改原意仍由第三阶段代理检查，结构校验不能保证这些事实。

最终输出可结论先行，随后 M4、四维度审查、下一步；没有独立 M7 重复总结。正文只呈现一个综合结论。

## 6. M3 替换为按需证据批次

新增 `ledger.py` 管理台账，新增 CLI：

```text
evidence-add <run-dir> <batch.json> [--verification-mode live|deferred]
```

批次的最小内容：batch_id、question_id、decision_impact、sources、claims、outcome。question_id 必须是当前审查问题；新增问题可以在本批次携带 question 定义。一次批次对应有意义的检索工作，不是每次打开网页都保存。

证据条目：

```json
{
  "claim_id":"e01",
  "claim":"论文覆盖了特定实验条件",
  "question_ids":["q1"],
  "source_refs":[{"source_id":"s01","version":1}],
  "relation":"support",
  "locator":"Section 4, Table 2",
  "inspection":"full_text",
  "limits":"不支持对其他实验条件的推断"
}
```

source 身份由现有 verifier 检查，忽略代理自报 verified。摘要、搜索片段可登记为候选；不能凭其建立直接近似覆盖或决定性阻断。`inspection` 是代理记录的检查方式，不能把枚举合格视为语义已核实。

来源不可达时保留候选与缺口，本批次其他有效条目可用；未验证来源对应 claim 保持 candidate，不进入支持判断的有效集合。明确返回接受、候选、拒绝条目清单，禁止静默丢弃。结构损坏或引用冲突则整批拒绝。

来源去重按 DOI → arXiv ID → 规范化 URL，并保留版本差异及别名映射；标题近似只提示重复，不自动合并。正文与网页内容作为外部数据处理，不作为指令执行。

复用当前来源解析器，增加运行内身份核验缓存。键包含规范化身份、版本和参与匹配的元数据；元数据变化不可复用旧验证结果。失败不永久缓存。首版不做全局缓存或跨项目全文库。

身份验证网络请求放在 manifest 锁外；提交时重新取得锁并验证基础版本，冲突返回可重试错误。batch_id＋内容摘要保证重试幂等；同 ID 不同内容拒绝。

## 7. 证据选择与更新规则

s3 必读 input、plan、review 和运行时生成的 evidence view。view 从 review 全部 evidence_refs（含反证与closest_work）求闭包，加入对应 source；不能只选支持最终结论的材料。台账其余条目和搜索轨迹按需读取。

每条引用携带 claim/source 版本。台账新增不相关条目不使现有结果失效；修改被引用条目时使消费它的 review/report 失效。相关证据尚未用于 review 时，批次 outcome 必须指向受影响 question；对已关闭审查问题的新证据，evidence-add 将 review 标为需复核。程序能验证声明关系，不能自动判断所有新增论文的科学相关性。

首版只实现三个阶段和显式 question/claim 引用的局部失效，不做通用图数据库。失效后更新 s2 当前记录，再更新 s3；不回到 s1，也不要求重新读取全领域历史。

## 8. 有界补查与预算

s3 发现会改变结论的缺口时，允许同一提交入口返回：

```json
{
  "task_id":"s3-report",
  "packet_id":"...",
  "recheck_request":{
    "question_id":"q1",
    "reason":"现有证据无法区分主题相近与贡献覆盖",
    "affected_judgment_ids":["j2"],
    "needed_evidence":"正文中的目标函数及实验设定"
  }
}
```

recheck_request 与最终 payload 互斥。首次有效请求原子记录并使 state=RECHECKING；状态包含 ready_tasks=[s2-review]。补查任务包包含原 plan、当前 review、相关证据视图和问题；不是重新执行整个审查。

默认 max_rechecks=1。第二次不能再派发检索，运行时返回 limit_reached 并允许 s3 以不足证据完成。s2 补查失败也可返回 unresolved 并结束；不能制造死循环。

budget 首版包括 max_rechecks、review_deadline_minutes（初始建议 30，可配置）、阶段产物软字符阈值。研究期限从首次 s2 packet 发出计时，重新发包不重置；过期停止新调研，允许提交保守判断和生成最终报告。无法硬中断正在宿主执行的搜索，需在 skill 中约束工具调用前检查剩余时间。

无需每个检索轮次强制产物。长阶段可将当前紧凑 review 草稿与未决问题保存为 recovery 文件；该文件非规范产物，不供 s3 使用。中断后恢复不会丢失已提交证据。

## 9. 文件级变更清单

| 文件 | 修改 |
|---|---|
| `scripts/idea_review_runtime/tasks.py` | 替换 TaskSpec 集合；删除 checkpoint、M3_DISCOVERY_TASKS、M5_TASKS；定义三个阶段职责和输入 |
| `scripts/idea_review_runtime/pipeline.py` | 重写 create/compute_state/_task_ready/_prepare_payload；移除 confirm 方法；新增证据批次、补查与选择性输入；复用锁和事务骨架 |
| `scripts/idea_review_runtime/validation.py` | 三阶段 payload 校验、packet_id 绑定、引用版本及报告块校验；去掉 M3/M5 专属前提 |
| `scripts/idea_review_runtime/evidence.py` | 保留身份 resolver；增加规范化身份键与运行内验证缓存支持 |
| `scripts/idea_review_runtime/ledger.py`（新增） | 证据版本、批次幂等、问题用途、候选隔离、视图闭包和影响查询 |
| `scripts/idea_review_runtime/report.py`（新增） | 从 s3 结构化块渲染 final-report.md，按引用追加链接 |
| `scripts/idea_review_runtime/artifacts.py` | 复用原子写入；必要时补不可变文件写入辅助函数 |
| `scripts/idea_review_runtime/locking.py` | 原则上不改 |
| `scripts/idea_review.py` | 删除 confirm；增加 evidence-add、预算参数；保留 init/status/emit-task/ingest/validate；更新帮助文案 |
| `scripts/idea_review_runtime/__init__.py` | 单一版本来源，建议 2.0.0 |
| `SKILL.md` | 三代理自动编排、无确认、s2 同上下文迭代、条件补查 |
| `references/positioning-and-routing.md` | 收敛为 s1 说明，不要求双产物 |
| `references/domain-prior.md` | 改为问题驱动检索参考，无强制地图或历史树 |
| `references/review-chain.md` | 单代理四维度综合判断＋针对性挑战 |
| `references/idea-reconstruction.md` | 保留六部分，作为 s3 子职责 |
| `references/report-format.md` | s3 合约与单次呈现，禁止混入未标注改写 |
| `references/runtime-orchestration.md` | 更新宿主调度、补查、失败与恢复语义 |
| `references/artifact-contracts.md` | 删除旧 13 任务协议，只保留新模型需要的字段 |
| `agents/openai.yaml`、`.codex-plugin/plugin.json`、`README.md` | 更新版本、示例和默认提示；删除确认措辞，保留自动发现策略 |

以上 scripts/references/agents 相对 `skills/ideapartner/`。实施时在项目现有文档文件内修改，避免同时保留互相冲突的新旧指导。

## 10. 旧运行兼容

加载 schema_version=1 时 status 返回原始状态、legacy_read_only=true、ready_tasks=[]，可给出已有报告路径。emit/ingest/evidence-add 拒绝写入并说明应新建 v2 run；不自动修改旧 manifest，不把旧 M3 JSON 冒充新版台账。

提供最简单的迁移路径：对同一 input.md 新建运行。旧文献可作为候选导入，必须经过新台账验证后才支持新判断；自动批量导入不纳入首版。需要继续原审查时使用已有旧发布版本。

## 11. 分步实施与测试

测试使用现有 unittest 和 FakeSourceVerifier，不以实时网络作为单元测试前提。每一项先新增行为测试并观察失败，再实现对应最小功能。

1. **三阶段骨架与兼容边界**
   - 修改 tasks.py、pipeline.py、CLI、__init__.py；替换 tests/helpers.py 的任务构造。
   - 在 tests/test_pipeline.py 新增正常三阶段完成测试、s3 不可越过 s2、无确认自动 ready、旧 schema 只读和错误版本拒绝测试。
   - 删除“必须等 M1 确认”和“所有 M4–M7 必须读取 M1/M2/M3”的旧行为断言。
2. **按需证据台账**
   - 新增 ledger.py 和 tests/test_ledger.py，更新 evidence.py、validation.py。
   - 验证未核验来源不能支持判断、没有决策用途的批次不接受、同一 DOI 去重保留版本、批次幂等、冲突不改变 manifest。
   - 模拟提交前崩溃：未引用的新文件不产生部分有效结果；模拟并发批次无丢失更新。
3. **输入选择与增量更新**
   - 修改任务包生成，新增 tests/test_packets.py。
   - 测试支持和反对证据均进入视图；大量不相关候选不进入必读内容；新增不相关条目不失效；修改引用条目或声明影响已审问题会触发复核。
4. **补查、期限与恢复**
   - 更新 pipeline.py、CLI；新增 tests/test_recheck.py。
   - 测试一次定向补查回到报告、重复请求幂等、上限后可出不足证据报告、过期不能开启新调研但能提交结论、重新发包不重置期限。
5. **M4 和最终输出**
   - 新增 report.py、tests/test_report.py，更新 tests/test_evidence.py。
   - 测试六部分缺失被拒、合法“缺失”项可接受、推断不会渲染为用户原述、悬空/失效引用拒绝、结构块只渲染一次、四维度未知允许完成。
6. **skill 与发布一致性**
   - 更新上述 references、SKILL、README、插件和代理配置。
   - 更新 tests/test_distribution.py：Unicode 安装路径、插件版本一致、初始状态 PLANNING、首个任务 s1-plan、无确认的端到端样例。

运行命令（仓库根目录）：

```text
python -m unittest tests.test_pipeline -v
python -m unittest tests.test_ledger tests.test_packets tests.test_recheck -v
python -m unittest tests.test_report tests.test_evidence tests.test_distribution -v
python -m unittest discover -s tests -v
```

上述测试已实现并通过；另增加 tests/test_failures.py 验证并发、失败恢复与跨运行隔离。不要保留只匹配文案、标题或固定数组长度的测试作为主要正确性依据。

## 12. 成本与质量验收

运行时记录：各 packet 的必读字符数、各提交的字符数、证据批次数、重复验证缓存命中、阶段时间戳、补查次数和结束原因。token 仅记录宿主真实提供的值，未提供为 null；不能将字符数标成 token，不能声称程序可观测所有搜索调用。

机械验收：普通路径只有三个主要代理任务；无确认命令；不存在完整 M3 地图门槛；没有后续任务被要求读取未引用的所有证据和搜索日志；最终必有 M4 六部分。

真实质量验收另用保留案例：直接撞车、异名撞车、相似但贡献不同、证据不足、机制或实验存在问题。检查误判、决定性工作发现、引用支持度、研究对象忠实性与下一步价值。三个代理任务本身不保证研究质量；实际节省率需在相同模型和工具条件下测量后再报告。

## 13. 首版刻意不做

不做多模型路由、任意 DAG 调度、跨项目知识库、自动评分、自动全文爬虫、通用事件溯源系统或新确认流程。独立代理的创建继续交给宿主工具；代码只提供明确任务包和可检查状态。

实现的核心改动是降低固定执行成本，并把调研深度交给当前审查问题，同时保留来源与原始 idea 的可追溯性。

# 使用 Case 评估 IdeaPartner

本说明用于运行 `evals/cases/` 中的研究 idea Case，并对 IdeaPartner 的实际审查行为进行人工评估。它主要回答三个问题：

1. 流水线是否按照设计真实执行，而不是在一个上下文中生成一份看似完整的报告；
2. Skill 是否根据领域、贡献类型和成熟度改变审查路线；
3. M3–M5 是否找到了该 Case 真正需要审查的关键问题，而不是输出通用科研建议。

这些 Case 是诊断性测试，不是带有唯一正确结论的考试题。评估对象是审查过程、证据使用和判断边界，不是最终给出的 `go`、`revise` 或 `stop` 标签是否与预期相同。

## 1. 基本原则

一次规范评测应遵守以下约束：

- 一个 Case 使用一个全新的 Codex 任务和一个独立 run；不要在同一聊天上下文中连续测试多个 Case。
- 开始时只允许 IdeaPartner 读取 `idea.md`。
- `researcher-confirmation.md` 只能在 M1 定位卡已经展示后提供。
- `expected-review-behavior.md` 只能在 M7 最终报告已经生成后打开。
- `case.yaml` 仅用于记录测试属性，不得作为模型输入或 M1 的提示。
- M3 使用 live evidence verification。网络失败时可以保留候选来源，但不能让未验证来源支持 blocker、最终引文或强新颖性判断。
- 不要在运行中为了让结果更接近预期而临时补充提示。除规定的研究者检查点外，保持输入不变。
- 比较不同版本时固定 Case、模型、reasoning effort、工具权限和运行日期，并记录 Skill 的 Git commit。

最重要的防泄漏顺序是：

```text
idea.md
   ↓
M1 定位结果
   ↓
researcher-confirmation.md
   ↓
M2–M7 完整运行
   ↓
最终报告
   ↓
case.yaml + expected-review-behavior.md
```

如果执行者在最终报告前读取了预期行为，该次运行应标记为“输入污染”，不能作为有效结果。

## 2. 每个 Case 的文件

每个 Case 目录包含四个文件：

| 文件 | 用途 | 何时可见 |
|---|---|---|
| `idea.md` | 模拟研究者最初提交的 idea | M0 开始时 |
| `researcher-confirmation.md` | 模拟研究者对 M1 的确认与修正 | M1 展示之后 |
| `case.yaml` | 领域、成熟度、贡献类型和测试目标 | 最终报告之后 |
| `expected-review-behavior.md` | 人工评估参照 | 最终报告之后 |

`expected-review-behavior.md` 规定“应当出现的审查行为”和“不能出现的错误行为”，但不规定报告必须使用相同措辞，也不规定唯一最终结论。

## 3. 推荐方式：在 Codex 中运行完整 Skill

### 3.1 创建全新任务

每个 Case 新建一个 Codex 任务。不要使用已经讨论过该 Case 预期结果的任务，否则模型可能从聊天历史中获得答案。

在 IdeaPartner 仓库根目录开始，使用下面的提示，将 `<CASE_ID>` 和路径替换成实际值：

```text
请使用 $ideapartner 对下面的研究 idea 进行完整审查：

<IdeaPartner绝对路径>/evals/cases/<CASE_ID>/idea.md

这是一次受控评测。开始时只能读取 idea.md，不得读取同目录中的
case.yaml、researcher-confirmation.md 或 expected-review-behavior.md。
请使用正式的 checkpointed runtime 和隔离 worker；完成 M1 后展示完整
定位卡并停止，等待我提供研究者确认。不要自行模拟确认，也不要提前执行 M2。
```

建议让执行任务在回复中保留：

- run ID；
- run directory；
- 当前状态和等待中的 checkpoint；
- 最终验证结果；
- `07-final-report.md` 路径。

### 3.2 M1 检查点

IdeaPartner 展示 M1 后，先观察它是否独立识别了以下内容：

- 主要和相关领域；
- 问题场景与 track；
- 研究对象和范围；
- 核心困难；
- 主要/次要贡献类型；
- 成熟度及当前不应要求的内容；
- 不确定项和替代定位。

此时打开该 Case 的 `researcher-confirmation.md`，把其中内容作为新的研究者消息发送。不要在第一次提示中附带该文件。

如果确认文件对 M1 作了实质修正，IdeaPartner 应更新 M1、生成新版本并再次展示定位卡，而不是只把修正写进一条备注后继续。确认后的 M1 才能成为 M2–M7 的起点。

### 3.3 M2–M7

完成 M1 确认后，让 IdeaPartner继续正式工作流。正常顺序为：

```text
M2 route
  ↓
M3 foundation ─┐
M3 data ───────┼→ M3 synthesis
M3 frontier ───┘
  ↓
必要时执行 post-M3 重新定位检查点
  ↓
M4 reconstructed idea
  ↓
M5-A problem legitimacy ─┐
M5-B knowledge increment ┼→ M5-C logic/mechanism → M5-D researchability
  ↓
M6 challenge
  ↓
M7 synthesis
```

如果 M3 发现证据要求重新定位，仍然需要真实停止并等待研究者决定。此时只能依据 `idea.md`、已确认 M1 和已验证证据回应，不得查看预期行为文件。

### 3.4 完成条件

只有同时满足以下条件，运行才算完成：

- runtime 状态为完成；
- `validate` 成功；
- 不存在 stale artifact；
- M3 的决定性来源通过 live verification；
- 生成非空的 `07-final-report.md`；
- 最终报告中的文献相关判断能够回到 canonical M3 evidence claims。

## 4. 底层命令方式：用于调试运行时

正常评测优先使用 `$ideapartner`，因为 Codex supervisor 需要负责检查点、worker 隔离和研究者交互。只有在定位状态、任务包或提交校验错误时，才直接操作运行时。

以下示例使用 PowerShell，并以 Case 06 为例：

```powershell
$Runtime = (Resolve-Path "skills/research-idea-review/scripts/idea_review.py").Path
$CaseDir = (Resolve-Path "evals/cases/06-emerging-harmful-language-open-environments").Path
$RunId = "case-06-20260902-r1"

python $Runtime init "$CaseDir/idea.md" --run-id $RunId
$RunDir = ".idea-review/runs/$RunId"

python $Runtime status $RunDir
python $Runtime emit-task $RunDir m1-positioning
```

`emit-task` 会输出任务包路径。把该任务包交给一个全新的 worker context，worker 按包内 `output_contract.submission_path` 写入提交文件。之后执行：

```powershell
python $Runtime ingest $RunDir m1-positioning "$RunDir/submissions/m1-positioning.json"
python $Runtime status $RunDir
```

展示 M1 并取得研究者回复之后，才记录 checkpoint：

```powershell
$Confirmation = Get-Content "$CaseDir/researcher-confirmation.md" -Raw
python $Runtime confirm $RunDir --checkpoint positioning --note $Confirmation
```

后续对 `status` 返回的每个 `ready_task` 重复：

```powershell
python $Runtime emit-task $RunDir <task-id>
# 新 worker 执行任务包并写出 submission JSON
python $Runtime ingest $RunDir <task-id> <submission-json>
```

M3 discovery 的 `ingest` 默认使用 live verification。不要为了得到完整报告而随意改成 deferred；deferred 来源不能支持决定性结论。全部任务完成后执行：

```powershell
python $Runtime validate $RunDir
python $Runtime status $RunDir
```

直接运行时仍然必须保证每个科学子任务由新 worker 执行。命令行只负责状态和校验，不会替代 worker 的文献检索或科学判断。

## 5. 人工评估方法

最终报告生成后，打开该 Case 的 `expected-review-behavior.md`。评估分为协议层和语义层。

### 5.1 协议层：Pass/Fail

逐项确认：

- [ ] 运行开始时只有 `idea.md` 可见；
- [ ] M1 后真实停止并等待研究者确认；
- [ ] 研究者修正被写回新的 M1，而不是被忽略；
- [ ] M3 discovery 与 M5-A/B 均由新 worker 执行；可并行任务没有依赖共享的隐式上下文；
- [ ] 后续 worker 收到了完整、版本固定的上游 artifacts；
- [ ] 未验证来源没有支持 blocker、最终引文或“相关工作不存在”；
- [ ] M4 保留了 researcher-stated、evidence-supported、inferred 和 missing 的边界；
- [ ] M6 不超过三个真正可能改变判断的挑战；
- [ ] runtime validate 成功，且无 stale artifact；
- [ ] 最终报告文件存在且引用闭合。

任何涉及输入泄漏、伪造研究者确认或未验证证据支持决定性结论的问题，都应视为关键协议失败。此时不要继续比较报告文风。

### 5.2 语义层：逐项人工判断

对 `expected-review-behavior.md` 中每条“应出现”和“不应出现”行为进行判断。推荐使用简单的三级记录，而不是计算统一 idea 分数：

| 标记 | 含义 |
|---|---|
| `0` | 缺失、判断相反，或只给出与该 Case 无关的通用建议 |
| `1` | 有所涉及，但缺少机制拆解、证据、边界或可执行影响 |
| `2` | 具体识别了问题，说明其在依赖链中的作用，并给出证据、替代解释或改变判断的条件 |
| `N/A` | 后续确认该行为不适用于该 Case，并记录原因 |

不要用关键词匹配。例如报告出现“时间泄漏”四个字不代表已经命中 Case 06；只有当它进一步检查训练截点、模型预训练时间、检索语料时间或跨时间传播时，才说明审查行为真正形成。

### 5.3 建议记录模板

```markdown
# IdeaPartner Case 评估记录

## 运行信息
- Case ID：
- Skill commit：
- 模型与 reasoning effort：
- 日期：
- Run ID：
- Run directory：
- 是否存在输入污染：否 / 是（说明）

## 协议层
- 结果：Pass / Fail
- 失败项：

## M1 定位
- 正确识别：
- 需要 researcher confirmation 修正：
- 修正后是否进入后续依赖：

## 预期行为对照
| 行为编号或简述 | 0/1/2/N/A | 报告或 artifact 证据 | 备注 |
|---|---:|---|---|
| | | | |

## 关键错误
- 漏掉的核心问题：
- 错误 blocker：
- 无证据强判断：
- 成熟度或贡献类型误用：

## 有效输出
- 最有价值的领域先验：
- 最有价值的依赖链判断：
- 最可执行的下一步：

## 总结
- 本次运行证明了什么：
- 本次运行不能证明什么：
- 建议修改的最早模块：M1 / M2 / M3 / M4 / M5 / M6 / M7 / Case 本身
```

## 6. 与单轮 LLM 基线对照

如果目标是展示 IdeaPartner 相对于普通审查提示的价值，应在另一个全新任务中运行单轮基线。两边使用相同模型、reasoning effort、联网权限和同一份 `idea.md`，但基线不读取确认文件和预期行为。

基线提示可以固定为：

```text
请审查下面的研究 idea，分析其问题价值、新颖性、方法合理性、可行性、
实验设计和主要风险，并给出是否值得继续推进的结论。请检索必要的相关工作，
对文献相关判断提供可核查来源。

<idea.md 内容>
```

比较重点不是报告长度、标题数量或最终态度，而是：

- 是否正确识别贡献类型和成熟度；
- 是否找到机制上最近的工作而不是只有关键词相似；
- 是否命中 Case 的核心断裂点；
- 是否区分事实、研究者主张、模型推断和未知内容；
- 是否根据证据范围校准 blocker 和最终结论；
- 是否给出能够淘汰错误假设的下一步。

不应在看到两边结果后修改基线提示来帮助其中一方。若修改评测协议，应重新运行两边。

## 7. 不同评测强度

### 开发期冒烟测试

- 每个 Case 运行一次；
- 主要检查协议失败和明显语义退化；
- 适合每次较大工作流修改后使用。

### 模块回归测试

- 只重跑最能覆盖被修改模块的 Case；
- 修改前后保持模型、Case 和设置一致；
- 至少检查两个独立运行，避免把一次随机波动当作改进。

### 对外展示或较强效果声明

- 每个 Case 进行多次独立运行；
- 加入固定单轮基线；
- 由不知道运行版本的评估者盲评；
- 完整公开失败 Case，而不是只展示最好的一次；
- 报告模型版本、日期、工具权限、Skill commit 和证据检索失败。

即使全部 Case 通过，也只能说明 IdeaPartner 在这些受控场景中表现出预期审查行为，不能据此声称已经达到或超过领域专家同行评审。

## 8. 失败后如何定位

发现错误时，先找到最早产生错误的模块，不要直接在 M7 文案上补规则：

| 现象 | 优先检查 |
|---|---|
| 领域、对象、贡献类型或成熟度错误 | M1 |
| 检索方向偏离、没有覆盖碰撞范围 | M2 route |
| 最近工作缺失、来源不可靠、领域共识错误 | M3 |
| 把模型补全误写成研究者主张 | M4 |
| 关键断裂点未被发现、贡献类型没有改变问题 | M5 |
| 挑战只是重复意见，没有改变判断能力 | M6 |
| 最终结论与上游证据不一致 | M7 |
| 预期行为本身过度具体或依赖隐藏事实 | Case 设计 |

修改后保留原运行记录并创建新 run，不要覆盖旧结果。只有这样才能判断改动是否真正改善了行为，还是只改变了最终报告的措辞。

## 9. 最短执行清单

```text
[ ] 新建一个没有 Case 历史的 Codex 任务
[ ] 只提供 idea.md
[ ] M1 后停止
[ ] 再提供 researcher-confirmation.md
[ ] 完成 M2–M7，M3 使用 live verification
[ ] validate 成功并保存 07-final-report.md
[ ] 最后才打开 case.yaml 和 expected-review-behavior.md
[ ] 完成协议层与语义层人工记录
[ ] 保留 commit、模型、日期、run ID 和失败信息
```

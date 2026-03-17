# `sdd.plan` 入口式索引方案

## 你的目标定义

按你的预期，[`/sdd.plan`](../templates/commands/plan.md:21) 不再默认生成整套 planning artifacts，而是支持三类目标入口：

- [`/sdd.plan`](../templates/commands/plan.md:21) 生成或更新某个 `详细设计`
- [`/sdd.plan`](../templates/commands/plan.md:21) 生成或更新某个 `接口定义`
- [`/sdd.plan`](../templates/commands/plan.md:21) 生成或更新 [`data-model.md`](../templates/plan-template.md:60)

并且在第一次 run 内，[`/sdd.plan`](../templates/commands/plan.md:21) 只做两件事：

1. `Stage 0` 生成索引文件 `Shared Baseline`
2. `Stage 1` 生成索引文件 `Artifact Workset`

当这两个索引文件生成完成后，第一次 run 结束。

第二次调用同一个 [`/sdd.plan`](../templates/commands/plan.md:21) 时：

- 读取已有 `Shared Baseline`
- 读取已有 `Artifact Workset`
- 按当前目标工件执行生成或更新
- 工件写出后结束本次 run

---

## 一、重新定义 `sdd.plan`

新的 [`/sdd.plan`](../templates/commands/plan.md:21) 应被定义为：

> 一个面向目标工件的 planning 索引构建器，而不是完整 planning 套件生成器。

也就是说，它的职责不再是一次性推进：

- `research.md`
- [`data-model.md`](../templates/plan-template.md:60)
- `test-matrix.md`
- [`contracts/`](../templates/commands/plan.md:34)
- [`interface-details/`](../templates/commands/plan.md:35)

而是：

- 识别当前要处理的目标工件
- 建立该工件所需的共享输入索引
- 建立该工件所需的最小工作集索引
- 然后结束当前入口流程

---

## 二、入口模型

## 2.1 标准入口

建议把 [`/sdd.plan`](../templates/commands/plan.md:21) 固定成三类入口。

### 入口 A：`data-model`

示例：

- `sdd.plan 生成/更新 data-model`

含义：

- 目标工件是 [`data-model.md`](../templates/plan-template.md:60)
- 本次只为 [`data-model.md`](../templates/plan-template.md:60) 构建索引

### 入口 B：`接口定义`

示例：

- `sdd.plan 生成/更新 "xxxx" 接口定义`

含义：

- 目标工件是某一个单接口定义
- 这里建议把“接口定义”映射到单 contract 工件，即 [`contracts/`](../templates/commands/plan.md:34) 下的一个目标文件

### 入口 C：`详细设计`

示例：

- `sdd.plan 生成/更新 "xxxx" 详细设计`

含义：

- 目标工件是某一个单详细设计
- 这里建议把“详细设计”映射到单 `interface detail` 工件，即 [`interface-details/`](../templates/commands/plan.md:35) 下的一个目标文件

---

## 2.2 入口标准化结构

无论用户怎么输入，都先标准化成统一 intent：

- `action`: `generate_or_update`
- `artifact_kind`: `data_model` / `contract` / `interface_detail`
- `target_id`: `global` 或某个稳定接口标识
- `target_name`: 用户输入的目标名
- `scope`: `single_artifact`

这样 [`/sdd.plan`](../templates/commands/plan.md:21) 内部不再按自然语言分支，而是按标准 intent 分支。

---

## 三、内部 Stage 只做索引

## 3.1 Stage 0：生成 `Shared Baseline`

### 目标

为当前目标工件建立统一共享输入索引。

### 输出

建议输出到 planning 目录下的独立文件，例如：

- `shared-baseline.md`
- 或 `shared-baseline.json`

### 内容

`Shared Baseline` 只放“当前目标工件与后续相关任务共同复用的稳定输入”。

建议字段：

- `feature identity`
- `artifact intent`
- `spec authority refs`
- runtime constitution (`.specify/memory/constitution.md`; source mirror: [`templates/constitution-template.md`](../templates/constitution-template.md))
- repository-first baseline refs
- `canonical glossary`
- `artifact registry`
- `baseline blockers`

### 原则

- 只放索引，不放全量正文
- 只放稳定锚点，不放中间推理
- 只放共享输入，不放当前工件的局部细节

---

## 3.2 Stage 1：生成 `Artifact Workset`

### 目标

从 `Shared Baseline` 中裁切出当前目标工件的最小工作集。

### 输出

建议输出第二个索引文件，例如：

- `artifact-workset.md`
- 或 `artifact-workset.json`

### 内容

`Artifact Workset` 只描述“当前这个工件到底要读什么、产出什么、在什么条件下停止”。

建议字段：

- `artifact kind`
- `artifact target`
- `required source slices`
- `required anchors`
- `required upstream artifacts`
- `output contract`
- `stop conditions`

### 原则

- 一次只对应一个工件
- 不允许同一个 workset 同时服务多个接口定义
- 不允许同一个 workset 同时服务多个详细设计
- 如果目标标识不清楚，停在这里，不继续猜

---

## 3.3 第一次调用在 Stage 1 完成后结束

这是这个新模型最关键的地方：

第一次调用 [`/sdd.plan`](../templates/commands/plan.md:21) 时，到 `Shared Baseline` 与 `Artifact Workset` 落盘后就结束。

也就是说，第一次 run 不再继续自动推进：

- 生成完整 [`data-model.md`](../templates/plan-template.md:60)
- 生成一批 [`contracts/`](../templates/commands/plan.md:34)
- 生成一批 [`interface-details/`](../templates/commands/plan.md:35)

而是把“生成条件”和“最小上下文”准备好后停止。

## 3.4 第二次调用负责实际工件生成

第二次调用同一个 [`/sdd.plan`](../templates/commands/plan.md:21) 时，才真正进入目标工件生成。

建议第二次调用流程固定为：

1. 解析当前入口 intent
2. 校验 `Shared Baseline` 是否存在且与当前目标匹配
3. 校验 `Artifact Workset` 是否存在且与当前目标匹配
4. 只读取 workset 指定的最小切片
5. 生成或更新单个目标工件
6. 写回 artifact registry 或状态摘要
7. 结束

这样就形成了明确的两段式协议：

- 第一次调用：建索引
- 第二次调用：按索引生成工件

---

## 四、三类入口对应的索引差异

## 4.1 `data-model` 入口

### `Shared Baseline`

应包含：

- feature 标识
- 与 domain backbone 相关的 `spec` refs
- runtime constitution (`.specify/memory/constitution.md`; source mirror: [`templates/constitution-template.md`](../templates/constitution-template.md))
- repository-first baseline 中与边界和实体有关的 refs
- glossary
- 已存在 artifact registry

### `Artifact Workset`

应包含：

- lifecycle anchors
- entity anchors
- invariant candidate refs
- relevant research refs
- [`data-model.md`](../templates/plan-template.md:60) 的输出约束
- 停止条件，如缺少 state anchor、术语冲突

---

## 4.2 `接口定义` 入口

这里建议直接等价于“单 contract 工件”。

### `Shared Baseline`

应包含：

- feature 标识
- glossary
- frozen tuple index
- contract registry
- facade 和 DTO anchor index

### `Artifact Workset`

应包含：

- 当前目标接口标识
- 对应 `Operation ID`
- facade method ref
- request response DTO refs
- relevant `TM` 与 `TC` refs
- contract 输出约束
- 停止条件，如 tuple 不稳定、DTO anchor 缺失

---

## 4.3 `详细设计` 入口

这里建议直接等价于“单 interface detail 工件”。

### `Shared Baseline`

应包含：

- feature 标识
- glossary
- frozen tuple index
- contract registry
- detail registry
- collaborator anchor index

### `Artifact Workset`

应包含：

- 当前 detail 目标标识
- 对应 contract ref
- relevant data-model anchors
- relevant research constraints
- collaborator refs
- sequence 与 UML 输出约束
- 停止条件，如 contract 缺失、collaborator anchor 缺失

---

## 五、为什么必须分成两个索引文件

## `Shared Baseline`

负责解决“统一输入口径”问题。

也就是：

- 当前工件依赖哪些稳定权威来源
- 这些来源的最小共享锚点是什么
- 本次 planning run 的公共约束是什么

## `Artifact Workset`

负责解决“最小执行上下文”问题。

也就是：

- 当前工件到底要补读哪些切片
- 需要哪些锚点
- 产出边界是什么
- 什么时候必须停止

一句话：

- [`Shared Baseline`](plans/plan-entry-baseline-artifact-cards-plan.md) 负责统一输入
- [`Artifact Workset`](plans/plan-entry-baseline-artifact-cards-plan.md) 负责最小执行

---

## 六、这套模型和原 stage 语义的关系

原 [`templates/commands/plan.md`](../templates/commands/plan.md:29) 的大 stage 不需要完全消失，但它们不再是一次调用里的直接流程，而是被拆成“两次调用”。

更合理的层级是：

### 第一次调用：索引准备层

- `Stage 0` -> `Shared Baseline`
- `Stage 1` -> `Artifact Workset`

### 第二次调用：工件执行层

由同一个 [`/sdd.plan`](../templates/commands/plan.md:21) 根据索引去生成或更新实际工件：

- [`data-model.md`](../templates/plan-template.md:60)
- 单 [`contracts/`](../templates/commands/plan.md:34) 工件
- 单 [`interface-details/`](../templates/commands/plan.md:35) 工件

所以你的方案本质上是在 [`/sdd.plan`](../templates/commands/plan.md:21) 内部增加一个更上层的“索引前置阶段”，并把实际工件生成延后到第二次调用。

---

## 七、我对你这个方案的收敛定义

如果严格按你的预期落地，那么 [`/sdd.plan`](../templates/commands/plan.md:21) 的新定义应该是：

> 第一次调用接收一个目标工件入口，先执行 `Stage 0` 生成 `Shared Baseline`，再执行 `Stage 1` 生成 `Artifact Workset`，两个索引文件落盘后结束；第二次调用仍由同一个 [`/sdd.plan`](../templates/commands/plan.md:21) 承接，按索引生成或更新该目标工件。

这比“完整 planning 一次跑完”更接近你要的模式，因为它把：

- 统一输入
- 最小工作集
- 单工件目标
- 早停边界

四件事都固定下来了。

---

## 八、建议 Todo

- [ ] 把 [`templates/commands/plan.md`](../templates/commands/plan.md:21) 的入口定义改成目标工件式入口
- [ ] 固定三类标准目标：[`data-model.md`](../templates/plan-template.md:60)、单接口定义、单详细设计
- [ ] 定义 `Shared Baseline` schema
- [ ] 定义 `Artifact Workset` schema
- [ ] 明确第一次调用的 `Stage 0` 只生成 `Shared Baseline`
- [ ] 明确第一次调用的 `Stage 1` 只生成 `Artifact Workset`
- [ ] 明确第一次调用在两个索引文件落盘后结束
- [ ] 定义第二次调用如何校验并消费索引
- [ ] 定义第二次调用只生成一个目标工件的规则

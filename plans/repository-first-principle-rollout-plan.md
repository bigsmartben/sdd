# 仓库优先原则总结与落地方案

## 一、仓库优先原则的简练归纳

建议把现有仓库优先约束收敛为下面这段可直接下游复用的规则文本：

> **Repository-First Principle**
> 所有仓库语义判断必须先基于可追溯的仓库事实，而不是说明文档、生成产物或推测。
> 仓库分析的核心目标只有三类：识别源代码目录、识别依赖矩阵、识别组件能力边界。
> 这些结论只能由源码锚点与工程装配事实推出；辅助文档只能作为背景输入，不能提升为语义证据。

如果要再压缩成提示词级别，可使用下面这个版本：

> **Prompt Form**
> 先做仓库事实分析，再做语义推断。
> 只为 代码目录、依赖矩阵、组件边界 三类结论扫描仓库。
> 只接受源码锚点与工程装配事实；拒绝把文档、计划、生成文件提升为 repo evidence。

## 二、原则的可执行定义

结合现有 [`Repo-Anchor Evidence Protocol`](../templates/constitution-template.md#repo-anchor-evidence-protocol)，建议把仓库优先落实为四条硬规则。

### 1. 分析目标固定

仓库分析只服务于三类核心结论：

- 源代码目录
- 技术依赖矩阵
- 组件或领域能力边界

不允许为了补充 narrative、示例、历史说明而扩展扫描面。

### 2. 证据来源分层

允许作为仓库语义证据的来源只有两类：

- **源码锚点**：如 [`src/`](src) 下的包、类、接口、方法、实体、调用点
- **工程装配事实**：如根/子模块 [`pom.xml`](pom.xml) 一类构建文件，用于识别依赖声明、模块装配、入口与打包边界

其中：

- 源码锚点负责证明 组件能力边界 与真实职责归属
- 工程装配事实负责证明 依赖矩阵、模块关系、构建边界

### 3. 禁止证据提升

以下内容可按命令需要读取，但不得提升为 repo semantic evidence：

- [`README.md`](README.md)
- [`docs/`](docs)
- [`plans/`](plans)
- [`templates/`](templates)
- [`tests/`](tests)
- 生成产物与 feature 产物，例如 `spec.md`、`plan.md`、`data-model.md`、`contracts/`、`interface-details/`、`tasks.md`

### 4. 产物职责分离

仓库扫描生成的产物各自只承载一种职责，不互相替代。

- `technical-dependency-matrix.md` = 技术事实清单
- `domain-boundary-responsibilities.md` = 业务边界说明
- `module-invocation-spec.md` = 执行约束与治理规则

## 三、三个核心产物如何承接仓库优先原则

### [`technical-dependency-matrix.md`](plans/repository-first-principle-rollout-plan.md)

**定位**：仓库级技术依赖事实表。

**仓库优先落点**：

- 只从根/子模块 [`pom.xml`](pom.xml) 提取依赖事实
- 只覆盖 2方/3方依赖
- 不从源码命名、文档描述、计划文本中反推依赖版本
- `unresolved` 与版本分叉必须保留，作为治理信号

**输出语义**：

它回答的是 依赖了什么、版本来自哪里、被哪些模块使用，不回答业务职责归属。

### [`domain-boundary-responsibilities.md`](plans/repository-first-principle-rollout-plan.md)

**定位**：领域边界职责说明。

**仓库优先落点**：

- 只从领域层、持久化层、接入层源码锚点归纳职责边界
- `Core Entity Anchors` 必须写成 `path::symbol`
- `2nd-Party Collaboration Anchor` 只能记录协作接入锚点，不能替代依赖矩阵
- 不通过 POM 依赖方向推导业务职责

**输出语义**：

它回答的是 谁负责什么业务语义、关键实体证据是什么，不回答依赖治理。

### [`module-invocation-spec.md`](plans/repository-first-principle-rollout-plan.md)

**定位**：模块调用与分层约束规范。

**仓库优先落点**：

- 调用方向必须对齐真实模块结构，如 `web/service/manager/dao/api/common`
- `Allowed Direction` 与 `Forbidden Direction` 必须建立在源码分层与模块装配事实上
- `Dependency Governance Rules` 必须引用技术依赖矩阵中的分叉版本与 `unresolved` 治理信号
- 不允许从说明文档直接发明调用链规则

**输出语义**：

它回答的是 应该怎样调用、哪些调用被禁止、发现依赖治理异常后如何处理。

## 四、推荐写入宪法的精简文本

建议把 [`templates/constitution-template.md`](../templates/constitution-template.md#repo-anchor-evidence-protocol) 中的 `Repo-Anchor Evidence Protocol` 收敛增强为下面这组短规则：

1. 仓库分析只为 源代码目录、依赖矩阵、组件能力边界 三类结论服务。
2. 这些结论只能由 源码锚点 与 工程装配事实 共同支撑。
3. 源码锚点用于证明职责与边界；工程装配事实用于证明依赖与模块关系。
4. 文档、计划、测试与生成产物不得提升为 repo semantic evidence。
5. 下游产物必须按职责分离原则生成，事实清单、业务边界、执行约束不得互相替代。

## 五、落地实施方案

### 阶段 A：先收紧宪法定义

在 [`templates/constitution-template.md`](../templates/constitution-template.md#repo-anchor-evidence-protocol) 的 `Repo-Anchor Evidence Protocol` 中补充三件事：

- 扫描目标固定为 代码目录、依赖矩阵、组件能力边界
- 合法证据来源固定为 源码锚点 + 工程装配事实
- 三个派生产物的职责边界固定，不允许互相替代

### 阶段 B：在 [`templates/commands/plan.md`](templates/commands/plan.md:103) 落地下游引用

`/sdd.plan` 应增加一条紧凑规则：

- 当需要生成依赖、边界、调用约束相关内容时，先定位证据类型
- 依赖矩阵只读 [`pom.xml`](pom.xml)
- 组件职责边界只读源码锚点
- 调用分层规范必须联合源码分层与依赖治理事实生成
- feature 产物只能做 planning input，不能反向证明仓库边界

同时在阶段产物投影中显式要求生成或引用：

- `technical-dependency-matrix.md`
- `domain-boundary-responsibilities.md`
- `module-invocation-spec.md`

### 阶段 C：在 [`templates/commands/analyze.md`](templates/commands/analyze.md:41) 落地审计

`/sdd.analyze` 应新增或强化三类检查：

1. **Dependency Evidence Check**
   - 依赖矩阵是否仅由 [`pom.xml`](pom.xml) 推导
   - 是否保留 `unresolved` 与版本分叉

2. **Boundary Evidence Check**
   - 领域职责边界是否由源码锚点证明
   - 是否错误使用文档或计划文件作为边界证据

3. **Invocation Governance Check**
   - 模块调用规范是否与真实模块结构一致
   - 是否把依赖矩阵中的治理信号接入调用治理规则

若失败，统一记为 `repo-anchor misuse`、`evidence drift` 或等价高优先级问题。

### 阶段 D：在 [`templates/commands/tasks.md`](templates/commands/tasks.md) 与 [`templates/commands/implement.md`](templates/commands/implement.md) 约束执行期使用

执行期不负责重新定义边界，只负责消费上游结论：

- 任务分解引用 `technical-dependency-matrix.md` 做依赖治理任务投影
- 任务分解引用 `domain-boundary-responsibilities.md` 做模块归属与接口分工投影
- 执行过程引用 `module-invocation-spec.md` 做调用方向与禁止穿透检查
- 如运行时发现结论缺乏源码/POM 证据，应回退到 `/sdd.plan` 或 `/sdd.analyze` 修正，而不是在 `/sdd.tasks`、`/sdd.implement` 现场补推语义

## 六、下游使用方式

### 在 `/sdd.plan` 中的使用

建议把三个产物作为 planning 阶段的标准仓库分析输出：

- `technical-dependency-matrix.md`：为依赖治理、版本风险、模块装配提供输入
- `domain-boundary-responsibilities.md`：为 capability map、contract scope、任务分工提供输入
- `module-invocation-spec.md`：为 interface design、implementation boundary、review checklist 提供输入

### 在 `/sdd.analyze` 中的使用

把三者作为一致性审计对象：

- 事实表是否真来自 POM
- 边界表是否真来自源码锚点
- 调用规范是否真与模块结构和依赖治理联动

### 在 `/sdd.tasks` 中的使用

把三者投影为任务来源：

- 依赖治理类任务来自 `technical-dependency-matrix.md`
- 组件归属与接口协作类任务来自 `domain-boundary-responsibilities.md`
- 分层调用整改与验证类任务来自 `module-invocation-spec.md`

### 在 `/sdd.implement` 中的使用

把三者作为实现边界基线：

- 修改依赖时对照技术依赖矩阵
- 修改职责归属时对照领域边界职责文档
- 新增或调整调用链时对照模块调用规范

## 七、最小可执行实施清单

- [ ] 收敛 [`templates/constitution-template.md`](../templates/constitution-template.md#repo-anchor-evidence-protocol) 的仓库优先规则，固定三类分析目标与两类证据来源
- [ ] 在 [`templates/commands/plan.md`](templates/commands/plan.md:103) 增加 三类结论 -> 三个产物 的生成映射
- [ ] 在 [`templates/commands/analyze.md`](templates/commands/analyze.md:45) 增加 针对依赖矩阵、边界职责、调用规范 的证据审计
- [ ] 在 [`templates/commands/tasks.md`](templates/commands/tasks.md) 增加对这三个产物的任务投影说明
- [ ] 在 [`templates/commands/implement.md`](templates/commands/implement.md) 增加对这三个产物的执行约束引用
- [ ] 明确 `README`、`docs`、计划文件、生成文件 只能作辅助上下文，不能作仓库事实证据

## 八、推荐实施顺序

1. 先修改 [`templates/constitution-template.md`](../templates/constitution-template.md#repo-anchor-evidence-protocol)
2. 再修改 [`templates/commands/plan.md`](templates/commands/plan.md:103)
3. 再修改 [`templates/commands/analyze.md`](templates/commands/analyze.md:45)
4. 最后补齐 [`templates/commands/tasks.md`](templates/commands/tasks.md) 与 [`templates/commands/implement.md`](templates/commands/implement.md)

这样能先固定原则，再固定生成入口，最后固定审计与执行消费路径。

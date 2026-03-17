# 仓库优先原则落地实施方案

## 目标

把 仓库优先 从抽象约束，落地成一条可执行链路：

1. 宪法定义统一规则
2. `/sdd.plan` 依据规则生成仓库分析产物
3. `/sdd.analyze` 依据规则审计证据来源与投射质量
4. `/sdd.tasks` 与 `/sdd.implement` 只消费已证明结论，不现场补推仓库语义

## 实施范围

### 第一批必须修改

- `templates/constitution-template.md`
- `templates/commands/plan.md`
- `templates/commands/analyze.md`

### 第二批承接修改

- `templates/commands/tasks.md`
- `templates/commands/implement.md`

### 第三批可选补齐

- `templates/plan-template.md`
- `templates/tasks-template.md`
- 相关 planning templates 如 `templates/research-template.md`

## 核心落地原则

### 1. 固定仓库分析目标

所有仓库分析只服务于三类结论：

- 源代码目录
- 技术依赖矩阵
- 组件或领域能力边界

### 2. 固定证据来源

只允许两类证据：

- 源码锚点
- 工程装配事实

说明：

- 源码锚点负责证明职责边界、实体锚点、调用关系
- 工程装配事实负责证明依赖矩阵、模块关系、构建装配

### 3. 固定三个派生产物

`/sdd.plan` 需要产出或显式引用以下三类标准产物：

- `technical-dependency-matrix.md`
- `domain-boundary-responsibilities.md`
- `module-invocation-spec.md`

### 4. 固定禁止提升来源

以下内容可以读，但不能提升为 repo semantic evidence：

- `README.md`
- `docs/**`
- `tests/**`
- `plans/**`
- `templates/**`
- feature 产物，如 `spec.md`、`plan.md`、`data-model.md`、`contracts/`、`interface-details/`、`tasks.md`

## 文件级实施方案

## A. `templates/constitution-template.md`

### 修改目标

增强 `Repo-Anchor Evidence Protocol`，把规则收敛为简练且可执行的版本。

### 需要写入的规则

1. 仓库分析只为 代码目录、依赖矩阵、组件能力边界 三类结论服务。
2. 三类结论只能由 源码锚点 与 工程装配事实 支撑。
3. 依赖矩阵来自工程装配事实；组件能力边界来自源码锚点。
4. 文档、计划、测试与生成产物不得提升为 repo semantic evidence。
5. 三个下游产物职责固定，互不替代：
   - `technical-dependency-matrix.md`
   - `domain-boundary-responsibilities.md`
   - `module-invocation-spec.md`

### 交付标准

- 规则不冗长
- 能直接被下游命令引用
- 不写命令级实现细节

## B. `templates/commands/plan.md`

### 修改目标

把 仓库优先 转成 `/sdd.plan` 的显式生成规则。

### 需要增加的内容

1. 当生成 依赖矩阵、边界职责、调用规范 相关内容时，必须先判断证据类型。
2. `technical-dependency-matrix.md` 只允许从根/子模块 `pom.xml` 提取。
3. `domain-boundary-responsibilities.md` 只允许从领域层、持久化层、接入层源码锚点归纳。
4. `module-invocation-spec.md` 必须同时参考真实模块结构与依赖治理事实生成。
5. feature 产物只能作为 planning input，不能反向证明仓库边界。

### 在命令中新增的产物投影要求

- `technical-dependency-matrix.md`
- `domain-boundary-responsibilities.md`
- `module-invocation-spec.md`

### 交付标准

- 明确 三类结论 对应 三类产物
- 明确 每类产物的唯一证据来源
- 明确 supporting input 不可提升为 repo anchor

## C. `templates/commands/analyze.md`

### 修改目标

把 仓库优先 转成审计规则，而不是泛泛的 repo-anchor misuse 描述。

### 需要增加的检查项

#### 1. Dependency Evidence Check

检查：

- `technical-dependency-matrix.md` 是否只基于 `pom.xml`
- 是否保留 `Version Source`
- 是否保留版本分叉与 `unresolved`

#### 2. Boundary Evidence Check

检查：

- `domain-boundary-responsibilities.md` 是否由源码锚点支持
- `Core Entity Anchors` 是否为 `path::symbol`
- `2nd-Party Collaboration Anchor` 是否只作为协作锚点，不替代依赖矩阵

#### 3. Invocation Governance Check

检查：

- `module-invocation-spec.md` 是否匹配真实模块分层
- 是否包含 `Allowed Direction`
- 是否包含 `Forbidden Direction`
- 是否包含 `Dependency Governance Rules`
- 是否把版本分叉与 `unresolved` 接入治理规则

### 违规归类

- 证据来源错误 -> `repo-anchor misuse`
- 产物职责串位 -> `evidence drift`
- 调用规则与模块结构不一致 -> 高优先级语义问题

## D. `templates/commands/tasks.md`

### 修改目标

任务分解只消费上游已证明结论，不现场补充仓库分析。

### 需要增加的使用规则

- 依赖治理类任务来自 `technical-dependency-matrix.md`
- 组件归属与协作任务来自 `domain-boundary-responsibilities.md`
- 分层调用整改与验证任务来自 `module-invocation-spec.md`
- 如果证据不足，回退到 `/sdd.plan` 或 `/sdd.analyze`

## E. `templates/commands/implement.md`

### 修改目标

实现阶段把三个产物作为执行边界基线。

### 需要增加的使用规则

- 修改依赖时对照 `technical-dependency-matrix.md`
- 修改职责归属时对照 `domain-boundary-responsibilities.md`
- 修改调用链时对照 `module-invocation-spec.md`
- 不允许在实现阶段用文档或计划文件补推仓库语义

## 三个产物的最终生成规格

## 1. `technical-dependency-matrix.md`

### 定位

仓库级技术依赖事实表，用于依赖治理与 planning 投影输入。

### 数据源

- 根/子模块 `pom.xml`

### 范围

- 仅 2方/3方依赖
- 排除仓内一方模块互相依赖
- 单表统一输出

### 必填字段

- `Dependency (G:A)`
- `Type`
- `Version`
- `Scope`
- `Version Source`
- `Used By Modules`

### 质量要求

- 可追溯到 POM
- 保留版本分叉
- 保留 `unresolved`
- 不做静默修正

## 2. `domain-boundary-responsibilities.md`

### 定位

领域边界职责说明，用于明确 谁负责什么业务语义。

### 数据源

- 领域层、持久化层、接入层源码锚点

### 范围

- 只到领域边界级
- 不下钻子域细节

### 必填字段

- `Domain Boundary`
- `Responsibilities`
- `Core Entity Anchors`
- `2nd-Party Collaboration Anchor`

### 约束

- 不描述依赖方向
- 只描述职责边界与实体证据
- 二方信息只作为协作锚点，不替代依赖矩阵

## 3. `module-invocation-spec.md`

### 定位

模块调用与分层约束规范，用于实施与评审的调用边界基线。

### 固定结构

1. `Allowed Direction`
2. `Forbidden Direction`
3. `Dependency Governance Rules`

### 表达要求

- 使用 MUST 或 SHOULD
- 必须与实际模块结构一致
- 必须与依赖矩阵联动
- 分叉版本与 `unresolved` 必须进入治理规则

## 实施顺序

- [ ] 第一步：修改 `templates/constitution-template.md`
- [ ] 第二步：修改 `templates/commands/plan.md`
- [ ] 第三步：修改 `templates/commands/analyze.md`
- [ ] 第四步：修改 `templates/commands/tasks.md`
- [ ] 第五步：修改 `templates/commands/implement.md`
- [ ] 第六步：补充相关模板或文档中的引用说明

## 实施完成判定

满足以下条件即可认为落地完成：

- 宪法中已存在简练且可执行的仓库优先规则
- `/sdd.plan` 能按规则生成三个标准产物
- `/sdd.analyze` 能审计三个产物的证据来源与职责边界
- `/sdd.tasks` 与 `/sdd.implement` 只消费这些结论，不再现场补推仓库语义
- 三个产物的定位、字段、结构、职责边界保持稳定一致

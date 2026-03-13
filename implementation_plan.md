# Implementation Plan

[Overview]
梳理并审计 Spec Kit 中 `/speckit.plan` 及其上下游关联工件的全链路 review 正确性现状，产出一份仅包含现状评估、风险识别与缺口清单的审计方案，而不引入任何新功能实现。

本次工作的目标不是修改生成逻辑，也不是新增校验器，而是把当前仓库中与“计划生成是否正确、是否可 review、是否可追溯、是否能发现错误”直接相关的链路完整拆开。结合现有实现，`/speckit.plan` 主要由命令模板、计划模板、setup 脚本、CLI 初始化逻辑以及后续 `/speckit.analyze` 的只读分析能力共同构成，因此“全链路 review 正确性”不能只看单个模板文件，而需要同时审视输入装配、阶段定义、约束声明、下游消费方式、现有测试覆盖和缺失的断言点。

从当前代码看，仓库已经具备部分“正确性 review”基础：`templates/commands/plan.md` 对 Stage 0~4 的输出和边界规定较细，`templates/commands/analyze.md` 提供了 spec/plan/tasks 三工件一致性分析能力，`scripts/bash/setup-plan.sh` 与 `scripts/powershell/setup-plan.ps1` 负责 plan 文件的初始化，`src/specify_cli/__init__.py` 负责命令分发、模板安装与 agent skill 生成。但这些能力当前更偏“流程定义”和“命令包装”，缺少一份面向仓库维护者的、聚焦 correctness 的现状审计结果：哪些环节有强约束，哪些只停留在文档层，哪些缺乏自动化断言，哪些存在跨工件语义漂移风险。

因此，本次计划的高层方式是：以“只审计、不改功能”为前提，定义一个专门的 correctness audit 输出物，逐项检查命令定义、模板结构、脚本行为、CLI 注册与测试覆盖之间的一致性，再将发现整理为结构化缺口清单。该方案应尽量复用现有 read-only 分析心智模型，避免把治理噪音混入业务/设计正文，同时让后续实现者在进入 ACT MODE 后可以直接据此补齐审计文档、补充必要测试，或在未来单独立项增加自动化校验。

[Types]
本次不涉及运行时代码类型系统变更，但需要定义审计输出的数据结构与分类口径，以保证现状审计结果稳定、可复核、可扩展。

建议在审计文档中采用以下逻辑数据结构（文档结构，不是 Python 运行时类型）：

1. `AuditScope`
   - `chain_segment: string`
     - 取值建议：`plan-command`、`plan-template`、`setup-script`、`cli-registration`、`downstream-analysis`、`test-coverage`
   - `included_files: string[]`
     - 必须为仓库内绝对或仓库相对路径
   - `review_goal: string`
     - 描述该段链路的正确性审计目标
   - 校验规则：`included_files` 不能为空；`review_goal` 必须能被人工验证，不允许写成泛泛口号

2. `CorrectnessCheckItem`
   - `check_id: string`
     - 建议格式：`PC-*`（Plan Correctness）
   - `area: string`
     - 例如：`input-contract`、`artifact-boundary`、`stage-consistency`、`script-behavior`、`test-assertion`
   - `statement: string`
     - 需要 review 的事实或约束陈述
   - `source_of_truth: string[]`
     - 对应源码/模板/脚本/测试文件路径
   - `verification_method: string`
     - 例如：静态比对、模板断言、CLI 集成测试、文档一致性检查
   - `status: enum`
     - `covered` / `partial` / `missing`
   - `risk_level: enum`
     - `critical` / `high` / `medium` / `low`
   - `gap_summary: string`
     - 当 `status != covered` 时必填
   - 校验规则：`check_id` 唯一；`missing` 状态必须有 `gap_summary`；`critical` 必须能映射到具体链路断点

3. `GapRecord`
   - `gap_id: string`
     - 建议格式：`GAP-*`
   - `title: string`
   - `affected_chain_segments: string[]`
   - `evidence: string[]`
   - `impact: string`
   - `recommendation: string`
   - `automation_candidate: boolean`
   - 校验规则：`evidence` 至少包含 1 个具体文件或符号锚点；`recommendation` 必须可执行

4. `CoverageSnapshot`
   - `dimension: string`
     - 例如：`template-vs-script`、`template-vs-analyze`、`docs-vs-tests`
   - `covered_by: string[]`
   - `not_covered_by: string[]`
   - `notes: string`
   - 作用：统一表达“当前 correctness review 被谁覆盖、没被谁覆盖”

这些结构只用于审计文档表达，不要求在 `src/specify_cli/` 中新增类或 dataclass，避免把“审计表达层”误实现为“运行时代码层”。

[Files]
本次文件变更以新增审计规划文档为主，不应修改现有 CLI 或模板逻辑。

详细拆分如下：

- 新建文件
  - `/home/ben/project/spec-kit/implementation_plan.md`
    - 用途：记录本次“全链路 review 正确性现状审计与缺口清单”的完整实施计划
  - 建议后续在 ACT MODE 中新增一个审计结果文档（路径建议二选一，由实现者择一）
    - `docs/plan-correctness-audit.md`
      - 面向仓库维护者的长期说明文档，适合沉淀规则与缺口现状
    - 或 `reports/plan-correctness-audit.md`
      - 若团队更倾向一次性审计报告，可置于 reports 目录（若该目录不存在则新建）

- 可能需要读取但不建议修改的既有文件
  - `templates/commands/plan.md`
    - 审计 Stage 0~4 语义、输入输出、边界与停止条件定义
  - `templates/plan-template.md`
    - 审计计划产物结构是否支撑 correctness review
  - `templates/commands/analyze.md`
    - 审计现有只读分析能力是否覆盖 plan correctness 的关键问题
  - `scripts/bash/setup-plan.sh`
    - 审计 shell 侧 plan 初始化行为与 JSON 输出契约
  - `scripts/powershell/setup-plan.ps1`
    - 审计 PowerShell 侧同构行为是否一致
  - `src/specify_cli/__init__.py`
    - 审计 CLI 中 plan/analyze/skills 注册与帮助文本是否一致
  - `tests/hooks/plan.md`
    - 审计 hooks 测试上下文是否覆盖 plan 阶段正确性
  - `tests/test_ai_skills.py`
    - 审计 plan 命令/skill 包装覆盖
  - `tests/test_cursor_frontmatter.py`
    - 审计 plan 相关 agent context/frontmatter 生成行为

- 不建议删除、移动的文件
  - 当前阶段不删除任何文件
  - 当前阶段不移动任何文件

- 配置文件更新
  - 当前阶段无依赖版本、构建配置或 CLI 配置更新
  - 若后续决定把审计纳入 CI，再单独修改 `pyproject.toml` 或 GitHub workflow；本计划不包含该实现

[Functions]
本次不规划新增运行时业务函数，重点是明确后续审计实现可能涉及的文档生成与测试补强点。

详细拆分如下：

- 新函数
  - 无必须新增函数
  - 如果在后续 ACT MODE 中决定用脚本自动汇总审计结果，才可考虑新增辅助函数，但不属于本次“现状审计”必需范围

- 重点审计的既有函数
  - `init()` — `src/specify_cli/__init__.py`
    - 需要确认 `/speckit.plan` 所依赖模板与命令在初始化后是否能被正确安装到各 agent 目录
    - 需要检查 `--ai-skills` 路径是否改变 plan 命令/技能的最终落点，进而影响 review 路径
  - `install_ai_skills()` — `src/specify_cli/__init__.py`
    - 需要确认 `speckit.plan` 模板在 skill 形态下是否保留足够 frontmatter/body 语义，避免 correctness review 信息丢失
  - `_build_ai_assistant_help()` — `src/specify_cli/__init__.py`
    - 需要确认命令帮助与真实 agent 配置同步，避免 review 范围误判
  - 无名 shell 主流程 — `scripts/bash/setup-plan.sh`
    - 需要确认 JSON 输出字段 `FEATURE_SPEC`/`IMPL_PLAN`/`SPECS_DIR`/`BRANCH`/`HAS_GIT` 与 `templates/commands/plan.md` 的消费预期一致
  - 无名 PowerShell 主流程 — `scripts/powershell/setup-plan.ps1`
    - 需要确认与 bash 版本行为对齐

- 不涉及移除的函数
  - 本次不移除任何函数
  - 不进行 API 迁移

[Classes]
本次不计划新增或修改运行时类；类层面的工作仅限于识别哪些现有类与 correctness review 链路有关。

详细拆分如下：

- 新类
  - 无

- 需重点审计的既有类
  - `StepTracker` — `src/specify_cli/__init__.py`
    - 虽不直接负责 `/speckit.plan` 内容正确性，但影响用户对 plan 初始化阶段成功/失败的感知，应纳入“链路可观察性”审计
  - `BannerGroup` — `src/specify_cli/__init__.py`
    - 不是 correctness 核心，但属于 CLI 呈现层，可忽略其实现正确性，避免审计范围失焦

- 不涉及移除的类
  - 无

[Dependencies]
本次不涉及新增依赖或升级依赖，审计工作应建立在现有 Python 3.11 + Typer/Rich/HTTPX/PyYAML/pytest 体系之上。

依赖层面需要记录的仅有两点：

1. 当前 correctness review 主要依赖仓库内静态模板、脚本与 pytest 测试，不依赖新增第三方包。
2. 如果后续决定把“审计结果生成”自动化为 CLI 子命令或 CI 检查，再评估是否需要引入 Markdown 解析/结构化校验库；本次计划明确不做该扩展。

[Testing]
测试策略应聚焦“现状审计的证据完整性”和“缺口识别可复核性”，而不是新增功能测试。

建议测试/验证方式如下：

1. 文档级审计验证
   - 为每个审计结论绑定至少一个源码或模板锚点
   - 审核 `templates/commands/plan.md`、`templates/plan-template.md`、`scripts/bash/setup-plan.sh`、`scripts/powershell/setup-plan.ps1`、`templates/commands/analyze.md` 之间是否存在契约不一致

2. 现有测试覆盖复盘
   - 检查 `tests/test_ai_skills.py` 是否覆盖 `speckit.plan` 作为 skill/command 的生成正确性
   - 检查 `tests/test_cursor_frontmatter.py` 是否覆盖 plan 相关 context 汇总正确性
   - 识别缺口：是否缺少针对 `/speckit.plan` 文本模板结构本身的断言；是否缺少 setup-plan 双脚本等价性断言；是否缺少 plan/analyze 之间语义衔接断言

3. 若后续进入实现阶段，可新增但当前不实现的测试文件建议
   - `tests/test_plan_command_contract.py`
     - 校验 `templates/commands/plan.md` 的脚本字段、阶段描述、输出声明与模板结构约束
   - `tests/test_setup_plan_scripts_parity.py`
     - 校验 bash 与 PowerShell 输出 JSON 字段、分支校验与模板复制行为一致
   - `tests/test_plan_analyze_review_coverage.py`
     - 校验 analyze 命令是否能覆盖 plan correctness 的关键审计点，或至少显式暴露未覆盖项

4. 验证策略
   - 当前阶段以人工审计 + 结构化缺口列表为主
   - 若后续补测试，优先补“契约一致性断言”，而非端到端大而全快照测试

[Implementation Order]
实施顺序应先完成静态证据审计，再形成缺口分类，最后决定是否需要进入后续自动化实现阶段。

1. 盘点 `/speckit.plan` 全链路参与文件，冻结本次审计范围与不在范围内的部分。
2. 对 `templates/commands/plan.md` 与 `templates/plan-template.md` 做逐段对照，识别阶段定义、输出声明、边界约束是否自洽。
3. 对 `scripts/bash/setup-plan.sh` 与 `scripts/powershell/setup-plan.ps1` 做等价性审计，确认计划初始化契约是否一致。
4. 对 `src/specify_cli/__init__.py` 中与 plan/analyze/skill 安装相关的入口进行审计，确认命令可达性与包装路径。
5. 复盘 `templates/commands/analyze.md` 及现有测试文件，识别“当前已经覆盖的 correctness review”与“未被覆盖的缺口”。
6. 产出审计结果文档，按 `covered / partial / missing` 和风险级别整理缺口清单。
7. 在审计结论中明确后续是否值得单独立项：仅补文档、补测试，还是未来新增自动化 correctness review 能力。

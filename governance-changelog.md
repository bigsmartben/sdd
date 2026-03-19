# Governance Changelog (Governance Backfill)

## 变更点与影响范围

| 变更点 | 影响范围 |
|---|---|
| 统一阶段治理边界：新增 `Authority rule / Stage boundary rule / Gate ownership rule`，并明确跨工件最终 `PASS/FAIL` 仅由 `/sdd.analyze` 持有 | `templates/commands/analyze.md`, `clarify.md`, `specify.md`, `specify.ui-html.md`, `plan.md`, `tasks.md`, `implement.md` |
| 固化 Repo Anchor Role 分类与闭包规则，明确哪些角色可用于 `State Owner Anchor(s)` 闭包 | `templates/constitution-template.md`, `data-model-template.md`, `test-matrix-template.md`, `contract-template.md`, `commands/plan.test-matrix.md`, `commands/plan.contract.md` |
| 强化边界锚点规范：`Boundary Anchor` 必须优先 repo 可证实；`Repo Anchor` 仅作佐证，不得替代边界语义；无可证实边界时保持 `TODO(REPO_ANCHOR)`/阻塞 | `templates/test-matrix-template.md`, `templates/contract-template.md`, `templates/commands/plan.test-matrix.md` |
| 新增“Seed Tuple vs Repo-Confirmed Boundary”漂移分类，显式记录 `none/naming/layering/missing` 及上游回路 | `templates/contract-template.md`, `templates/commands/plan.contract.md` |
| 收紧合同字段字典治理：引入 `Dictionary Tier=operation-critical/owner-residual`，并要求关键字段优先展示 | `templates/contract-template.md`, `templates/commands/plan.contract.md` |
| 数据模型从“抽象类全集”调整为“骨干语义集”，限定仅在稳定 owner/可复用契约边界下引入核心类，并收紧 `extended`/`new` 证据标准 | `templates/data-model-template.md`, `templates/commands/plan.data-model.md` |
| 原型交付约束增强：`ui.html` 明确动作入口可执行性要求（无目标则禁止死链 CTA），并强调该阶段 `Ready/Blocked` 仅为本地就绪，不是全局门禁 | `templates/ui-html-template.html`, `templates/commands/specify.ui-html.md` |
| 模板路径命名统一为 `feature-YYYYMMDD-slug`，减少分支/目录占位符歧义 | `templates/spec-template.md`, `templates/plan-template.md`, `templates/tasks-template.md` |
| 版本说明同步至 `v2.0.26` 相关提交语义 | `release_notes.md` |


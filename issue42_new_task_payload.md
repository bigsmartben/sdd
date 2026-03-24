# new_task payload for issue42 implementation

```json
{
  "name": "new_task",
  "arguments": {
    "context": "目标：实现 issue42（/sdd.plan.data-model lifecycle/FSM runtime contract 对齐），并按 P0+P1 一次性完成验收与发布放行。\n\nRefer to @implementation_plan.md for a complete breakdown of the task requirements and steps. You should periodically read this file again.\n\n如果当前处于 plan mode，请先切换到 act mode 再执行实现任务。\n\n请按以下 Plan Document Navigation Commands 分段读取：\n1) Read Overview section\n   sed -n '/^\\[Overview\\]/,/^\\[Types\\]/p' implementation_plan.md | cat\n2) Read Types section\n   sed -n '/^\\[Types\\]/,/^\\[Files\\]/p' implementation_plan.md | cat\n3) Read Files section\n   sed -n '/^\\[Files\\]/,/^\\[Functions\\]/p' implementation_plan.md | cat\n4) Read Functions section\n   sed -n '/^\\[Functions\\]/,/^\\[Classes\\]/p' implementation_plan.md | cat\n5) Read Classes section\n   sed -n '/^\\[Classes\\]/,/^\\[Dependencies\\]/p' implementation_plan.md | cat\n6) Read Dependencies section\n   sed -n '/^\\[Dependencies\\]/,/^\\[Testing\\]/p' implementation_plan.md | cat\n7) Read Testing section\n   sed -n '/^\\[Testing\\]/,/^\\[Implementation Order\\]/p' implementation_plan.md | cat\n8) Read Implementation Order section\n   sed -n '/^\\[Implementation Order\\]/,$p' implementation_plan.md | cat\n\n实施要求：\n- 严格执行 P0+P1 一次性验收范围，不拆分发布。\n- 先完成验收工件与自动化门禁，再接入 release workflow。\n- 所有新增逻辑需补充对应测试，并在 bash/PowerShell 端保持 data-model closure 规则一致性。\n- 不引入新三方依赖；复用现有 pytest、lint、preflight、release 脚本。\n\ntask_progress Items:\n- [ ] Step 1: 对齐并实现 issue42 的 runtime/prompt/template/lint/test 变更（P0+P1）\n- [ ] Step 2: 实现 issue42 专项验收门禁脚本与结构化验收报告输出\n- [ ] Step 3: 为验收门禁与 P1 规则补齐/更新自动化测试\n- [ ] Step 4: 接入 CI（test.yml）与发布前门禁（release.yml / release-trigger.yml）\n- [ ] Step 5: 执行 dry-run 验证并完成发布前核查\n- [ ] Step 6: 完成正式发布与发布后回归观察（按 runbook）"
  }
}
```

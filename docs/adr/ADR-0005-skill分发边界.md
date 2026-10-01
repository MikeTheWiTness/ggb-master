# ADR-0005：skill 为自包含分发单元（2026-08-27）

## 状态

已接受（用户决策）。

## 决策

`skills/ggb-master/` 是**可独立分发的 skill 单元**，在任意主机上安装（如 `~/.zcode/skills/ggb-master/`）即可运行：
- 只包含**精炼产物**（`macros/` 106 个 .ggt、`patterns/` 12 张选型卡、`fixtures/` 基准样例）
  与运行时工具、文档；
- **不得包含/引用仓库设施**：路径不写死、不引用 `samples/`、`extractions/`、`tools/`、`CONTEXT.md/PLAN.md/docs/adr`；
- 工作区约定：`projects/`、`exports/` 相对**当前工作区**（环境变量 `GGB_ROOT` 可覆盖，默认 CWD）；
- 文档措辞对"实证来源"的描述改用"真实成品验证"类表述，不指向具体库路径。

仓库侧（`samples/`、`extractions/`、`tools/`、`CONTEXT.md/PLAN.md/docs/adr/`）是**开发设施**，
服务"提取 → 精炼 → 安装进 skill"的维护流程，不随 skill 分发。

## 理由

skill 将迁移到其他主机运行；写死路径与仓库引用会当场失效。
精炼产物体积可控（约 800K），完整内嵌后无外部依赖，改主机即用。

## 影响

- 修改 skill 后需同步安装副本（开发仓库 `skills/ggb-master/` → `~/.zcode/skills/ggb-master/`）。
- 维护流程证据（samples/extractions）只对仓库维护者可见，skill 文档不引用。

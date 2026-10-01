# GGB Master

让 AI agent 产出**可直接用 GeoGebra 打开的交互式模拟课件 .ggb** 的 skill。
骨架仿 ppt-master：「AI 规划 + 确定性工具 + 质量门」。

- 术语与领域事实：`CONTEXT.md`
- 开发计划与决策：`PLAN.md`、`docs/adr/`
- DSH 插件包（skill + preset + `ggb` 原生工具，工作流随时插拔）：`packages/dsh-ggb-master/README.md`

## 快速开始

```bash
# 1. 初始化一个课件项目
python3 skills/ggb-master/scripts/project_manager.py init "单摆运动探究"

# 2. （AI 按 skills/ggb-master/SKILL.md 的流程写 design.md 与 geogebra.xml）

# 3. 五层校验（结构/引用/拓扑/数值/JS）——质量门
python3 skills/ggb-master/scripts/ggb_check.py projects/单摆运动探究/geogebra.xml
python3 skills/ggb-master/scripts/ggb_check.py projects/单摆运动探究/geogebra.xml --fix   # 填充缓存值

# 4. 打包导出（pack 内部会再跑一次质量门）
python3 skills/ggb-master/scripts/ggb_pack.py projects/单摆运动探究/ -o exports/单摆运动探究.ggb

# Modify 场景：解包已有 .ggb → 补丁 XML → 校验 → 重打包
python3 skills/ggb-master/scripts/ggb_unpack.py 已有课件.ggb -o projects/已有课件-modify/
```

## 仓库结构

```
GGB-master/
├── CONTEXT.md / PLAN.md / docs/adr/     # 术语 · 计划 · 决策记录
├── skills/ggb-master/                   # 开发源码（自包含分发单元，ADR-0005）
│   ├── SKILL.md                         # skill 入口：全局纪律 + 路由
│   ├── workflows/                       # routing / generate-ggb / modify-ggb / export-html-demo
│   ├── references/                      # construction-language（金标准）/ planner /
│   │                                    # interactivity / design-rules / failure-recovery
│   ├── scripts/                         # ggb_check / ggb_pack / ggb_unpack / project_manager
│   │                                    #   + ggb_macro_preview / html_demo_check / selftest
│   │   └── defaults/                    # 权威默认样式（随包进 .ggb）
│   └── templates/                       # 题型手册：轨道运动学 / 几何定理 / 函数参数
├── packages/dsh-ggb-master/             # DSH 组合包：随包 skill 副本 + ggb 原生工具 + 「GGB 课件」preset
├── tests/                               # 插件包打包契约测试 + 原生工具行为测试
├── tools/                               # 仓库维护设施（副本同步等，不随 skill 分发）
├── projects/                            # 用户项目工作区（每课件一目录）
├── exports/                             # 产物 .ggb
└── ggb绘图/                             # 本地真实样例库（形态验证基准，当前 33 个文件）
```

## skill 副本同步纪律

`skills/ggb-master/` 是开发源码；它有两类副本——**随包副本**
`packages/dsh-ggb-master/skills/ggb-master/`（DSH 插件包自洽所需，ADR-0006）与
**安装副本** `~/.zcode/skills/ggb-master/` 等（harness 实际加载）。
**改完源码必须同步所有副本**，以 `diff -rq` 仅剩 `__pycache__` 差异为完成标准：

```bash
# 一次同步随包副本 + 两个安装副本（workbuddy 副本自动做路径定制）
python3 tools/sync_skill_copies.py

# 自证：随包副本与源码应零差异
diff -rq skills/ggb-master/ packages/dsh-ggb-master/skills/ggb-master/

# 只改了个别 md / 脚本时，cp 单文件即可，但 diff 验证不可省
```

契约测试会逐文件比对随包副本与源码，漏同步直接红：

```bash
python3 -m pytest tests/ -q
```

## DSH 插件包（工作流随时插拔）

`packages/dsh-ggb-master/` 把 skill 与工具链打成 DSH 组合包（bundle）：安装后在
「插件」页可见，新会话可把 agent preset 选成「GGB 课件」——该 preset 只在这个会话里
挂载随包 ggb-master skill 并解锁 `ggb` 原生工具（子命令 `init` / `check` / `pack` /
`unpack` / `macro-preview` / `html-demo-check` / `selftest`）。换回 `ptc` preset 即完全摘掉，
其它会话与全局配置不受影响。

```bash
# 装：插件页 → 按本地路径安装下面这个目录；或 creator 会话里 plugin_manager install_bundle
packages/dsh-ggb-master/

# 零素材冒烟：随包基准样例应 exitCode 0 且 stdout 为 OK
#   ggb  args: ["check", "<包目录>/skills/ggb-master/fixtures/kepler-baseline.xml", "--quiet"]
```

细节、配置覆盖与宿主验收步骤见 `packages/dsh-ggb-master/README.md` 与
`packages/dsh-ggb-master/host-probe/README.md`。

## 设计红线（详见 PLAN.md §2.5）

1. **脚本分层**：GeoGebra 命令语法优先，JavaScript 仅兜底（命令优先原则）。
2. **物理真实性**：运动规律必须符合真实物理，禁止匀速扫角式造假；范围：**解析解系统**为默认（状态 = 时间显式函数，允许级数/牛顿迭代解隐式方程）；**允许 GeoGebra 内置 NSolveODE/SolveODE 数值求解**（三体、拉格朗日点、双杆等解析式写不出的轨迹），**禁止手写积分递推**（JS/Sequence 循环累加）。
3. **双层交互**：教师层参数充分（每物理量一个滑杆），观众层一键演示（播放/重置/动态读数）。

## 工具链自检基线

一键回归：`python3 skills/ggb-master/scripts/selftest.py`（22 项断言：骨架/样例/语料库/回填/往返/变异/JS/顺序校验/宏审计/预览）。
插件包契约与原生工具行为测试：`python3 -m pytest tests/ -q`（随包副本一致性、preset/工具行形状、真 Node 加载工具的分发与工作区注入）。

- `开普勒三定律模拟.ggb`（本机真实样例）：五层校验通过，求值器重算值与其缓存**逐位一致**（弧度制级数解）。
- `ggb绘图/` 全部真实 .ggb：五层校验 0 error。
- 往返测试：pack → unpack → check 幂等一致；变异测试（缓存篡改→warning、未定义引用→error、顺序颠倒→error）均被正确拦截或告警。
- 端到端示例：`projects/开普勒轨道探究/`（design.md → XML → 校验 → `exports/开普勒轨道探究.ggb`）。

## 已知边界

- 无官方无头渲染器：视觉正确性靠「结构/数值校验 + 用户打开确认」双保险，skill 不做截图对比。
- 求值器只覆盖常见函数子集（金标准 §9）；`Area` 等内核命令依赖 GeoGebra 加载重算。
- 内置 `NSolveODE/SolveODE` 属许可范围（金标准 §4.14E、patterns/nsolveode.md）；check 对 ODE 导数变量降级提示，不误报。
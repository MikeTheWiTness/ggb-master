# GGB Master 开发计划（v1.0 定稿）

> 2026-08-26 grilling 定稿。术语见 CONTEXT.md，关键决策见 docs/adr/。

## 0. 一句话

仿照 ppt-master 的「AI 规划 + 确定性工具 + 质量门」骨架，做一个让 AI agent 产出**可直接用 GeoGebra 打开的交互式模拟课件 .ggb** 的 skill，名称 **ggb-master**，全部文件中文。

## 1. 已确认的格式事实

基于本机真实样例 `开普勒三定律模拟.ggb` 拆解：

- `.ggb` = zip 包：`geogebra.xml`（必需）+ `geogebra_defaults2d.xml` / `geogebra_defaults3d.xml` / `geogebra_javascript.js` / `geogebra_thumbnail.png`（均可选）
- `geogebra.xml` 顶层：`<gui>` / `<euclidianView>` / `<algebraView>` / `<kernel>` / `<construction>`
- construction 三种构造原语：自由对象 `<element>`（滑杆/自由点/布尔）、表达式对 `<expression>`+`<element>`（派生对象）、`<command>`+输出元素
- 渲染属性家族：`show` / `objColor` / `layer` / `labelMode` / `lineStyle` / `pointSize` / `caption` / `absoluteScreenLocation` / `isLaTeX` / `font` / `fixed` / `animation`

## 2. 已确认决策（grilling 结论）

| # | 决策点 | 结论 |
|---|---|---|
| 1 | 目标场景 | 交互式模拟课件（拖滑杆、播放动画、探究规律） |
| 2 | 视图范围 | 2D 一等公民；3D 仅显式请求；CAS 不支持 |
| 3 | 交互深度 | 全交互：滑杆/动画/动态文本/复选框/按钮/InputBox/**JavaScript** |
| 4 | 产出单位 | 一次运行一个 .ggb；套件走多次调用 |
| 5 | 确认门 | 轻量单阶段聊天确认；显式 quick 可跳过；无 Confirm UI server |
| 6 | 校验深度 | 结构 + 引用一致 + 依赖拓扑 + 数值重算（常见函数子集，兼填充缓存值）+ JS 语法检查；不做截图对比 |
| 7 | 顶层路线 | Generate（新建）+ Modify（补丁已有 .ggb） |
| 8 | 规划工件 | 单文档 design.md；不写 spec_lock（XML 即锁定） |
| 9 | 模板 | 轻量题型手册；首批：轨道运动学 / 几何定理 / 函数参数 |
| 10 | 文档语言 | 全中文 |
| 11 | skill 名称 | ggb-master |
| 12 | 工作区 | repo 内 `projects/<课件名>/`，产物在 `exports/` |
| 13 | 脚本分层 | ggb 命令语法优先，JS 仅兜底（命令优先原则） |
| 14 | 物理真实性 | 禁止造假运动；解析解系统为默认，**允许内置 NSolveODE/SolveODE**，禁止手写积分递推 |
| 15 | 双层交互 | 参数充分（每物理量独立滑杆）+ 演示简单（一键播放/重置） |

## 2.5 设计原则（用户补充，2026-08-26）

1. **脚本分层：ggb 语法优先，JS 兜底**。一切脚本逻辑先用 GeoGebra 命令语法；表达不了才上 `geogebra_javascript.js`（命令优先原则）。
2. **物理真实性**。模拟要符合真实物理规律，禁止为省事造假：如开普勒问题中天体运行不是匀速的——平近点角 M 随时间线性，但位置必须由开普勒方程解出偏近点角 E 再算（级数或牛顿迭代），不能写成匀速圆周/匀速扫角。**解析解系统为默认**（状态 = 时间的显式函数，允许级数/迭代解隐式方程）；**允许 GeoGebra 内置 NSolveODE/SolveODE**（三体、拉格朗日点、双杆等解析式写不出的轨迹，2026-08 扩展）；**禁止手写积分递推**（JS/Sequence 循环累加）。
3. **参数充分 + 演示简单（双层交互）**。教师层：每个物理量独立滑杆，数值不写死在公式里（如 a、e、Δt 各自一个滑杆）；观众层：演示交互尽量简单——默认场景开箱可演、播放/暂停/重置一键按钮、动态读数自动更新，不要求观众理解一堆滑杆。

## 3. 目标结构

```
GGB-master/
├── README.md
├── CONTEXT.md
├── PLAN.md
├── docs/adr/
├── skills/ggb-master/
│   ├── SKILL.md                     # 薄入口：全局纪律 + 路由
│   ├── workflows/
│   │   ├── routing.md               # Generate / Modify 选路
│   │   ├── generate-ggb.md          # 主路线：需求 → design.md → 确认 → 手写 XML → 校验 → 打包
│   │   └── modify-ggb.md            # 补丁路线：解包 → 改 XML → 校验 → 重打包
│   ├── references/
│   │   ├── construction-language.md # 元素语法规范（金标准手册）
│   │   ├── planner.md               # 规划角色：design.md 怎么写
│   │   ├── builder.md               # 构造角色：手写 XML 的纪律与技巧
│   │   ├── interactivity.md         # 滑杆/动画/按钮/复选框/InputBox/JS
│   │   └── failure-recovery.md      # 失败恢复与续做指针
│   ├── scripts/
│   │   ├── ggb_check.py             # 五层校验（结构/引用/拓扑/数值/JS）
│   │   ├── ggb_pack.py              # geogebra.xml + 资源 → .ggb
│   │   ├── ggb_unpack.py            # .ggb → 工作目录（Modify 用）
│   │   └── project_manager.py       # init 项目骨架
│   └── templates/
│       ├── orbital-motion.md        # 轨道/运动学模拟
│       ├── geometry-theorem.md      # 几何定理探究
│       └── function-explorer.md     # 函数参数探究
└── projects/                        # 用户项目工作区
```

## 4. 两条路线概要

**Generate**：需求理解 →（缺料补研究）→ init 项目 → Planner 写 design.md → ⛔ 单阶段确认 → Builder 手写 geogebra.xml → ggb_check 五层校验（质量门）→ ggb_pack 导出 → exports/*.ggb。显式 quick：跳过确认，决策留上下文。

**Modify**：读入 .ggb → ggb_unpack → 理解现有构造 → 一句话确认改动点 → 补丁 XML → ggb_check → ggb_pack。不重生成整个构造。

## 5. 与 ppt-master 的本质差异（设计红线）

1. **无中间语言问题**：geogebra.xml 即原生语言，直接手写；工具链只做「校验 + 打包」。
2. **单画布**：无多页 roster，规划工件相应简化（单 design.md）。
3. **动态一致性是新难点**：label 引用、依赖拓扑、缓存值与表达式一致——ggb_check 的主战场。
4. **验证闭环有限**：无官方无头渲染器，视觉自查靠结构/数值校验 + 用户打开确认。

## 6. 里程碑

- M1 `construction-language.md` 金标准手册 + 样例解剖（以 Kepler 样例为基准）
- M2 骨架：SKILL.md + routing + generate-ggb 主流程 + project_manager
- M3 ggb_check.py（五层）+ ggb_pack.py + ggb_unpack.py
- M4 planner.md + builder.md + interactivity.md + design.md 模板
- M5 三本题型手册 + 端到端示例（用 skill 重新生成一个 Kepler 级模拟）
- M6 modify-ggb 路线 + failure-recovery + quick 模式打磨

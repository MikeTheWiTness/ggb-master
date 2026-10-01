# Context — GGB Master

Ubiquitous Language 术语表。只收术语与领域概念，不收实现决策与规格。

skill 名称（2026-08-26 共识）：**ggb-master**。项目工作区：repo 内 `projects/<课件名>/`，产物在 `exports/`。

## 格式层（geogebra.xml 领域事实）

- **construction**：`<construction>` 元素，一个 ggb 文件的全部数学对象容器，对应"一个课件/一张画布"。
- **自由对象（free object）**：不依赖其它对象的对象，如滑杆数值、自由点、布尔开关。XML 形态为单个 `<element>`（可含 `<slider>` / `<value>` / `<coords>`）。
- **派生对象（dependent object）**：由表达式或命令定义、依赖其它对象的对象。XML 形态为 `<expression>` + 紧随的 `<element>`（表达式对），或 `<command>` + 各输出 `<element>`。
- **缓存值（cached value）**：派生对象 `<element>` 内记录的最近一次计算结果（`<value val=...>` / `<coords .../>`），是加载前的初始显示状态。
- **滑杆（slider）**：`type="numeric"` 自由对象 + `<slider min max width x y .../>`，模拟的主要交互入口。
- **caption**：对象上的中文说明文字（`<caption val="..."/>`），在代数区/工具提示显示，区别于画布标签 label。
- **layer**：对象所在图层（0–9），高层覆盖低层。
- **绝对定位（absoluteScreenLocation）**：以像素为单位的屏幕坐标，用于文本说明和滑杆排布，不随坐标系缩放移动。
- **视图（view）**：2D 绘图区（euclidianView）、3D 区、代数区、CAS 区等。本 skill 范围（2026-08-26 共识）：2D 为一等公民，3D 仅在用户显式请求时支持，CAS 不支持。
- **动画（animation）**：对象的时间演化设置（step/speed/type/playing），滑杆动画是模拟"播放"的机制。
- **交互件（interactive controls）**：滑杆、复选框、按钮、InputBox。本 skill 范围（2026-08-26 共识）：全部交互件为一等公民，且包含 JavaScript 全局脚本（geogebra_javascript.js + GeoGebra JS API）。

## 规划层（skill 内部概念，随讨论补充）

- **模拟课件（simulation courseware）**：本 skill 的主要产出物定位（2026-08-26 共识）——老师/学生在 GeoGebra 中打开、通过拖滑杆和播放动画探究规律的交互式 .ggb 文件。区别于静态几何题解和纯函数绘图。产出单位为一次运行一个 .ggb；套件需求通过多次调用满足，skill 内不做批量编排。

- **design.md**：Generate 路线的唯一规划工件（2026-08-26 共识）——记录探究目标、参数滑杆清单与范围、动画机制、画面布局、文字说明；是确认门的展示对象，也是跨会话续做和 Modify 路线理解原意图的依据。不写 spec_lock：geogebra.xml 本身就是精确可执行的锁定。

- **题型手册（genre guide）**：`templates/` 下的轻量参考文档（2026-08-26 共识）——每题型一份 markdown：适用场景、构造套路、关键 XML 片段、常见坑。首批三个：轨道/运动学模拟、几何定理探究、函数参数探究。不做 index.json/workspace 重结构。
- **双层交互（two-layer interaction）**：术语（2026-08-26 共识）。规范正文：skill `SKILL.md` 全局纪律 2 与 `references/design-rules.md`（双副本同步纪律见下「工作区事实」）。
- **物理真实性（physical fidelity）**：术语（2026-08-26 共识，2026-08-28 扩）。规范正文：skill `SKILL.md` 全局纪律 3；动画节奏口径见 `references/design-rules.md` §5.5。
- **脚本分层**：术语（2026-08-26 共识）。规范正文：skill `SKILL.md` 全局纪律 5。
- **物理量可视化（physical visualization）**：术语（2026-08-27 共识）。规范正文：`references/design-rules.md` §0（速度/力矢量、场标记的强制呈现与执行细则）。

## 确认门（confirmation gate）
- **确认门（confirmation gate）**：生成前的用户确认点。本 skill 范围（2026-08-26 共识）：默认轻量单阶段聊天确认（展示模拟设计文档一次），显式 quick 意图可跳过；不做独立 Confirm UI server。
- **构造校验（construction check）**：ggb_check.py 的五层职责（2026-08-26 共识）：① XML 结构合法 ② 引用一致（label 唯一、引用对象已定义）③ 依赖拓扑（无循环、无先用后定义）④ 数值重算（常见函数子集，同时负责填充缓存值；算不了的写 best-effort 并依赖 GeoGebra 加载重算）⑤ JS 语法检查。不做视觉截图对比。

## 决策记录

见 `docs/adr/`。

## 文档语言（2026-08-26 共识）

skill 全部文件（SKILL.md / workflows / references / templates）使用中文，与用户已有的笔记类 skill 保持一致。产出物内容（caption、文字说明）跟随用户语言。

## 路线（2026-08-26 共识）

- **Generate**：从需求新建模拟课件。主路线。
- **Modify**：读入已有 .ggb，解包后直接补丁 XML（调参数/加对象/改交互），校验后重打包。不重生成整个构造。

## 工作区事实

- **skill 三副本**：源码在本仓库 `skills/ggb-master/`；随包副本在
  `packages/dsh-ggb-master/skills/ggb-master/`（DSH 插件包自洽所需，ADR-0006）；
  安装副本在 `~/.zcode/skills/ggb-master/`（harness 实际加载安装副本）。同步纪律：
  **改完源码必须同步所有副本**，一条命令 `python3 tools/sync_skill_copies.py`
  （默认目标已含随包副本与两个安装副本），以 `diff -rq` 仅剩
  `__pycache__` 差异为同步完成标准（2026-08-30 起执行；操作命令见 README「skill 副本同步纪律」）。
- **DSH 插件包**：`packages/dsh-ggb-master/` 是自包含 bundle，声明 agent preset
  「GGB 课件」（id `ggb-master`），preset 内挂载随包 skill 并注册原生工具 `ggb`
  （子命令 → 随包脚本）。安装/启用即挂上，换回普通 preset 或停用 bundle 即摘掉——
  工作流可随时插拔（ADR-0006）。
- 路径约定：`projects/<课件名>/` 工作区、`exports/` 产物，相对当前工作目录
  （环境变量 `GGB_ROOT` 可指定，未设则取当前目录）。

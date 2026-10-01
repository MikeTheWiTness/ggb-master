---
name: ggb-master
description: 生成、修改 GeoGebra 模拟课件（.ggb）——教师可调参（每个物理量独立滑杆）、观众一键播放/重置的交互演示，物理规律须真实（限解析解系统，禁造假）。当用户提到 "用 GeoGebra 做课件/模拟"、"做个可拖滑杆的动画演示"、"给这道题做个交互课件"，或要求在 GGB-master 项目里出 .ggb 时使用。
---

# SKILL.md —— ggb-master 薄入口

> 让 AI agent 产出**可直接用 GeoGebra 打开的交互式模拟课件 .ggb** 的 skill。
> 骨架：AI 规划（design.md）+ 确定性工具（ggb_check/ggb_pack）+ 质量门（五层校验）。
> 术语与设计原则内嵌于 `references/`；`fixtures/` 为随包基准样例（开普勒三定律、线框入磁 v-t 两份可解剖对象）。

## 全局纪律（所有路线必须遵守）

0. **分层职责（2026-08 重构）**：skill 只收录「模型训练语料少、且不可自行推理验证」的层——
   XML 元素形态与隐性坑、组合套路（插图区 v-t 图、播完自停、NSolveODE 边界值）、标准画法
   元件、教学规范红线、质量门工具；**物理/数学方程推导、题材分析、守恒/边界/量纲自检、
   滑杆范围推导交给模型自身**。判定一句话：模型能自行验证正确性的交给模型；只有模型
   无法自行验证、必须查语料才知道的才写进 skill。所有模板与流程文档开头带「公式自推」
   声明，不教可推理内容。
   - **取用成本预算**：任何参考件（模板/选型卡/片段/宏）应 ≤1 次读取即可决定
     「手绘 / 抄片段 / 用宏」；需要解包才能评估的素材（.ggt）先跑 `ggb_macro_preview.py`
     预览定夺，禁止未经预览直接拆包细读。
   - **沉淀去向规则**（新知识写进哪，2026-08-30 定）：元素形态与隐性坑 → construction-language
     （对应类型节 / §10）；交互编排 → interactivity；流程与步骤 → generate-ggb 对应节；
     设计红线与有效域 → design-rules；工具行为与恢复 → failure-recovery 或对应 workflow。
     **禁止新建平行清单**——坑与规范只允许一个权威的家，其余位置只留指针。

1. **产出单位**：一次运行只产出一个 `.ggb`（`exports/<课件名>.ggb`）。套件需求通过多次调用完成，skill 内不做批量编排。
2. **双层交互**：教师层参数充分——每个物理量独立滑杆、数值不写死在公式里；观众层演示简单——默认开箱可演、播放/重置一键按钮、动态读数自动更新。
3. **物理真实性**：运动/演化规律必须符合真实物理，禁止造假（如开普勒不能匀速扫角）。范围：**解析解系统**为默认（状态可表示为时间的显式函数，允许级数/迭代解隐式方程）；**允许 GeoGebra 内置 `NSolveODE/SolveODE` 数值求解**（三体、拉格朗日点等用它直接出轨迹），**禁止手写积分递推**（JS/Sequence 循环累加）。
4. **物理量可视化**：演示运动必配速度矢量、静力学必配力矢量图；磁场/电场区域必有场标记（⊗/⊙、电场线、磁感线）；场线形状标准严谨、优先矢性函数/矢量场呈现（design-rules.md §0）。
5. **脚本分层**：一切脚本先用 GeoGebra 命令语法（`<ggbscript>` 里的 `SetValue/StartAnimation/If/SetCaption…`），表达不了才上 `geogebra_javascript.js`（命令优先原则）。
6. **视图范围**：2D 为一等公民；3D 仅当用户显式要求；CAS 不支持。
7. **文档语言**：skill 文件全中文；产出物内容（caption、画面文字）跟随用户语言。
8. **质量门**：任何 `.ggb` 导出前必须通过 `ggb_check.py` 五层校验；不过关不打包。
   - **视觉验收（可选，2026-08 规范）**：有视觉能力的模型在打包后做一次真实渲染截图检查
     （流程与检查清单见 `workflows/generate-ggb.md` §9）；纯文本模型跳过，并在 `说明.md`
     记录「视觉验证未做」、交付时提醒用户自行打开验证。

## 路由

先读 `workflows/routing.md` 选路：

- **Generate**（主路线）：从需求新建模拟课件 → `workflows/generate-ggb.md`。
- **Modify**：读入已有 `.ggb`，补丁 XML → `workflows/modify-ggb.md`。

不确定选哪条，或需求只是零散问题 → 先按 Generate 走，缺料在流程内补研究。

> **路径约定**：脚本在**本 skill 目录**的 `scripts/` 下（以本文所在目录为准）；`projects/`、`exports/` 相对**当前工作区**（环境变量 `GGB_ROOT` 可指定，未设则取当前目录）。

## 常用工具

```bash
# init 项目骨架（建 projects/<课件名>/、拷贝默认样式、落 design.md 模板）
python3 ~/.zcode/skills/ggb-master/scripts/project_manager.py init "课件名"

# 五层校验（质量门）：结构 / 引用一致 / 依赖拓扑 / 数值重算 / JS 语法
python3 ~/.zcode/skills/ggb-master/scripts/ggb_check.py projects/<课件名>/geogebra.xml
python3 ~/.zcode/skills/ggb-master/scripts/ggb_check.py projects/<课件名>/geogebra.xml --fix   # 填充缓存值

# 打包 / 解包
python3 ~/.zcode/skills/ggb-master/scripts/ggb_pack.py projects/<课件名>/ -o exports/<课件名>.ggb
python3 ~/.zcode/skills/ggb-master/scripts/ggb_unpack.py exports/<课件名>.ggb -o <工作目录>/

# 宏预览/审计（取用任何 .ggt 前必跑，一次调用定夺：手绘/抄片段/用宏）
python3 ~/.zcode/skills/ggb-master/scripts/ggb_macro_preview.py <宏.ggt 或 macros/>

# 工具链自检（改了 scripts/ 之后必跑；在工作区运行，可选 GGB_ROOT）
python3 ~/.zcode/skills/ggb-master/scripts/selftest.py
```

> **宿主原生工具**：宿主若提供 `ggb` 原生工具（如 DSH 的「GGB 课件」preset），优先用它——
> 参数是「子命令 + 原样参数」：`init` / `check` / `pack` / `unpack` / `macro-preview` /
> `html-demo-check` / `selftest`，它自带随包脚本路径并注入会话工作区（`GGB_ROOT`）。
> 没有该工具时用上面的 `python3` 命令，两者等价。

## 参考文档索引

**选路与主流程**

| 文档 | 内容 | 什么时候读 |
|---|---|---|
| `workflows/routing.md` | Generate / Modify 选路 | 每次开始 |
| `workflows/generate-ggb.md` | Generate 主流程（含 Builder 速查 §5、视觉验收 §9） | 每次 Generate |
| `workflows/modify-ggb.md` | Modify 补丁流程 | 每次 Modify |
| `workflows/export-html-demo.md` | 可选出口：单文件 HTML 定妆演示件（免环境播放器） | 用户要免环境/可嵌入演示时 |

**规划与构建**

| 文档 | 内容 | 什么时候读 |
|---|---|---|
| `references/planner.md` | design.md 怎么写 | 写 design 前 |
| `references/design-rules.md` | 设计规范：模型有效域、参数域推导、非负性清单、动画节奏合规 §5.5 | 定滑杆范围/写公式前必读 |
| `references/construction-language.md` | 元素语法金标准（本 skill 最重要文档） | 手写 XML 前必读 |
| `references/interactivity.md` | 滑杆/动画/按钮/复选框/InputBox/JS（含按钮四母本 §3.1） | 涉及交互时 |
| `patterns/index.md` | 12 张选型卡（单元级：怎么选、母本、详见章节） | 建模前选型 |
| `macros/README.md` | 106 个自定义工具（.ggt，分类 + 全表） | 要插标准元件/改成品时 |
| `templates/orbital-motion.md` | 轨道/运动学题型（解析运动学构造套路） | 按题型选用 |
| `templates/motion-graph.md` | 运动+图像关联题型（同窗 v-t 图：单视图插图区仿射映射 + NSolveODE 边界值 + 播完自停） | 运动与图像对照演示 |
| `templates/geometry-theorem.md` | 几何定理题型（绘图模式 vs 几何模式、命令块形态） | 几何题用 |
| `templates/function-explorer.md` | 函数探究题型（函数对象/根/极值/导数命令） | 函数题用 |

**校验、恢复与解剖**

| 文档 | 内容 | 什么时候读 |
|---|---|---|
| `references/failure-recovery.md` | 失败恢复与续做指针 | 遇到问题/被打断时 |
| `fixtures/kepler-baseline.xml` | 开普勒三定律基准样例（整个构造可打开对照） | 解剖/对照时 |
| `fixtures/线框入磁-vt-baseline.xml` | 运动+图像同窗基准样例（线框入磁 v-t，解剖见 templates/motion-graph.md） | 解剖/对照时 |

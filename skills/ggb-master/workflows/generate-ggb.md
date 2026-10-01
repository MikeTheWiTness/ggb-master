# generate-ggb —— Generate 主路线

> 主流程：需求 → design.md → ⛔ 确认 → 手写 geogebra.xml → 五层校验 → 打包到 exports/。
> 角色分工：本文档讲流程，`references/planner.md` 讲 design.md 怎么写；XML 形态金标准在
> `references/construction-language.md`（§5 有 Builder 速查）。
> 术语标记：⛔ = 确认门（用户必须知情/确认）；🛠 = 工具命令。

## 0. 流程总览

```
1 需求理解（含缺料补研究）
2 🛠 init 项目骨架（project_manager.py）
3 Planner 写 design.md
4 ⛔ 单阶段确认（展示 design.md 摘要；显式 quick 跳过）
5 Builder 手写 geogebra.xml（素材随附：media/ 图片 + 宏定义）
6 🛠 ggb_check.py 五层校验（质量门）
    └─ 不过 → 回到 5 修，循环
7 🛠 ggb_pack.py 导出 → exports/<课件名>.ggb
8 收尾：写一页「打开方式/操作说明」到项目目录，向用户报告
9 ⛔🎨 视觉验收（可选，按模型能力判定，见 §9）：有视觉能力的默认做；
   纯文本模型跳过并在说明.md 记录，交付时提醒用户自行打开验证
```

## 1. 需求理解

把用户需求转成一张「可确认的事实单」：

- **主题**：探究什么规律？对应哪类题型（轨道运动学 / 几何定理 / 函数参数 / 其它）？
- **角色**：老师讲台演示还是学生自己探究？（影响 caption 语气与交互复杂度）
- **视图**：2D 够不够？3D 只有显式要求才做。
- **物理/数学模型**：写出解析关系（时间显式函数）。**缺料就补研究**——公式不确定就查证，不要在假设上写死。
  公式推导交给模型自身（SKILL.md 第 0 条分层职责）：skill 的模板/语料**只供构造形态与坑，
  不教物理推导**；模型自推后按 design.md「模型层自检」清单自查（守恒恒等式、分段边界连续、
  量纲、数值对拍）。
- **交互面**：哪些量该是滑杆？哪些该是按钮？要不要复选框/InputBox？动画主时钟是什么？

> 这是唯一一次系统性问需求的机会。宁可这里多问两句，不要在写 XML 时返工。
> 注意：**确认门放在 design.md 之后**（更具体的展示件），需求阶段只澄清事实，不急着确认方案。

> 路径中的 `~/.zcode/skills/ggb-master/` 是安装副本约定位置；其它主机/工具链以实际安装路径为准。

## 2. init 项目（🛠）

```bash
python3 ~/.zcode/skills/ggb-master/scripts/project_manager.py init "<课件名>"
```

落在 `projects/<课件名>/`：

```
projects/<课件名>/
├── design.md                # 规划工件（Planner 接下来写）
├── geogebra.xml             # Builder 接下来写
├── geogebra_defaults2d.xml  # 默认样式（工具拷入）
├── geogebra_defaults3d.xml  # 默认样式（工具拷入，3D 才需要，有就留着）
└── geogebra_javascript.js   # 占位 function ggbOnInit() {}
```

课件名建议：中文主题 + 简短，如 `开普勒第三定律`。最终命名 `exports/<课件名>.ggb`。

## 3. Planner 写 design.md

按 `references/planner.md` 写。产出五件事：

1. **探究目标**（一段话：观众拖什么、看到什么、得出什么结论）。
2. **模型层先行（与探究目标同轮完成）**：先写「状态 = 时间的显式函数」与自检手段
   （design.md「模型层自检」小节），**再谈界面**——物理公式由模型自推与自查，
   语料只供形态；没有完整分段闭式不许进滑杆清单。
3. **参数滑杆清单**：每个物理量的滑杆名、范围、初值、步长、动画（教师层参数充分，一个量一个滑杆）。
4. **演示机制**：主时钟、动画对象、播放/重置按钮、可见性切换——观众层一键到底。
5. **画面布局与文字**：坐标系范围、左右布局、caption/标题/读数文本的内容（中文）。

写完后把 design.md 的**摘要**（不是全文粘贴）准备好给用户确认。

## 4. ⛔ 单阶段确认

- 默认：向用户展示 design.md 摘要，请其确认或提出修改。确认后进入 Builder。
- 显式 `quick` 意图（用户在开始时说了"直接做"/"不用确认"）：跳过本轮，design.md 里标注 `确认：quick 跳过`，继续。
- 自主会话（用户不在线、无法应答，2026-08-30 规则）：视同显式 quick——跳过确认门，design.md
  顶部标注 `> 确认：自主会话跳过（需求已完整明确，决策留档 design.md）`，继续推进。
- 用户要改：改 design.md → 再确认 → 继续。

## 5. Builder 手写 geogebra.xml

按 `references/construction-language.md`（元素语法金标准）写。纪律：

- 以 init 生成的 `geogebra.xml` 骨架为底，只改 `<construction>`、`<euclidianView><coordSystem>`
  与必要的内核区块（角度单位语义见金标准 §10 坑3）。
- 缓存值**不要手填**：交给 ggb_check 第四层填充（留 `<value/>`、`<coords/>` 或不写）。
- 需要 JS 才写 `geogebra_javascript.js`；否则保留占位。
- 写完自查引用顺序（拓扑序）。

**Builder 速查**（原 builder.md 精华，2026-08-30 并入）：

- **书写顺序 = 依赖拓扑**：滑杆/布尔/按钮等自由对象 → 派生中间量（`show object="false"`）→
  几何主对象 → 读数与说明文本；被引用的 label 先于引用者出现。
- **布局心眼**：交互件像素定位且两套定位不混用（滑杆/文本 `absoluteScreenLocation`，
  按钮/复选框/InputBox `labelOffset`）；先算内容尺寸再定 `coordSystem` 的 scale
  （可视世界范围 ≈ 画布像素 ÷ scale）；图层 0 主体 / 1 强调 / 2 文本 / 7 按钮；课件字号 18~20。
- **每对象自查**：label 拼写与引用完全一致；expression 与紧随 element 的 label 相同；
  命令 input/output 引用存在；中文 UTF-8 直写，`<` `>` `&` 转义；裸三角函数按弧度（角度显式写 `°`）。
- 坑速查：元素形态坑看 construction-language §10 与本文 §9.5；按报错层定位看 failure-recovery §1。
- **素材两条路**（设计稿「素材清单」里已列）：
  1. 图片素材 → 放 `media/<引用路径>`，XML 写 image 元素（boundary：物理对象必须数学对象，
     只有符号/装饰用图，见 construction-language §4.12）；
  2. 标准元件（电路符号、地面、滑轮框…）→ 从 `macros/<类>/` 取 .ggt，把宏定义拼进
     `geogebra_macro.xml` 再调用（construction-language §4.13）；
  注意：`ggb_check` 自动读宏白名单，缺素材只告警；**`ggb_pack` 引用缺失会拒绝打包**。

### 5.1 复杂任务三步分步模式（planner 判定「高复杂度」时强制）

**目的**：把「几何对不对」和「参数动不动」解耦，每步产出可被用户实测检查的 .ggb，
避免一次性生成整条链、出错难定位（环形磁场案例的教训）。核心技巧：**先写死，后参数化**。

| 步 | 内容 | 产物 | 检查点 |
|---|---|---|---|
| P1 静态构图 | 轨迹/几何对象公式用**固定常量**写死（θ、v、k 先在公式里写数值）；坐标系、布局、滑杆外壳建好但不接线 | `exports/<名>-p1-静态.ggb` | ⛔ 用户打开看构图、方向、轨迹形状是否正确 |
| P2 参数化 | 常量替换为滑杆引用；派生链、动点、动画接通 | `exports/<名>-p2-动态.ggb` | ⛔ 用户检查拖滑杆是否联动、动画是否顺 |
| P3 交互打磨 | 按钮、读数文本、复选框、文案、适用域警示 | `exports/<名>.ggb` | 全量验收 |

- 每步产物都必须通过 ggb_check 五层校验（缓存子元素一律**省略**，--fix 填充；勿写空 `<value/>`）；不过关不进下一步。
- 用户每步反馈的修正走 Modify 思路（解包上一步产物补丁），不推倒重来。
- 中间产物留在 exports/ 作为备份；最终产物以无后缀名为准。
- 自主会话适配（2026-08-30 实践）：无用户可实测时，「⛔ 用户实测检查点」降级为「渲染截图
  自检关卡」——P1 初态渲染查构图、P2 中段/终点渲染 + getValue 抽查查联动、P3 极值参数渲染
  + 视觉验收查全量；每步仍独立跑 ggb_check，中间产物照常留 exports/。

## 6. 🛠 ggb_check 五层校验（质量门）

```bash
python3 ~/.zcode/skills/ggb-master/scripts/ggb_check.py projects/<课件名>/geogebra.xml
```

五层：结构合法 → 引用一致 → 依赖拓扑 → 数值重算（兼填充缓存值）→ JS 语法（症状→处置速查见 `references/failure-recovery.md` §1）。

- 失败：按报错回到第 5 步修。
- 通过但带警告（如 `Area(s1)` 求值器子集外）：记录，不阻塞。
- **数值层通过后会建议 `--fix` 填充/校正缓存值**：

```bash
python3 ~/.zcode/skills/ggb-master/scripts/ggb_check.py projects/<课件名>/geogebra.xml --fix
```

- ⚠ `--fix` 会重排 XML（缩进、自闭合标签规范化，见 failure-recovery §5）：fix 之后再 Edit
  该文件必须**先重新 Read**（旧 old_string 全部失配；2026-08-30 实测）。

## 7. 🛠 ggb_pack 打包

```bash
python3 ~/.zcode/skills/ggb-master/scripts/ggb_pack.py projects/<课件名>/ -o exports/<课件名>.ggb
```

打包前 pack 会再跑一次 `ggb_check.py` 作为最后一道闸（`--skip-check` 可跳过，仅用于排查）。

## 8. 收尾

在项目目录写 `说明.md`：课件名、打开方式（GeoGebra Classic / 网页端）、操作步骤（"拖 a 滑杆看轨道形状变化"、按钮含义）、结论提示。
最后向用户报告：`.ggb` 路径、设计要点、哪几个量是滑杆、怎么玩、以及「请在 GeoGebra 里打开验证视觉效果」的提醒。

## 9. 视觉验收（可选 · 按模型能力判定，2026-08 规范）

> 五层校验只保证「XML 合法 + 缓存值正确」，**不能发现视觉错位**（文本/几何对位、视图自适应
> 平移、标签显示成 "名称 = 值"、滑杆初值失效等全部来自实测返工）。本步骤把真实渲染截图检查
> 固化进流程，**但不强制**——判定权在模型能力：

### 9.0 判定（进入本步前的第一件事）

| 模型能力 | 规则 |
|---|---|
| **纯文本模型**（不能看图） | **跳过本步骤**。在 `说明.md` 记录「视觉验证未做（纯文本模型）」，交付时提醒用户自行打开验证。 |
| 有视觉能力 | **默认做**。课件含屏幕定位文本 / 插图 / 多部件对位时风险高，更应做。 |
| 有视觉能力但渲染环境不可达（断网、无浏览器） | 降级为跳过，同样在 `说明.md` 记录原因与「待用户验证项」。 |

> 例外抬高：含自定义函数对象（`type="function"`，如分段 If 链/奇偶选支的 v-t 曲线源）
> 是五层校验盲区——L4 对函数体标「求值器子集外」放行，**校验全过也可能加载失败**
> （实测：函数体内 `Mod[floor(u),2]` 报 `error in <expression>`）。此类课件不允许降级跳过
> 视觉步骤；纯文本模型需在 `说明.md` 显式标注「函数链未实机验证」。
>
> 浏览器工具 fallback（2026-08-30 实测）：会话内 Playwright MCP 报「系统 Chrome 未安装」时，
> 改用 node render.js + ms-playwright 缓存 chromium（launch 的 executablePath 显式指向缓存
> 路径）；/tmp/ggbview 本地服务与页面模板跨会话存活，先 `curl localhost:8765` 探测再重建。

### 9.1 环境（一次搭好，可复用）

```bash
# 1) 本地静态服务（常驻）
mkdir -p /tmp/ggbview && (python3 -m http.server 8765 --directory /tmp/ggbview &)

# 2) 加载页模板 /tmp/ggbview/index.html（deployggb 用镜像站 ggb123.cn，2026-08 实测比
#    geogebra.org 稳定；官方不可达时可换回 https://www.geogebra.org/apps/deployggb.js）
#    <script src="https://ggb123.cn/apps/deployggb.js"></script>
#    <script>
#      const file = new URLSearchParams(location.search).get('file') || 'course.ggb';
#      new GGBApplet({ appName: 'classic', filename: file, width: 1280, height: 900,
#        showToolBar: false, showAlgebraInput: false, showMenuBar: false }, true).inject('ggb');
#    </script>

# 3) Playwright 渲染脚本（本地有 chromium 缓存即用；关键点：持久 profile 缓存 app 资源，
#    首次下载后离线秒开；页面加载用 waitForFunction(window.ggbApplet) 轮询）
cp exports/<课件名>.ggb /tmp/ggbview/course.ggb
node render.js   # → 截图 + 可选 getValue 抽查（见 9.3）
```

> **applet 尺寸一致性**（2026-08-30 实测）：index.html 里 GGBApplet 的 width/height 必须与课件
> `<euclidianView><size>` 相同——不一致时滑杆/文本像素定位的检查结论全部失真（借用旧会话
> 1200×800 模板渲染 1280×800 课件，右栏布局被误导）。
>
> **渲染资产不随包**（2026-08 REVIEW）：上述 render.js / index.html 是「按需本机搭建」的
> 流程样板，不在 skill 包内（依赖 deployggb CDN 与 Playwright，环境易碎）。有自带浏览器
> 自动化的模型（如 Playwright/浏览器工具）**直接用会话内工具加载本地 .ggb 并截图**，
> 替代脚本；无浏览器能力走 §9.0 跳过分支。

### 9.2 截图策略（建议三张起）

1. **初态**（t=0 或默认参数）：布局全景，读数组与几何对位。
2. **运行中**（`evalCommand('SetValue[t, 中段]')`）：动画主对象、矢量/跟踪点位置。
3. **极值参数**（拖滑杆到两头 / 设 k=1 等临界态）：参数域边界不出鬼、警告文本出现。

### 9.3 检查清单（逐项过）

1. 关键派生量读数与 design.md / Python 预验一致（防"滑杆初值失效"类问题）。
2. 文本/标注与几何对位：跟随内容的标注不因视图自适应平移漂移（静态文本用
   `<startPoint x y>`，动态标注用 labelMode=3 Caption / Text[.., 点]）。
3. 标签没显示成 "名称 = 值"（点/段 labelMode 归 0 或用 Caption）。
4. 曲线/虚线线型、颜色、粗细符合设计；插图无截断、无文字互相遮挡。
5. 滑杆/按钮可见、不互相遮挡；打开不自动播放、点一次即播；播放到上限自停。
6. fit 平移观察：几何内容与屏幕层（滑杆/按钮/读数组）相对位置可接受即可，不要求逐像素。
7. 交互件实测：按钮脚本 `evalCommand('RunClickScript[btnX]')` 触发后 `getValue` 断言生效
   （目标值、按钮文字）；复选框翻转后截图确认显隐联动（2026-08-30 实测：一键设值类按钮用此法验证）。
8. 动态文本无截断：按金标准 §4.10「文本宽度预算」估宽，且用**滑杆全域最长字符串**检查
   （不是默认值），右缘留白 ≥20px。

### 9.4 迭代与出口

- 发现错位 → 改 XML → `ggb_pack` 重打 → 重渲染复查（控制在 2~3 轮；改完必须再跑
  `ggb_check`，视觉改动不能绕过质量门）。
- 通过 → 在 `说明.md` 记录「已视觉验收 + 检查时刻」；跳过 → 按 9.0 记录原因。
- 交付语言固定提醒：无视觉闭环的跳过场景里，请用户打开后反馈视觉细节。

### 9.5 踩坑速记（2026-08 实测，改 XML 时对照）

- 存在但空的 `<value/>` / `<coords/>` 直接让 GeoGebra 报 "For input string: null" 打不开（**省略子元素**才是安全形态，GeoGebra 加载重算；此处指写了空元素且无 val）
  （--fix 算不了的必须手动填默认参数真值，见 construction-language §8）。
- 滑杆 element 子元素必须按官方顺序（value → slider(带 showAlgebra) → lineStyle →
  show → objColor → layer → labelMode → animation（step 可带可省）→ caption），
  否则网页版/新版本 `<value>` 失效、滑杆落到 min。
- `Point[NSolveODE输出, 参数]` 的参数是**归一化 [0,1]**，取终点用 `1`。
- CurveCartesian 输出 element 的 type 是 `curvecartesian`（不是 locus）。
- 文本锚定：官方形态是 `<expression>` + `<startPoint x y>`（静态锚点）；动态标注优先
  labelMode=3（Caption）。`<command name="Text">` 可行但 `ggb_check --fix` 会解码破坏
  字符串引号，慎用。
- 渲染脚本每次换 `?file=xxx&v=时间戳` 参数，避免浏览器缓存旧构造。

---

## 10. 可选出口：HTML 定妆演示件

用户要「免 GeoGebra 环境、可嵌入网页/PPT」的演示时，在主流程验收通过后追加一步：把
**默认参数组下、实现探究目标结论的一次完整演化**烘焙成单文件 HTML 播放器（只播放不模拟，
数据由项目侧 Python oracle 注入）。定位、三纪律、数据契约与流程见
`workflows/export-html-demo.md`；数据校验：`python3 scripts/html_demo_check.py <data.json|demo.html>`。

---

## 质量门失败恢复

出错时的处置统一见 `references/failure-recovery.md`。高频前三：

1. label 引用未定义/顺序错 → 检查拓扑序。
2. 缓存值与公式不一致 → 跑 `--fix`。
3. XML 转义漏（`>` 写成裸符号）→ 看 ggb_check 第一层报错位置。

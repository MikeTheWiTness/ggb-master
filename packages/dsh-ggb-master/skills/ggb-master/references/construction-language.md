# construction-language —— geogebra.xml 金标准手册

> 本手册是本 skill 的元素语法规范（金标准）：一切 `geogebra.xml` 手写都必须服从这里的形态。
> 全部形态均来自对真实 GeoGebra 成品的拆解（开普勒三定律模拟基准见 `../fixtures/kepler-baseline.xml`，另验证 100+ 个成品）。
> 不是凭记忆推断。标注 ⚠️ 的条目是「见过但未完全验证」的形态，遇到先实机确认。
> 行为类结论（§10 坑、§8 缓存）为实机验证（样张 version 5.2.x 一线）；GeoGebra 升级后个别行为可能变化，存疑先实机复测。
>
> 配套：`interactivity.md`（滑杆/动画/按钮/复选框/InputBox/JS 的交互编排）；书写流程与
> Builder 速查在 `workflows/generate-ggb.md` §5。

## 0. 一句话

`.ggb` 是一个 zip 包，核心是 `geogebra.xml`：一个 `<construction>` 容器装下全部数学对象。
本 skill 手写这个 XML，`ggb_check.py` 校验、`ggb_pack.py` 打包，产出可直接被 GeoGebra 打开的交互式模拟课件。

## 1. .ggb 包结构

```
xxx.ggb                       # zip 包
├── geogebra.xml              # 必需。全部构造与视图设置
├── geogebra_defaults2d.xml   # 可选，2D 新对象默认样式（推荐随包，见 scripts/defaults/）
├── geogebra_defaults3d.xml   # 可选，3D 默认样式（仅 3D 时带上）
├── geogebra_javascript.js    # 可选，全局 JS（至少含 function ggbOnInit() {}）
└── geogebra_thumbnail.png    # 可选，缩略图
```

- 只有 `geogebra.xml` 也能打开，但带上 defaults 会让新建对象获得合理默认样式（点默认蓝色等）。
- `ggb_pack.py` 只打包工作目录里**已存在**的这些文件；`project_manager.py init` 会把 `scripts/defaults/` 里的默认样式拷进项目目录。

## 2. geogebra.xml 顶层骨架

开头必须是这一行（换行符 LF 即可）：

```xml
<?xml version="1.0" encoding="utf-8"?>
<geogebra format="5.0" version="5.2.871.0" app="classic" platform="d" xsi:noNamespaceSchemaLocation="http://www.geogebra.org/apps/xsd/ggb.xsd" xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
```

顶层子元素按固定顺序（参照 XSD `ggb.xsd` 与真实样例）：

```xml
<gui> ... </gui>
<euclidianView> ... </euclidianView>
<algebraView> ... </algebraView>
<kernel> ... </kernel>
<tableview .../>
<scripting blocked="false" disabled="false"/>
<construction title="课件名" author="" date="">
  ... 全部数学对象 ...
</construction>
</geogebra>
```

### 2.1 最小可用骨架（2D 直接抄这一段）

```xml
<?xml version="1.0" encoding="utf-8"?>
<geogebra format="5.0" version="5.2.871.0" app="classic" platform="d" xsi:noNamespaceSchemaLocation="http://www.geogebra.org/apps/xsd/ggb.xsd" xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<gui>
	<window width="1200" height="800" />
	<perspectives>
<perspective id="tmp">
	<panes><pane location="" divider="0.8" orientation="1" /></panes>
	<views><view id="1" visible="true" inframe="false" stylebar="true" location="3" size="1200" window="100,100,600,400" /></views>
	<toolbar show="true" items="0 73 62 | 1 501 67 , 5 19 , 72 75 76 | 2 15 45 , 18 65 , 7 37 | 4 3 8 9 , 13 44 , 58 , 47 | 16 51 64 , 70 | 10 34 53 11 , 24  20 22 , 21 23 | 55 56 57 , 12 | 36 46 , 38 49  50 , 71  14  68 | 30 29 54 32 31 33 | 25 17 26 60 52 61 | 40 41 42 , 27 28 35 , 6" position="1" help="false" />
	<input show="true" cmd="true" top="algebra" />
	<dockBar show="false" east="false" />
</perspective>
	</perspectives>
	<labelingStyle  val="1"/>
	<font  size="18"/>
</gui>
<euclidianView>
	<viewNumber viewNo="1"/>
	<size  width="1200" height="700"/>
	<coordSystem xZero="560" yZero="380" scale="40" yscale="40"/>
	<evSettings axes="true" grid="false" gridIsBold="false" pointCapturing="3" rightAngleStyle="1" checkboxSize="26" gridType="3"/>
	<bgColor r="255" g="255" b="255"/>
	<axesColor r="37" g="37" b="37"/>
	<gridColor r="192" g="192" b="192"/>
	<lineStyle axes="1" grid="0"/>
	<axis id="0" show="true" label="" unitLabel="" tickStyle="1" showNumbers="true"/>
	<axis id="1" show="true" label="" unitLabel="" tickStyle="1" showNumbers="true"/>
</euclidianView>
<algebraView><mode val="1"/></algebraView>
<kernel>
	<continuous val="false"/>
	<usePathAndRegionParameters val="true"/>
	<decimals val="5"/>
	<angleUnit val="degree"/>
	<algebraStyle val="0" spreadsheet="0"/>
	<coordStyle val="0"/>
</kernel>
<tableview min="-2.0" max="2.0" step="1.0"/>
<scripting blocked="false" disabled="false"/>
<construction title="课件标题" author="" date="">
	<!-- 对象写在这里 -->
</construction>
</geogebra>
```

- `<coordSystem>`：`xZero/yZero` 是坐标原点在画布上的像素位置，`scale` 是每单位像素数。
  如 `xZero=560 yZero=380 scale=40` ≈ 画布 1200×700、原点居中、1 单位=40px。
- `<kernel><angleUnit val="degree|radian"/></kernel>`：角度单位。**模拟物理一律写公式内部弧度、并把 angleUnit 设为 radian 或保持 degree 不冲突**——见 §11 常见坑 3。

## 3. construction 的三种构造原语

| 原语 | XML 形态 | 对应对象 |
|---|---|---|
| 自由对象 | 单个 `<element>`（含 `<slider>`/`<value>`/`<coords>`） | 滑杆数值、自由点、布尔开关、按钮 |
| 表达式对 | `<expression>` + 紧随的 `<element>` | 由公式/命令定义的派生对象（数值、点、圆锥曲线、函数、文本） |
| command | `<command>` + 各输出 `<element>` | 需要 GeoGebra 内核命令构造的复合对象（多边形、线段、Textfield） |

**表达式对 = `<expression label=... exp=... type=.../>` + `<element type=... label=...>`，两者 label 必须一致，且 element 必须紧跟 expression。**

## 4. 对象类型 XML 手册

通用子元素（可省略项见各类型）：
- `<show object="true|false" label="true|false" ev="4"/>`：object=画布可见，label=代数区标签可见。
- `<objColor r g b alpha/>`：RGB 0-255；alpha 0=不透明（几何填充色另见 polygon 的 alpha）。⚠️ 语义有反直觉处，把背景/填充色的 alpha 放在 `<objColor>` 上，参考样例照抄。
- `<layer val="0-9"/>`：图层，高层覆盖低层；文字说明放 2。
- `<labelMode val/>`：0=隐藏，1=名称+值，2=只显示值，**3=显示 Caption（2026-08-30 实测，网页版 classic）**，4=只显示名称。要显示中文 caption（球名、滑杆标题）用 3。
- `<caption val="中文说明"/>`：代数区/工具提示里的中文说明，区别于画布 label。
- `<fixed val="true|false"/>`：是否锁定。
- `<animation step=".." speed=".." type=".." playing="true|false"/>`：动画设置（见 interactivity.md）。
- `<condition showObject="布尔label"/>`：对象级显隐条件（布尔驱动、零脚本；也可加 `showLabel`）。
  显隐开关首选它或 SetVisibleInView，不要用 If 包表达式隐藏（§4.15 坑）。
  放 **element 子元素末尾**（其余状态子元素之后）实测通过（2026-08-30）；point/segment/vector/polygon/text 均可挂。

### 4.1 numeric 自由对象（滑杆）

```xml
<element type="numeric" label="a">
	<value val="5"/>
	<slider min="2" max="8" width="180" x="20" y="30" fixed="false" horizontal="true" absoluteScreenLocation="true" showAlgebra="true"/>
	<lineStyle thickness="10" type="0" typeHidden="1"/>
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="1"/>
	<animation step="0.1" speed="1" type="1" playing="false"/>
	<caption val="半长轴 a"/>
</element>
```

> **推荐新序**（value→slider→lineStyle→show→objColor→layer→labelMode→animation→caption，
> 线框入磁样张形态；网页版/新版对子元素顺序敏感，见 §10 坑2）。旧序
> （show→…→slider→value→animation→caption）见于老成品（kepler 基准），老版本可用、
> 网页版有 `<value>` 失效、滑杆落到 min 的风险——**新文件一律按新序**。

- `<slider>`：`min/max` 数值范围，**可直接引用派生数值对象**（如 `max="tEnd"`，参数变化时上限自动伸缩——「播完自停」套路见 interactivity.md §2）；`x/y` 为左上角**像素坐标**（画布坐标，不随坐标系缩放）；`width` 像素宽度；`absoluteScreenLocation="true"` 表示用屏幕坐标定位（模拟交互件必须用它）；`fixed="false"` 允许拖。
- `<value val>`：当前值（首屏状态）。
- `<animation>`：动画参数，见 interactivity.md。**模拟主时钟 `type="1"`（振荡），`playing` 初始一律 `false`（打开不播——加载不自动启动动画，interactivity.md §3 实测教训）；播完自停型 用 `type="3"` + 动态上限（interactivity.md §2.1）。**
- 状态位（推荐全量）：`show/objColor/layer/labelMode/slider/value/animation/caption`。

### 4.2 numeric 派生对象（表达式对）

```xml
<expression label="b" exp="a * sqrt(1 - ex^2)" type="numeric"/>
<element type="numeric" label="b">
	<show object="false" label="false" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="0"/>
	<value val="4.330127018922193"/>
</element>
```

- `<expression exp>` 用 GeoGebra 代数语法（**函数用圆括号** `sqrt(...)`、幂用 `^`、引用其它对象用 label 名）。
- `<value val>` 是**缓存值**（见 §8），由 Builder 留空、`ggb_check.py` 用内置求值器填充并校验；手动填也可以，但必须与 `exp` 一致。
- 派生辅助量（离心率、半短轴、周期等）默认 `show object="false"` 不显示。

### 4.3 boolean 自由对象（复选框）

```xml
<element type="boolean" label="showOrbit">
	<value val="true"/>
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="1"/>
	<checkbox fixed="true"/>
	<labelOffset x="850" y="30"/>
	<caption val="显示轨道"/>
</element>
```

- `<value val="true|false"/>` 当前勾选状态。
- `<checkbox fixed="true"/>` 表示不可拖动位置（标准做法）。
- **屏幕定位用 `<labelOffset x y/>`**（像素坐标），不是 absoluteScreenLocation（实测证实）。
- 控制别的对象显隐：给目标对象写 `<condition showObject="showOrbit"/>`（通用子元素），比 If 包裹更稳。
- 布尔派生对象（表达式对）写法示例：`<expression label="on" exp="emit ∧ U &gt; (-Ek)"/>` 无 type 属性也可（缺省 boolean），逻辑符用 Unicode `∧ ∨ ¬` 或用 `and/or/not`，`>` 等要 XML 转义（`&gt;`）。

### 4.4 button（按钮 + 点击脚本）

```xml
<element type="button" label="btnPlay">
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0"/>
	<bgColor r="255" g="255" b="255" alpha="255"/>
	<layer val="7"/>
	<labelOffset x="850" y="70"/>
	<labelMode val="3"/>
	<fixed val="true"/>
	<auxiliary val="true"/>
	<ggbscript val="StartAnimation[t, true]&#xd;&#xa;SetCaption[btnPlay, &quot;暂停&quot;]"/>
	<caption val="播放"/>
	<font serif="false" sizeM="2" size="20" style="0"/>
</element>
```

- `<caption val>` 是按钮上显示的文字。
- **点击脚本 = `<ggbscript val="..."/>` 属性**，这是实测 48 个文件 221 处验证过的标准形态。
- 多行脚本用 `&#xd;&#xa;`（=\r\n）分隔；脚本里的双引号写 `&quot;`。
- 屏幕定位用 `<labelOffset x y/>`。
- `<font sizeM="2" size="20">`：sizeM 缩放档、size 字号。

### 4.5 point 派生对象（表达式对）

```xml
<expression label="P" exp="(a*cos(E)-c, b*sin(E))" type="point"/>
<element type="point" label="P">
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="255" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="1"/>
	<animation step="0.1" speed="1" type="1" playing="false"/>
	<pointSize val="7"/>
	<pointStyle val="0"/>
	<coords x="2.5" y="0.0" z="1.0"/>
	<caption val="行星"/>
</element>
```

- `<expression exp>` 形如 `(x, y)`，可引用数值与其它点。
- **缓存坐标 `<coords x y z="1.0"/>`**，z=1 是齐次坐标（2D 恒为 1.0）。
- 渲染属性：`pointSize`（默认 5）、`pointStyle`（0=圆点，10=十字等）。

### 4.6 conic（圆锥曲线）

```xml
<expression label="Orbit" exp="(x+c)^2/a^2 + y^2/b^2 = 1" type="conic"/>
<element type="conic" label="Orbit">
	<show object="true" label="false" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="0"/>
	<lineStyle thickness="4" type="0" typeHidden="1"/>
	<eqnStyle style="implicit"/>
</element>
```

- 隐式方程写在 `<expression exp>` 里（`= 1` 形式）。
- conic **没有缓存值**；`<lineStyle thickness type/>` 控制线宽/线型，`<eqnStyle style="implicit"/>`。
- 线型 type：0=实线，10=虚线，15=点线等（对照样例实测）。

### 4.7 function（函数）

```xml
<expression label="g" exp="g(x) = (x * tan(20°)) - (10 / ((200 * (cos(20°))^(2))) * x^(2))" type="function"/>
<element type="function" label="g">
	<show object="true" label="true" ev="4"/>
	<objColor r="199" g="80" b="0" alpha="0"/>
	<layer val="0"/>
	<labelMode val="0"/>
	<fixed val="true"/>
	<lineStyle thickness="5" type="0" typeHidden="1" opacity="204"/>
</element>
```

- 表达式形如 `g(x) = ...`（f(x)= 形式），可用 `°` 表示角度，弧度直接写。
- function 无缓存值。

### 4.8 segment / line / ray / vector（command 原语）

```xml
<command name="Segment">
	<input a0="Sun" a1="P"/>
	<output a0="segSP"/>
</command>
<element type="segment" label="segSP">
	<show object="true" label="false" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="0"/>
	<lineStyle thickness="2" type="10" typeHidden="1"/>
	<eqnStyle style="explicit"/>
</element>
```

- `<input a0=起点 a1=终点>` 引用对象的 label；`<output a0=新对象 label>`。
- `name` 可取 Segment/Line/Ray/Vector/Textfield/Polygon 等。
- vector 渲染色、线型同 segment。

### 4.9 polygon（command，多输出）

```xml
<command name="Polygon">
	<input a0="Sun" a1="P" a2="P2"/>
	<output a0="s1" a1="s1a" a1="..." a3="s1c"/>
</command>
```

- 输出 a0=多边形本体，a1..a3=三条边（segment），**每个输出各跟一个 `<element>`**（样例：多边形显示 + 三条边隐藏）。
- 多边形填充色在 `<element type="polygon">` 里：`<objColor r g b alpha="0.25"/>`（alpha 0-1 透明度）+ `<lineStyle ... opacity="63"/>`（0-255 不透明度）。

### 4.10 text（文本 / 动态文本）

静态文本：

```xml
<expression label="titleText" exp='"开普勒三定律模拟"' type="text"/>
<element type="text" label="titleText">
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="2"/>
	<labelMode val="0"/>
	<fixed val="true"/>
	<isLaTeX val="false"/>
	<font serif="false" sizeM="1.0" size="0" style="0"/>
	<absoluteScreenLocation x="500" y="20"/>
</element>
```

动态文本（拼接表达式值，`+` 连接字符串与对象）：

```xml
<expression label="dataText" exp='"r=" + r + "  扫过面积=" + swept' type="text"/>
```

- 字符串字面量用**双引号包住**、写在 exp 里；中文直接放。
- **屏幕定位用 `<absoluteScreenLocation x y/>`**（文本用这个；按钮/复选框用 labelOffset——两套都有样例支撑，别混）。
- `<isLaTeX val="false"/>` 纯文本；需要数学排版再研究 LaTeX 模式（⚠️ 少见，先做纯文本）。
- 纯文本里 `_` 下标**只吃下一个字符**：`E_min` 渲染成 E+下标m+正常"in"；多字符下标要写
  `E_{min}`（`_{}` 花括号形式在纯文本下同样生效，2026-09-04 实测）。
- caption 与 exp 不同：文本对象的`画面内容`由 exp 决定，`caption` 只是代数区说明。

**世界坐标锚定文本**（静态标注贴在图形上、随视图平移缩放）：定位不用 absoluteScreenLocation，
改在 element 里写 `<startPoint x y z="1"/>`——实测形态（线框入磁样张的 × 场标记、v-t 图刻度）：

```xml
<expression label="tx11" exp='"×"' type="text"/>
<element type="text" label="tx11">
	<show object="true" label="false" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="2"/>
	<labelMode val="0"/>
	<fixed val="true"/>
	<isLaTeX val="false"/>
	<font serif="false" sizeM="1.0" size="16" style="0"/>
	<startPoint x="-0.84" y="-0.33" z="1"/>
</element>
```

- 适用：场区标记（⊗/⊙/×）、坐标轴刻度数字、图内小标签（O、B、t/s）。动态拼接文本
  （读数、告警）仍用 `absoluteScreenLocation`——它贴屏幕，不随坐标系漂。
- 点阵类标注（× 阵、刻度）可逐枚写出（真实样板行为），也可 `Sequence` 生成（§4.15）。
- ⚠️ **`<startPoint x y z/>` 的 x/y/z 属性只接受数值字面量**（2026-09-04 3D 计算器实测）：
  写 `x="-6.2*L"` 这类算式会被静默忽略、文本回退到默认位置（曲线标注飘离曲线 500px 级）。
  位置需随参数缩放时，加隐藏锚点对象 + exp 引用：
  `<expression label="P_ek3" exp="(-6.2*L, -6.6*L, 0.02)" type="point"/>`（隐藏）+
  `<startPoint exp="P_ek3"/>`。矢量/线段本就走 `exp` 形态，不受影响。

**动态锚定文本**（跟随动点/矢量端点的数值标注）用 `Text[内容, 锚点]` 命令，内容可拼实时值（实测形态）：

```xml
<command name="Text"><input a0="&quot;v = &quot; + round(val*100)/100 + &quot; m/s&quot;" a1="(0.2, y(P) - k*val)"/><output a0="lblV"/></command>
<element type="text" label="lblV"><show object="true" label="false" ev="4"/><objColor r="0" g="0" b="0" alpha="0.0"/><layer val="2"/><labelMode val="0"/><fixed val="true"/><isLaTeX val="false"/><font serif="false" sizeM="1.0" size="14" style="0"/></element>
```

- 锚点即文本锚（世界坐标）；不再需要 `<startPoint>`。
- ⚠ 含 Text 命令的文件**改动后不要再跑 `ggb_check --fix`**（会解码破坏 `&quot;`；text 类本无缓存，跳过 fix 无损失）。

**文本宽度预算（2026-08-30 两次渲染返工实测，防右边界截断）**：画布文本全角 ≈ 1.0~1.1×字号 px/字、
半角/数字 ≈ 0.5~0.6×字号 px/字符（sizeM=1.0；15 号中文实测 ≈16px/字，经验估计普遍低估 30%+）。
动态文本按**滑杆全域最长字符串**估宽（数值涨一位就溢出：实测 "32 = 32"→"34.05 = 34.05" 被裁），
起点 x + 估宽 ≤ 画布宽 − 20px；放不下拆两行，不要压字号硬挤。

### 4.11 textfield（InputBox 输入框）

```xml
<command name="Textfield">
	<input a0="mp"/>
	<output a0="InputBox1"/>
</command>
<element type="textfield" label="InputBox1">
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0"/>
	<bgColor r="255" g="255" b="255" alpha="255"/>
	<layer val="0"/>
	<labelOffset x="38" y="387"/>
	<labelMode val="3"/>
	<auxiliary val="true"/>
	<caption val="人的质量(50 - 200 kg)"/>
	<length val="4"/>
</element>
```

- `<input a0="被编辑对象 label"/>`——输入框绑定一个数值对象的 label（`mp`），观众改数值写回它。
- 定位用 `<labelOffset x y/>`，`<length val>` 显示字符宽度。


### 4.12 image（图片素材元素）

```xml
<element type="image" label="pic1">
	<file name="73dd…hash/1643865556043.png"/>
	<inBackground val="false"/>
	<startPoint number="0" exp="G"/>
	<startPoint number="1" exp="H"/>
	<show object="true" label="true" ev="3"/>
	<objColor r="0" g="0" b="0" alpha="1"/>
	<layer val="4"/>
</element>
```

- `<file name>` 是 **zip 内相对路径**，也是打包时按引用收图的依据：素材放项目 `<media>/<引用路径>`（或 unpack 产物原目录），zip 内路径=引用路径。
- 定位：双锚点 `<startPoint number="0" exp="P"/>`（左上角点）+ `number="1"`（左下角点，定宽）；纯屏幕背景用 `<inBackground val="true"/>`。
- 配套行为：`ggb_check.py` 对缺失素材告警（warning，不阻塞），`ggb_pack.py` 引用缺失**拒绝打包**、未引用图片提示且不带出。

**适用边界（与 design-rules §0 配套）**：物理对象（动点/场线/矢量）→ 数学对象，禁止图片冒充；符号/示意（电阻、滑轮框、小车…）→ 优先宏命令（§4.13）；装饰/背景（坐标纸、题目截图）→ image 元素。

### 4.13 宏（自定义工具：用命令调用的复用构造）

`macros/` 已提供 106 个成品工具（见 `macros/README.md`）。宏定义形态（`.ggt` 内 `geogebra_macro.xml`）：

```xml
<macro cmdName="开关" toolName="开关" toolHelp="开关[ <Point>, <Point> ]"
       iconFile="…/开关.png" showInToolBar="false" copyCaptions="false" viewId="1">
	<macroInput a0="A" a1="B"/>
	<macroOutput a0="f" a1="g" a2="g'" a3="f'" a4="h" a5="i" a6="C" a7="D"/>
	<construction title="">
		<command name="Midpoint">…</command>
		<element type="point" label="A">…（输入点要在构造里齐全）</element>
		…
	</construction>
</macro>
```

- **调用**：`<command name="开关"><input a0="A" a1="B"/><output a0="f"/>…</command>`，或 expression 内联 `t=开关[A,B]`。
- **示例引健康宏**（2026-08 REVIEW 修正）：本示例选自包含 ✓ 的开关；已审计残缺的宏（如定值电阻：空 label + 悬挂引用 `_1`，「导入 GeoGebra 同样失败」）不得作正面模板，见 `macros/README.md` 质量审计表；直抄形态优先 `macros/snippets/`。
- **嵌入方法（Modify/Generate 通用）**：从 `macros/<类>/<工具>.ggt` 解出 `<macro>` 定义，与图标 PNG 一并加入目标项目（`geogebra_macro.xml` + 图片按 `<file>` 引用路径关系放 `media/`），宏文件的图标引用打包由 ggb_pack 自动处理。
- **检查器支持**：`ggb_check.py` 自动读取同目录 `geogebra_macro.xml` 的 `cmdName` 白名单，`电阻[A,B]` 等调用不再误报未定义。
- **纪律**：cmdName 即命令名，嵌入后必须与调用一致；宏内自带图层/颜色/字号可能与主构造冲突，嵌入后按需覆盖；同课重复元件都走宏（否则就手写几何）。Generate 默认手写几何，仅"标准元件"（电路符号、地面、滑轮框）拷宏——宏定义体积大（20+ 命令），非标准件手写更可控。

### 4.14 轨迹三件套（Locus / CurveCartesian / trace）

```xml
<!-- A. Locus[点, 变量]：动点/数值解轨迹（会随参数重算） -->
<command name="Locus"><input a0="Pball" a1="t"/><output a0="loc1"/></command>

<!-- B. CurveCartesian[fx, fy, 变量, t0, t1]：显式参数曲线（波形族） -->
<command name="CurveCartesian">
	<input a0="x(B) + c" a1="y(B) + (2 * sin((n * c)))" a2="c" a3="0" a4="l"/>
	<output a0="a"/>
</command>

<!-- C. trace：过程痕迹（随动画累积，不产生几何对象） -->
<trace val="true"/>
```

选择优先序：解析可写 → CurveCartesian；有动点/数值解（NSolveODE）→ Locus；要"过程感"演示 → trace，并把复位脚本加 `SetTrace[P,false] SetTrace[P,true]` 重绘。禁止手画折线当轨迹。

**D. CurveCartesian 元素形态**：命令输出 element 的 type 是 `curvecartesian`（不是 locus），
波形/参数曲线通用。真实样张（线框入磁 v-t 图，插图区仿射映射，见 templates/motion-graph.md）：

```xml
<command name="CurveCartesian">
	<input a0="1.15 + u*3.1/tRange" a1="-1.55 + fv(u)*0.325" a2="u" a3="0" a4="tEnd"/>
	<output a0="vtCurve"/>
</command>
<element type="curvecartesian" label="vtCurve">
	<show object="true" label="false" ev="4"/>
	<objColor r="204" g="51" b="0" alpha="0"/>
	<layer val="1"/>
	<labelMode val="0"/>
	<lineStyle thickness="4" type="0" typeHidden="1"/>
</element>
```

- `CurveCartesian[fx, fy, 变量, t0, t1]`；a0/a1 是引用该变量的表达式，a3/a4 为参数区间。
- 「世界坐标插图区」套路：把物理量函数经仿射映射画进图框（`x=1.15+u*3.1/tRange`、
  `y=-1.55+fv(u)*0.325`），配同步跟踪点与同映射的时刻虚线——见 templates/motion-graph.md。

**E. NSolveODE 求阶段边界值**（换自变量法，许可范围的数值解用法，母本 25 处）：

```xml
<expression label="v'" exp="v'(x, v, w) = g/v - K" type="function"/>
<element type="functionnvar" label="v'"><show object="false" label="false" ev="4"/><objColor r="0" g="0" b="0" alpha="0.0"/><layer val="0"/><labelMode val="0"/></element>
<expression label="tau'" exp="tau'(x, v, w) = 1/v" type="function"/>
<element type="functionnvar" label="tau'"><show object="false" label="false" ev="4"/><objColor r="0" g="0" b="0" alpha="0.0"/><layer val="0"/><labelMode val="0"/></element>
<command name="NSolveODE"><input a0="{v', tau'}" a1="0" a2="{v1, 0}" a3="H"/><output a0="nv" a1="nt"/></command>
<element type="locus" label="nv"><show object="false" label="false" ev="4"/><objColor r="0" g="0" b="0" alpha="0"/><layer val="0"/><labelMode val="0"/></element>
<element type="locus" label="nt"><show object="false" label="false" ev="4"/><objColor r="0" g="0" b="0" alpha="0"/><layer val="0"/><labelMode val="0"/></element>
<command name="Point"><input a0="nv" a1="1"/><output a0="P_v2"/></command>
<element type="point" label="P_v2"><show object="false" label="false" ev="4"/><objColor r="0" g="0" b="0" alpha="0"/><layer val="0"/><labelMode val="0"/><pointSize val="3"/><pointStyle val="0"/><coords x="0.6" y="1.67" z="1.0"/></element>
<expression label="v2" exp="y(P_v2)" type="numeric"/>
<element type="numeric" label="v2"><show object="false" label="false" ev="4"/><objColor r="0" g="0" b="0" alpha="0.0"/><layer val="0"/><labelMode val="0"/><value val="1.6706208777116553"/></element>
```

- 导数函数 element 的 type 是 **`functionnvar`**，签名 `f'(x, v, w)`（x=自变量，之后为状态向量分量）。
- `NSolveODE[{导数…}, 自变起始, {初值…}, 终止]` 输出 **locus**。
- **`Point[输出, 1]` 取终点**（参数归一化 [0,1]，1=末端），`y(P)` 取末值——典型用途：
  分段过程中"阶段结束时刻/末速度"（线框入磁：x=进入深度，解到完全进入 x=H 取 v2/τ2）。
- 正确分工：**数值解只喂阶段边界值，曲线本体仍画解析闭式**（线框入磁样板 `fv(x)` 的
  指数段直接解析画出）——数值解是边界探测器，不是轨迹来源。
- L2/L3 校验会对导数函数形参（`q/w/tt` 等）报「未定义标识符」warning（0 error）——形参不是
  全局对象，属预期放行，**不要改写消除**（2026-08-30 实测）。

### 4.15 list / Sequence（列表与点阵）

```xml
<command name="Sequence">
	<input a0="(k, r_1(k))" a1="k" a2="0" a3="10" a4="1"/>
	<output a0="l1"/>
</command>
<command name="Sequence">
	<input a0="Sequence[Vector[(i, j, 0), (i, j, 10)], i, 0, 10, 1]" a1="j" a2="0" a3="10" a4="1"/>
	<output a0="l4"/>
</command>
```

- `Sequence[表达式, 变量, 起, 止, 步长]` 生成列表；**点/矢量的列表是矢量场底座**（配合 `Vector[(i,j),(i,j)+k*E(i,j)]` 用场强公式定箭头，见 design-rules §0）。
- 列表操作：`Flatten[嵌套列表]` 展平、`Element[list,k]` 取元、`Zip[表达式, …]` 并行遍历、`Join/Append/RemoveUndefined`。
- 网格密度 ≤21×21，太多渲染卡顿。
- **条件失效对象的偷懒隐藏法**：列表项坐标包 `If[cond, 有效值, -100]` 移出画布（实测形态，
  用于"主模型失效时事件标记不显示"）——不要 `If[cond, Sequence[…], {}]`（list/set 混用风险），
  也不要用 If 包整个对象隐藏（破坏缓存求值）。

## 5. 脚本（ggbscript）

### 5.1 承载位置

| 想做什么 | 写在哪 |
|---|---|
| 按钮点击脚本 | 按钮 `<element>` 里 `<ggbscript val="..."/>` |
| 对象更新脚本 | 该对象的 `<element>` 里 `<ggbscript onUpdate="..."/>`（滑杆/点/布尔都行） |
| 全局 JS | `geogebra_javascript.js` |

### 5.2 语法要点

- 命令可用 **方括号 `If[...]` 或圆括号 `SetValue(...)`**，同文件可混用（实测两种都有）。
- 多行用 `&#xa;` 或 `&#xd;&#xa;` 分隔；引号、`<`、`>`、`&` 一律 XML 转义（`&quot;`、`&amp;`、`&lt;`、`&gt;`）。
- 赋值即建对象/改值：`v = If[v, false, true]`、`SetValue[t, 0]`。
- 字符串参数 E.g. `SetCaption[btnPlay, "暂停"]`。
- `&apos;` 转义撇号（如 `CenterView[P']`）。

### 5.3 构造命令表（写对象用；真实成品实测统计）

| 命令 | 作用 | 实测频率 |
|---|---|---|
| `Segment` / `PolyLine` / `Polygon` | 线段/折线/多边形（骨架） | 2912 / 数百 |
| `Point` / `PointIn` / `Intersect` / `IntersectPath` | 点/路径上点/交点/路径交点 | 1429 / 41 / 792 / 40 |
| `Vector` | 矢量（速度/力/场箭头） | 1321 |
| `Circle` / `CircleArc` / `CircumcircleArc` / `Semicircle` | 圆/圆弧/外接圆/半圆 | 739 / 49 / 28 |
| `Line` / `Ray` / `OrthogonalLine` | 线/射线/垂线 | 370 / 72 / 256 |
| `Angle` | 角度 | 407 |
| `Midpoint` / `Distance` / `Length` | 中点/距离/长度 | 90 / 214 / 29 |
| `Translate` / `Rotate` / `Reflect` / `Mirror` / `Dilate` | 平移/旋转/对称/相似变换 | 585 / 262 / 70 |
| `If` | 分段条件（见 patterns/if-segment） | 661 |
| `Sequence` / `Zip` / `Flatten` / `Element` | 列表生成/并行/展平/取元（§4.15） | 241 |
| `CurveCartesian` / `Locus` | 参数曲线/轨迹（§4.14） | 88 / 44 |
| `SlopeField` / `NSolveODE` | 方向场/数值 ODE（内置命令，许可范围） | 2 / 25 处 |
| `Integral` | 定积分 | 29 |
| `Textfield` / `LaTeX` | 输入框（§4.11）/公式文字 | 117 / 50 |

脚本命令（`SetValue/StartAnimation/…`）词表见 `interactivity.md` §6；表达不了再上 JS（命令优先原则）。
## 6. 渲染属性家族速查

| 属性 | 位置 | 取值 | 说明 |
|---|---|---|---|
| `show object/label` | `<show/>` | true/false | 画布/代数区可见性 |
| `objColor` | `<objColor/>` | r g b 0-255, alpha | 对象颜色 |
| `bgColor` | `<bgColor/>` | 同上 | 按钮/InputBox 背景色 |
| `layer` | `<layer/>` | 0-9 | 图层叠放 |
| `labelMode` | `<labelMode/>` | 0/1/3 | 标签显示策略 |
| `lineStyle` | `<lineStyle/>` | thickness, type, opacity | 线宽/线型/不透明度 |
| `pointSize`/`pointStyle` | 同层 | 5/0 | 点大小/形状 |
| `caption` | `<caption/>` | 中文 | 中文说明 |
| `eqnStyle` | `<eqnStyle/>` | implicit/explicit | 曲线/段方程样式 |
| `isLaTeX` | `<isLaTeX/>` | true/false | 文本是否 LaTeX |
| `font` | `<font/>` | serif, sizeM, size | 字号 |
| `fixed` | `<fixed/>` | true/false | 锁定 |
| `absoluteScreenLocation` | `<absoluteScreenLocation/>` | x, y | 屏幕定位（文本/滑杆） |
| `labelOffset` | `<labelOffset/>` | x, y | 屏幕定位（按钮/复选框/InputBox） |
| `animation` | `<animation/>` | step, speed, type, playing | 动画 |

## 7. label 命名与书写纪律

1. **label 全局唯一、大小写敏感**；引用必须用完全相同的名字。
2. 建议英文标识符 + 中文 caption：`a/ex/t/dt`、`P/P2`、`Orbit`、`btnPlay`、`showOrbit`。避免 label 含空格、括号、运算符、`°`。
3. **构造顺序即依赖顺序**：被引用的对象必须先于引用者出现（拓扑序）。ggb_check 第三层会用这个顺序做「无循环、无先用后定义」校验。
4. 滑杆/自由对象放最前；中间量（b/c/E/面积）放中间并把 `show object="false"`；画面主对象与文字放后。

## 8. 缓存值规范

- 派生数值对象 `<value val>` 与派生点 `<coords x y z>` 是**加载前的初始显示状态**。
- 规则：这些缓存值由 `ggb_check.py` 的第四层（数值重算）用内置求值器**填充并校验**；Builder 一律**省略** `<value/>`/`<coords/>` 子元素（`--fix` 只新建、不产生空元素）。
- ⚠ **省略 ≠ 空元素**（2026-08 REVIEW 修正）：存在但无值（`<value/>` 无 val）会让 GeoGebra
  报 "For input string: null" 打不开（generate-ggb §9.5 实测）；求值器算不了的类型
  （`Area(s1)`、conic、函数、time 步进等）保持**省略**即可，GeoGebra 加载重算兜底，
  check 打「依赖重算」note 不算错。
- 求值器用**弧度**处理裸三角函数（与真实样例缓存逐位吻合，见 §11 坑 3）。

## 9. 求值器函数子集（与 ggb_check.py 第四层保持一致）

支持：四则 `+ - * /`、幂 `^`、一元负号、括号；比较 `== != < > <= >=`；逻辑 `and or not` 及 Unicode `∧ ∨ ¬ ≥ ≤ ≠`；`If(cond,a,b)`。

函数（圆括号；同时接受方括号以兼容脚本式写法）：`sqrt abs min max sin cos tan asin acos atan ln log exp floor ceil round sign`、`deg(x)`。
常量：`pi`、`e`、`∞`（可略）。后缀 `°` = 乘以 π/180。
字符串拼接 `"..." + obj` 也支持（用于文本对象诊断）。

不在子集内（例）：`Area Distance SetValue` 等命令、`g(x)=...` 函数定义、隐式方程、向量/复数运算 → 标记「求值器子集外」放行。

## 10. 常见坑清单

1. **expression 与 element 的 label 不一致 / element 没紧跟 expression** —— 直接打不开或丢对象。
2. **XML 转义**：表达式里的 `<`、`>`、`&` 必须转义成 `&lt; &gt; &amp;`；脚本里的中文引号用 `&quot;`；文件保存为 UTF-8。
3. **三角函数角度制**：GeoGebra 对裸数字三角函数按弧度算（开普勒样例缓存与弧度级数逐位吻合），不受 `<angleUnit>` 影响；要用角度就显式写 `°` 或 `deg(...)`。别在公式里裸写 `sin(90)` 想要 1。
4. **`ex^2` 不是 `ex²`**：重载/平方展开都能省，但字符集不同的 `²` 少用，统一 `^2`。
5. **缓存值必须与公式一致**：改了 exp 忘了改 `<value>`，GeoGebra 加载时会重算覆盖，但缩略图/首屏可能闪旧值；交给 ggb_check 统一重算。
6. **画布放不下**：`coordSystem` 的 scale 与内容坐标要匹配（轨道尺度过大就 `xZero/yZero/scale` 调小）。交互件像素坐标要落在 `<gui><window width height>` 与 `<euclidianView><size>` 范围内。
7. **按钮/复选框用 `labelOffset`，文本/滑杆用 `absoluteScreenLocation`**，别混（两套都有真实样例，混用行为不稳定）。
8. **脚本命令用 `[ ]` 或 `( )` 均可，但在 `<expression exp>` 的公式里函数用 `( )`**。混淆点在于 SetCaption 是脚本命令（`[]`），`if` 在公式里也可用 `If(cond,a,b)`。
9. **依赖顺序**：引用未定义对象 = 加载报错。命令输出先声明 element 再被后续引用。
10. **动画 `type`**：0=递增到顶重来、1=振荡往返、2=递减、3=递增一次到头停。模拟时钟常用 1（振荡）。
11. **脚本变量必须先定义**：`ggbscript` 里引用的一切标识符（含赋值目标）要么是已定义对象，
    要么是本脚本先前已赋值的变量；`v = If[v, false, true]` 这种「自引用创建」在 v 不存在时
    GeoGebra 求值 RHS 即报「未定义变量」（实机确认）。翻转开关先建隐藏布尔自由对象。
    ggb_check L2 第 4 步负责拦截（下标等价 `a_1 ≡ a_{1}` 已做规范化）。
12. **表达式里别用 `min(a, b)` / `max(a, b)` 逗号多参**（实机确认：`sEff = min(v*t, Ltot)`
    在 GeoGebra 表达式解析器报错 `error in <expression>`）。数值钳制一律写
    `If(a < b, a, b)`——GeoGebra 的 If 三参在表达式与脚本里都稳定。注意：ggb_check 的
    求值器为了兼容故意支持 min/max 多参，**通过校验 ≠ GeoGebra 能解析**，Builder 自查此坑。
13. **自定义函数体里的奇偶/取模**：`f(u) = If[Mod[floor(u), 2] == 0, 1, -1]` 实机确认
    GeoGebra 加载报 `error in <expression>`（单独 `Mod[5,2]` 与 `floor(u)` 均正常，组合进函数体即失败）。
    奇偶性统一写 `(-1)^k` / `(-1)^floor(u)`（负底数整数幂实测可行）。此类表达式 L4 标
    「求值器子集外」放行——**五层校验全过也可能加载失败，含 function 定义的对象必须渲染/实机验证**。
14. **函数名一律小写**（2026-08-30 实测）：`Abs(...)`、`Sqrt(...)` 等首字母大写的**函数**在
    `<expression>` 解析报 `error in <expression>`（命令才用 CamelCase：If/Min/Element/Sequence…；
    Min/Max 单参列表形态可用，两参 `Min(a,b)` 在表达式层仍按坑 12 改 `If(a<b,a,b)`）。

## 11. 样例解剖：开普勒三定律模拟（基准）

解剖对象 `../fixtures/kepler-baseline.xml`（144 行，来自开普勒三定律模拟基准）：

- **画面**：1200×800 窗口，原点 (560,380)，scale=40；6 根滑杆竖排左侧（a/ex/t/dt/a2/ex2，absoluteScreenLocation 定位），右侧 3 行文本 + 数据行。
- **滑杆时钟**：`t` 滑杆 `min=0 max=2π step=0.02 type=1(振荡) playing=true` 做**主时钟**；`dt` 是第二定律时间间隔。
- **物理**：`M = t`（平近点角线性），偏近点角 `E = M + e·sin(M) + (e²/2)sin(2M) + (e³/8)(3sin(3M)–sin(M))`（开普勒方程级数解，**非匀速扫角**——这就是「物理真实性」红线的落地），行星点 `P=(a·cosE–c, b·sinE)`。
- **第二定律**：`Polygon(Sun,P,P2)` 与 `Polygon(Sun,P2,P3)` 两块面积用 `Area(s1)/Area(s2)` 对比，配 `caption` 说明「相等时间扫过相等面积」。
- **第三定律**：`T1=a^(3/2)`、`ratio1=T1²/a³`，动态文本 `"T²/a³=" + ratio1` 实时显示，两轨道比率应同。
- **交互线索**：无按钮/JS（纯滑杆动画 + 动态读数）；`geogebra_javascript.js` 只有 `function ggbOnInit() {}` 占位。

这张采样例可以直接抄作「轨道/运动学题型」的构造骨架（模板见 `templates/orbital-motion.md`）。

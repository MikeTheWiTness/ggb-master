# interactivity —— 滑杆/动画/按钮/复选框/InputBox/JS

> 全部交互件的 XML 形态与编排方法。形态均来自对真实 GeoGebra 成品的拆解验证（100+ 文件）。
> 脚本优先 GeoGebra 命令语法，表达不了才用 JS（命令优先原则）。

## 1. 交互件总览

| 件 | XML 形态（金标准 §4） | 定位方式 | 脚本载体 |
|---|---|---|---|
| 滑杆（numeric 自由） | `<element type="numeric">` + `<slider/>` | `absoluteScreenLocation` | `onUpdate` |
| 复选框（boolean） | `<element type="boolean">` + `<value/>` `<checkbox/>` | `labelOffset` | `onUpdate` |
| 按钮 | `<element type="button">` + `<caption/>` | `labelOffset` | `ggbscript val`（点击） |
| InputBox（textfield） | `<command name="Textfield">` + `<element type="textfield">` | `labelOffset` | — |
| 动态文本 | `<expression type="text">` 字符串拼接 | `absoluteScreenLocation` | — |

## 2. 动画四要诀

1. **主时钟**：一个数值滑杆承担时间轴，`<animation step="0.02" speed="1" type="1" playing="false"/>`。
   - `type`：0=递增到顶重来，1=**振荡往返**（乐器/往复类默认），2=递减，3=递增一次停。
   - `step`：每帧增量；`speed`：倍速。step 越小越平滑（0.01~0.05 合适，模拟里 2π 周期用 0.02）。
   - **初始一律 `playing="false"`（打开不播，§3 实测教训）**；只有一个滑杆承担动画，其余静止。
   - 播完自停型：`type="3"`（递增一次停）+ `max` 绑派生终点（§2.1）。
2. **动画对象**：让某个 object 随时间动 → 它的坐标/值表达式里引用主时钟 `t`。
3. **起停**：`StartAnimation[t, true/false]`；**归零**：`SetValue[t, 0]`。
4. **动画速度与物理量的对应**：物理真实性要求运动规律本身正确（开普勒不能匀速），动画只是播放机制。

### 2.0 展示时间轴与物理时间解耦（流畅优先）

过程演示的首要目标是连续、可辨认的运动画面。若题目的真实过程很短，或按真实时间驱动会造成卡顿，允许把展示时钟设为独立的 `0~5 s` 或 `0~10 s`，再用线性映射把展示时刻换算为物理时刻：

```text
tPhys = tAnim / tAnimMax · tPhysicalEnd
```

- 轨迹、速度和相对运动公式引用 `tPhys`；播放/暂停/重置和终点判断引用 `tAnim`。
- 画面读数应明确这是“动画时间”还是“物理时间”，不要把演示时钟误标成题目真实时间。
- 优先选能稳定播放的 `0~5 s` 或 `0~10 s`；动画步长通常取 `0.01~0.03`，再调 `speed` 使全过程连续播放。允许演示时间与题目数值不完全相同，但不得改变状态随物理时刻的函数关系。
- GeoGebra 的 `StartAnimation` 需要数值对象绑定 `<slider>`；若不希望画面出现时间条，保留一个 `show object="false"` 的隐藏滑动条即可。
- 验收至少检查初态、中段和终态：动点无跳跃、速度矢量方向连续、终点自动停下且按钮状态复位。

### 2.1 播完自停（阶段演示专用，2026-08 线框入磁样张验证）

过程型演示（播到"演示终点"自动停、按钮自动复位）的标准组合——**动态上限 + 一次型动画 + 按钮态复位**：

- **滑杆 `max` 直接引用派生数值 `tEnd`**（`<slider min="0" max="tEnd" …/>`），参数变化时上限自动伸缩；
  场景里的函数、插图区曲线都画到 `tEnd`，不用再手动同步视图范围。
- **`animation type="3"`**（递增一次到头停）——到上限即自停，不振荡回绕。
- **滑杆 `ggbscript onUpdate`** 在到顶时把播放按钮文字复位（否则按钮还停在「暂停」上）：

```xml
<element type="numeric" label="t">
	<value val="0"/>
	<slider min="0" max="tEnd" width="150" x="320" y="8" absoluteScreenLocation="true" fixed="false" horizontal="true" showAlgebra="true"/>
	<lineStyle thickness="10" type="0" typeHidden="1"/>
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="1"/>
	<animation speed="1.2" type="3" playing="false"/>
	<caption val="时间 t（动画主时钟）"/>
	<ggbscript onUpdate="If[t &gt;= tEnd, SetCaption[btnPlay, &quot;播放 ▶&quot;]]"/>
</element>
```

- 配套：按钮仍是 §3 播放/暂停母本（不引缺失变量）；重置按钮 `SetValue[t,0]` + 复位 `playing`。
- 注意：`type="3"` 只用于"播完即止"的过程演示；往复/周期演示仍用 `type="1"`。

## 3. 按钮模板（点击脚本）

**先定义开关布尔，再写按钮**——脚本赋值虽可运行时建对象，但 RHS 引用不存在的变量会直接报
「未定义变量」（实测）。播放/暂停二合一的标准做法：

```xml
<!-- 隐藏布尔开关：必须预先定义。打开不播、一点即播（GeoGebra 加载不自动启动动画） -->
<element type="boolean" label="playing">
	<value val="false"/>
	<show object="false" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="7"/>
	<labelMode val="0"/>
	<checkbox fixed="true"/>
</element>
<element type="button" label="btnPlay">
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0"/>
	<bgColor r="255" g="255" b="255" alpha="255"/>
	<layer val="7"/>
	<labelOffset x="850" y="70"/>
	<labelMode val="3"/>
	<fixed val="true"/>
	<auxiliary val="true"/>
	<ggbscript val="playing = If[playing, false, true]&#xd;&#xa;StartAnimation[t, playing]&#xd;&#xa;SetCaption[btnPlay, If[playing, &quot;暂停&quot;, &quot;播放 ▶&quot;]]"/>
	<caption val="播放 ▶"/>
	<font serif="false" sizeM="2" size="20" style="0"/>
</element>
```

要点：
- 多行脚本 `&#xd;&#xa;` 分隔；脚本内双引号写 `&quot;`，单引号 `&apos;`。
- 常用组合拳：`SetValue[t,0]` 归零再 `StartAnimation[t,true]`（重置并播放）；切换按钮文字用 `SetCaption`。
- **打开不播、一点即播**（2026-08 实测教训）：GeoGebra 加载文件不自动启动动画，即使滑杆
  XML 里 `playing="true"`。因此标准初始态：`playing=false` + caption「播放 ▶」+
  主时钟 `animation playing="false"`——打开后点一次即开播，文字与状态同步。
  切勿初始 caption「暂停」（曾造成「先切到播放、再点才播」的错位）。
- 翻转布尔必须引用**预定义**的隐藏布尔（如上 `playing`），不能凭空 `v = If[v,...]`——成品样例能那样写是因为其文件里已有隐藏布尔 `v`。

### 3.1 四母本速查（真实成品 685 个按钮聚类：形态/频率/母本）

| 母本 | 脚本（可直抄） | 频率 | 说明 |
|---|---|---|---|
| 播放/暂停（极简） | `SetValue[e,¬e]&#xa;StartAnimation[α,e]` | 57 | 复用已有布尔 e；按钮文字固定"播放/暂停" |
| 播放/暂停（联动） | `SetValue(on,!on)&#xa;If(on,SetCaption(b1,"暂停"),SetCaption(b1,"启动"))&#xa;StartAnimation(t,on)` | 27 | 上段完整模板的同款 |
| 复位 | `t=0`；完整型 `t=0&#xa;StartAnimation[t,false]&#xa;ZoomIn[1]` | 30 / 15 | 批量参数逐个 `SetValue`；先置零后停动画 |
| 显隐开关 | `SetValue(show1,!show1)&#xa;If(show1,SetCaption(b1,"隐藏波动1"),SetCaption(b1,"显示波动1"))` | 28+17 | 对象侧用 `<condition showObject="show1"/>`；多视图批量用 onUpdate + `SetVisibleInView` |
| 步进 | `If(n<10,SetValue(n,n+1))&#xa;If(n<10,SetColor(b3,"red"),SetColor(b3,"gray"))` | 14 | 越界保护写进每条 If；颜色表达"到边界"。n 为整数步进滑杆 |

- 频率为候选库统计口径（方括号/圆括号两种调用形态等价，聚类时已归一）；母本详情见 `../patterns/` 对应选型卡。
- 复位本质是**所有自由对象回初值**：设计阶段给每个参数定初值，按钮复位列清单逐一核对（含布尔开关，否则状态与文字错位）。

## 4. 复选框用法

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

- 控制可见性：把对象表达式包进 `If[showOrbit, 原表达式, 占位]`——但**不要**用 If 隐藏（会破坏缓存求值）；
  更稳的做法：`<ggbscript onUpdate="SetVisibleInView[Orbit, 1, showOrbit]"/>` 写在复选框上，或用 JS 的 `setVisible`。
- 控制公式分支：`v = If[check, a, b]`（布尔派生对象，金标准 §4.3）。

## 5. InputBox（输入框）

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

- `<input a0>` 绑定被编辑的数值对象；观众输入数值写回该对象（超范围值 GeoGebra 会拒绝/截断）。
- InputBox 适合教师层快速试数，但**默认演示**优先滑杆（一目了然）。

## 6. ggb 脚本词汇表（真实成品实测）

| 命令 | 作用 | 示例 |
|---|---|---|
| `SetValue[obj, v]` | 设值 | `SetValue[t,0]` |
| `StartAnimation[obj, b]` | 开/停动画 | `StartAnimation[t,true]` |
| `If[cond, a, b]` | 条件 | `v=If[v,false,true]` |
| `SetCaption[obj, "s"]` | 改 caption | `SetCaption[b,"已开启"]` |
| `SetVisibleInView[obj, viewNo, b]` | 视图内可见 | `SetVisibleInView[P,1,true]` |
| `SetColor[obj, r,g,b]` / `[obj,"red"]` | 颜色 | `SetColor[P,255,0,0]` |
| `SetLineThickness[obj, n]` | 线宽 | `SetLineThickness(u,P+1)` |
| `SetTrace[obj, b]` | 痕迹 | `SetTrace[P,true]` |
| `CenterView[obj]` | 视图居中 | `If[fold,CenterView[P']]` |
| `ZoomIn[factor]` / `ZoomOut` | 缩放 |   |
| `Execute[{"cmd1","cmd2"}]` | 批量执行命令字符串 |   |
| `RunClickScript[obj]` | 触发别的按钮 | `RunClickScript[bReset]` |
| `ShowLayer[n]` / `HideLayer[n]` | 图层显隐 |   |

命令参数用方括号（`[ ]`）或圆括号均可；**赋值**（`v = If[...]`）在脚本里合法。

## 7. 什么时候升级 JS（判定清单，命令优先原则的边界）

ggb 命令语法表达不了（再考虑 `geogebra_javascript.js`）：

1. 复杂循环/递归数据结构（ggb 的 Sequence/Iteration 不够）。
2. 精细事件控制（多对象联动、防抖、时序编排）。
3. 数学运算超集（矩阵批量、特殊函数）。
4. 需要调用 GeoGebra JS API 的外部交互（`ggbApplet.evalCommand`、`registerObjectUpdateListener`、`getValue`/`setValue`、`setVisible`）。

**先写一个「为什么 ggb 语法不够」的清单，确认了再动 JS。** ggb_check 只对 JS 做语法检查（`node --check`），没有语义校验——JS 层出的 bug 完全靠打开验证。

## 8. 常见坑

1. 脚本里引号不转义 →XML 解析失败；统一 `&quot;`。
2. 用 `If[check, expr, 占位]` 隐藏对象 → 缓存求值被占位污染；改用 SetVisibleInView/JS setVisible。
3. 动画 step 太大（>0.05）→ 掉帧/跳变；step 太小（<0.005）→ 一帧走不完一圈。
4. 按钮文字改不动 → SetCaption 第一个参数必须与按钮 label 完全一致（大小写）。
5. InputBox 绑定对象后观众输入超范围 → 设计时给 caption 写范围提示（如「50 - 200」）。
6. **脚本变量未定义**（`v = If[v,...]` 报「未定义变量」）→ 脚本引用的一切变量（含赋值目标）
   必须是已定义的自由对象或本脚本先前已赋值的变量；开关布尔先建隐藏 `<element type="boolean">`。
   ggb_check L2 会拦截此类错误（含下标等价 `a_1 ≡ a_{1}` 的规范化）。
7. **Min/Max 没有单参重载**（实测：`SetValue[v, Max(vStar, Min(v))]` 报「参数不符合规则：数字 v」）——
   别想用 `Min(obj)` 取滑杆下限。下限/上限直接写数值，或 `If[val > 1.2, val, 1.2]` 钳制。

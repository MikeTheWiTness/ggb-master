# 题型手册：运动 + 图像关联（v-t 同窗样板）

> 适用：物理过程分阶段推进，需要**运动画面与 v-t/x-t 图像同窗对照**的探究（线框进出磁场、
> 板块模型、碰撞前后、传送带等）。观众拖动时间轴时，场景与图上的跟踪点同步走。
> **公式自推声明（SKILL.md 第 0 条）**：本模板只给构造套路、XML 形态与实测坑；分段
> 物理公式由模型自行推导并用 design.md「模型层自检」自查。线框入磁的三段解析式
> （自由落体 → 阻尼进入 → 尾段）见 `fixtures/线框入磁-vt-baseline.xml` 头注释（解剖引用）。
> 基准样例：`fixtures/线框入磁-vt-baseline.xml`（真实成品解包原样收录，全构造可打开对照）。

## 适用场景

- 状态 = 时间的**分段解析闭式**（每段匀速/匀变速/指数趋近等），段间由事件切换。
- 演示核心是「运动 → 图像」对应：曲线斜率（加速度）、拐点（阶段切换时刻 t₁/t₂）、
  水平渐近段（临界速度）与场景中物件的运动状态一一对应。
- **不适用**：轨迹类演示（曲线画轨迹用 §4.14 优先序）或与图像无关的纯运动学。

## 构造套路（六步）

1. **阶段划分 + 解析闭式（公式自推）**：把过程写成 `fv(x) = If[x<t1, …, If[x<=t2, …, …]]`、
   `fs(x) = …`（位置同构分段）。每段一个解析式，段界时刻 t₁/t₂ 是派生数值；各段公式
   由模型按物理定律自推（样板：线框入磁三段式见 fixture 头注释）。
   - 结构要点（语料）：段界处边界条件严格连续（`If[x<=t2,…]` 用 `<=` 而非 `<`，
     两段在界点同值），防跳变。
2. **数值解只用于段界值，不画曲线**（本样板最精妙处）：进入过程换自变量消去时间——
   `dv/dx = (g−K·v)/v`、`dτ/dx = 1/v`，`NSolveODE[{v', τ'}, 0, {v1, 0}, H]` 解到
   完全进入（x=H），`Point[nv, 1]`（参数归一化 [0,1]，**1=终点**）取末端 v2、τ2。
   曲线本体仍由解析 `fv` 画——数值解只喂边界值，两全其美（详见 construction §4.14D）。
3. **单视图插图区 v-t 图（本样板核心，不用第二个 Graphics 视图）**：
   在**同一个视图**右下角划一块世界坐标图框，用**仿射映射**把物理函数画进图框：
   - 图框定位点：`Px0=(1.15,-1.55)`（原点）、`Px1=(4.25,-1.55)`（t 轴端点）、
     `Pv1=(1.15,1.05)`（v 轴端点）；轴用两根 `Segment`。
   - 映射公式（横轴 tRange→3.1 单位、纵轴 8 (m/s)→2.6 单位，比例 0.325）：
     `x_图 = 1.15 + (u/tRange)*3.1`，`y_图 = -1.55 + v*0.325`。
   - 曲线：`CurveCartesian(1.15 + u*3.1/tRange, -1.55 + fv(u)*0.325, u, 0, tEnd)`。
   - **同步跟踪点**：`Trk = (1.15 + t*3.1/tRange, -1.55 + fv(t)*0.325)`——时间轴一动，
     场景线框与图上的点同时走，这就是「运动和图像关联」的直观来源。
   - 关键时刻虚线（t₁/t₂）用**同一映射公式**生成一段线段（含横坐标 `1.15+t1/tRange*3.1`），
     与曲线精确对位；临界速度画水平虚线（图例文案说明线型含义）。
   - 刻度/轴名：静态文本 `"0"` `"2"`…`"t/s"` `"v/(m/s)"`，用 `<startPoint x y z="1"/>`
     锚在世界坐标（随视图缩放，见 construction §4.10）。
   - 图框坐标与场景坐标在同一个坐标系里，提前算好布局：场景区与图框区不重叠即可。
4. **场景可视化**：隐藏全局坐标轴（`<evSettings axes="false">` + 两轴 `show="false"`），
   滑杆顶栏排布；物件的几何（多边形顶点）按 `fs(t)` 驱动；运动必配速度矢量
   `Vector[M0, M0+fv(t)*比例]`（design-rules §0）；磁场区域配 × 点阵场标记
   （文本 `"×"` 逐枚 `startPoint` 锚定，5×4、间距 0.3×0.4；可 Sequence 生成，逐枚写是真实样板行为）。
5. **播完自停主时钟**：`t` 滑杆 `max="tEnd"`（**动态上限，引用派生数值**）+
   `animation type="3"`（递增一次到头停）+ 滑杆 `ggbscript onUpdate=If[t>=tEnd, SetCaption[btnPlay,"播放 ▶"]]`
   复位按钮文字（interactivity §2 播完自停）。
6. **一键演示与警示**：播放/暂停 + 重置按钮（interactivity §3 母本）、一键临界值按钮
   （`SetValue[k, 1]`）、情形判读文本（`If[k>1.001, "减速进入", If[k<0.999, "加速进入", "匀速进入"]]`，
   阈值 ±0.001 防 k=1 抖动）、超视野/超量程警示文本（design-rules §6.3）。

## 关键 XML 片段

NSolveODE 求段界值（派生函数 + 命令 + 取终点）：

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
```

插图区 v-t 曲线与跟踪点：

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
<expression label="Trk" exp="(1.15 + t*3.1/tRange, -1.55 + fv(t)*0.325)" type="point"/>
<element type="point" label="Trk">
	<show object="true" label="false" ev="4"/>
	<objColor r="204" g="0" b="0" alpha="0"/>
	<layer val="2"/><labelMode val="0"/>
	<pointSize val="6"/><pointStyle val="0"/>
	<coords x="1.15" y="-1.55" z="1.0"/>
</element>
```

播完自停主时钟：

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

## 常见坑

1. **别急着上第二个 Graphics 视图**：布局 XML（perspective/panes/双 euclidianView）形态未在
   本 skill 语料实测验证；单视图插图区（本样板）是真实成品验证过的做法，且天然保证
   场景与图像同坐标系、跟踪点简单对位。
2. `Point[NSolveODE输出, 参数]` 的参数是**归一化 [0,1]**，取终点用 `1`（同 generate-ggb §9.5）。
   输出 element 的 type 是 `locus`；导数函数 element 的 type 是 `functionnvar`。
3. 曲线用 `CurveCartesian` 而非手工折线；`CurveCartesian` 输出 element 的 type 是
   `curvecartesian`（不是 locus）。
4. 刻度、时刻虚线、跟踪点共用**同一套映射公式**——改一个量（如 tRange）时其余跟着变，
   不会对位错开；写成独立副本则必然漂移。
5. 动态上限滑杆：`<slider max="tEnd">` 合法；参数变化时上限自动伸缩。`tEnd` 别用固定值
   写死，否则改参数后动画过长/过短。
6. 极端参数下出图外（释放高度超视野、末速度超量程）：警示文本放在显眼处并在
   caption 给解法提示（减小 k / 增大 B·l / 减小 m·R），不要静默截断。
7. 分段 If 的段界用 `<=` 对齐，边界值从数值解取（`y(P_v2)`），两段在界点严格连续，
   曲线才没有肉眼可见的折角断裂。
# 题型手册：轨道 / 运动学模拟

> 适用：行星轨道、抛体/圆周运动、追及相遇、简谐振动等**解析解运动学**探究。
> **公式自推声明（SKILL.md 第 0 条）**：本模板只给构造套路、XML 形态与实测坑；
> 具体运动方程由模型按物理定律自行推导，并用 design.md「模型层自检」自查
> （守恒恒等式、量级、边界连续）。样例公式仅作解剖引用（见 construction-language §11）。
> 基准样例：`开普勒三定律模拟.ggb` 解剖见 construction-language.md §11。

## 适用场景

- 状态 = 时间的显式函数（位置、角度、相位随时间可解析表达）。
- 观众通过拖参数滑杆/播放动画观察运动轨迹与规律。
- **不适用**：手写积分递推的系统（JS/Sequence 循环）；三体/变轨等内置 `NSolveODE` 可解的见 patterns/nsolveode.md。

## 构造套路（五步）

1. **选主时钟**：一个 `t` 滑杆（范围 0~2π 或 0~T），`type="1"` 振荡，**初始不播**（`playing="false"`，打开后点播放开始——interactivity.md §3 实测教训）。
2. **写解析运动学**：位置 = f(t, 参数)，每个物理量一个滑杆、不写死在公式。
   - 运动方程的推导交给模型自身（自推 + 自检）；写进 design.md 后在此处只留「状态 =
     f(t, 参数)」一行总览。样例：开普勒用平近点角 → 解偏近点角（级数/牛顿迭代）得
     椭圆位置，**禁止用匀速扫角近似**（见坑 1）。
3. **画轨迹**：隐式曲线（conic）或 `Trace[P]`/`Locus`；多时刻快照点（`P2/P3` 用 `t+dt`）。
4. **动态读数**：文本对象拼接 `"v=" + v`，实时显示物理量。
5. **一键演示**：播放/重置按钮（ggbscript），复选框切换可见层。

## 关键 XML 片段

主时钟滑杆（其余滑杆照此去掉 playing；子元素按金标准 §4.1 推荐新序）：

```xml
<element type="numeric" label="t">
	<value val="0"/>
	<slider min="0" max="6.283185307179586" width="180" x="20" y="130" fixed="false" horizontal="true" absoluteScreenLocation="true" showAlgebra="true"/>
	<lineStyle thickness="10" type="0" typeHidden="1"/>
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="1"/>
	<animation step="0.02" speed="1" type="1" playing="false"/>
	<caption val="时间 t（动画）"/>
</element>
```

动画点：`<expression label="P" exp="(x(t), y(t))" type="point"/>` + `<element type="point">`（缓存 `<coords/>` 省略，由 --fix 填充；`<animation step="0.1" playing="false"/>`）——x(t)/y(t) 为自推的位置函数。

播放/重置按钮脚本：

```xml
<ggbscript val="SetValue[t, 0]&#xd;&#xa;StartAnimation[t, true]"/>
```

## 常见坑

1. **匀速造假（红线例证）**：行星轨道若让扫角匀速（位置 = 圆参数方程直引 t），近日点
   与远日点快慢会颠倒。必须平近点角 → 开普勒方程解偏近点角。模型自检口径：角速度在
   近日点快、远日点慢。**判定权在物理直觉，红线在 skill 纪律（SKILL.md 第 3 条）**。
2. 滑杆范围要给真实物理量区间（单位要标），step 匹配精度。
3. 轨道比例：`coordSystem scale` 要覆盖全部轨道（近地点~远地点）；两轨对比注意尺度一致。
4. 第二定律面积对比：用 `Polygon`（太阳+两时刻点）`Area()` 对比，时间间隔由 `dt` 滑杆控制。
5. 读数文本太长 → 超画布；GeoGebra 文本换行用回车，控制每行长度。
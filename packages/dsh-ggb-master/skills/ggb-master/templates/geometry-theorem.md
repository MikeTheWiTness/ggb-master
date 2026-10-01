# 题型手册：几何定理探究

> 适用：三角形四心、圆幂定理、动态几何、辅助线观察、轨迹探究等「拖点看性质」课件。

## 0. 绘图模式 vs 几何模式（构造哲学）

文件格式上没有「几何模式」：同一个 geogebra.xml 用 GeoGebra 任意模式打开都渲染。
「几何感」来自**构造方式**，不是 app 壳：

- **本题型的主场构造哲学 = 几何关系优先**：多用几何命令
  （`Midpoint`、`PerpendicularLine`、`Circle(O,P)`、`Intersect`），
  少用坐标算术（`P=(a,b)` 写死坐标是绘图模式思维，拖不动/不自然）。
  自由点 `<element type="point">` 直接可拖，派生对象自动跟随——这就是「几何模式」体验，
  绘图模式同样具备。
- **不要为了「几何模式」切换 app 壳**：几何 app 里滑杆/数值/代数区设施弱化，
  对探究课件的读数和交互反而不便；继续用 classic/graphing 打开即可。
- 需要坐标数值参与的（角度读数、距离度量、轨迹方程）正常用 expression 派生，
  两者混排没有障碍（Angles 用 `Angle(A,B,C)`、长度用 `Distance`）。

## 适用场景

- 探究对象是**几何不变量**：拖自由点/动点，观察某个度量（角度、长度、比、面积）不变。
- 观众角色多为学生自己拖拽验证，不需要复杂动画。
- 交互重心：自由点 + 动态读数 + 复选框（显示/隐藏辅助线）。

## 构造套路（五步）

1. **自由几何对象**：用滑杆定位（`numeric` 滑杆当参数）或自由点（自由点 XML 形态 = `<element type="point">`，不带 expression），拖拽交互。
   ⚠️ 自由点在 XML 里是 `<element type="point" label="A">` + `<coords x y z>` 无 expression——Builder 写的时候坐标即初值，观众可拖。
2. **派生度量**：`Distance(A,B)`、`Angle(A,B,C)`、`Area(tri)`、`Length(seg)` 都写成派生 numeric（show=false），供动态文本使用。
3. **定理对象**：conic（圆/椭圆/双曲线）、线段、垂线 `PerpendicularLine`、中点 `Midpoint`、内心 `Incenter` 等命令——全部走 `<command>` + 输出 element。
4. **动态读数**：文本对象把度量拼接出来，如 `"∠ACB = " + ang`；单位/精度通过格式或 caption 说明。
5. **演示控制**：
   - 复选框（`labelOffset` 定位）切换辅助线可见性：`<ggbscript onUpdate="SetVisibleInView[aux, 1, showAux]"/>`。
   - 重置按钮：`SetCoords[A, x0, y0]` 回初始位置（先把初始坐标写死到脚本里），或整组 SetValue。
   - 需要「动画到某位置」：用 Slider + `Zoom(1)`… 简单场景用按钮归位即可。

## 关键 XML 片段

中点 + 度量：

```xml
<command name="Midpoint">
	<input a0="A" a1="B"/>
	<output a0="M"/>
</command>
<element type="point" label="M">
	<show object="true" label="false" ev="4"/>
	<objColor r="255" g="0" b="0" alpha="0.0"/>
	<layer val="1"/>
	<labelMode val="1"/>
	<pointSize val="5"/>
	<pointStyle val="0"/>
</element>

<expression label="dAB" exp="Distance(A, B)" type="numeric"/>
<element type="numeric" label="dAB">
	<show object="false" label="false" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="0"/>
</element>
```

动态读数文本：`<expression label="info" exp='"AB = " + dAB + "   ∠C = " + ang' type="text"/>`。

## 常见坑

1. **依赖顺序**：命令输出先声明，度量的表达式引用它们要在后。
2. `Distance`/`Angle` 由 ggb_check 求值器**算不了**（子集外）→ 缓存留空，GeoGebra 加载重算；不要手填。
3. 自由点拖动后缓存坐标会变——**自由点的 `<coords>` 是初值不是缓存**，别用 --fix 去「修正」它（check 只处理 expression 派生点）。
4. 角度单位：显示度数时公式里 `Angle(A,B,C)` 默认弧度，文本拼接要 `Deg(ang)` 或 caption 说明。
5. 复选框 onUpdate 里 `SetVisibleInView` 的第 2 个参数是视图号（1=2D 绘图区），写错不报错但没效果。
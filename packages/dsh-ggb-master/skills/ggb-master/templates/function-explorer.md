# 题型手册：函数参数探究

> 适用：二次函数开口/平移、正弦波相位/振幅/频率、指数增长、参数曲线等「拖参数看图像」课件。

## 适用场景

- 探究对象是一个**参数化函数族**：拖参数滑杆，图像/性质随之变化。
- 观众观察：极值、零点、交点、区间单调性、图像形状的变化规律。
- 核心交互：参数滑杆 + 函数图像 + 动态读数 + 可选轨迹/动点。

## 构造套路（五步）

1. **参数滑杆**：每个系数一个滑杆（a、b、c；A、ω、φ…），范围给典型值（如 a∈[-3,3] step=0.1，A∈[0.5,3] step=0.1）。
2. **函数对象**（金标准 §4.7）：
   ```xml
   <expression label="f" exp="f(x) = a*x^2 + b*x + c" type="function"/>
   <element type="function" label="f">
   	<show object="true" label="true" ev="4"/>
   	<objColor r="0" g="0" b="150" alpha="0.0"/>
   	<layer val="1"/>
   	<labelMode val="0"/>
   	<fixed val="true"/>
   	<lineStyle thickness="4" type="0" typeHidden="1" opacity="204"/>
   </element>
   ```
   正弦：`f(x) = A*sin(ω*x + φ)`。函数表达式里 `x` 是自变量（不是对象引用）。
3. **特征点**：顶点 `( -b/(2a), f(-b/(2a)) )`、零点 `Root(f)`、极值 `Extremum(f)`——派生点/命令输出，随参数联动。
4. **动态读数**：`"顶点 = " + 顶点`；判别式、对称轴等派生数值实时显示。
5. **对比与轨迹**：复选框切换第二函数/网格；动点沿曲线滑动（`Point(f)` 路径参数 + `t` 滑杆），观察切线斜率 `Slope` / 导数 `Derivative(f)` 输出函数曲线。

## 关键 XML 片段

函数 + 顶点：

```xml
<expression label="f" exp="f(x) = a*x^2 + b*x + c" type="function"/>
<element type="function" label="f">
	<show object="true" label="true" ev="4"/>
	<objColor r="0" g="0" b="150" alpha="0.0"/>
	<layer val="1"/>
	<labelMode val="0"/>
	<fixed val="true"/>
	<lineStyle thickness="4" type="0" typeHidden="1" opacity="204"/>
</element>

<expression label="V" exp="(-b/(2a), f(-b/(2a)))" type="point"/>
<element type="point" label="V">
	<show object="true" label="false" ev="4"/>
	<objColor r="200" g="0" b="0" alpha="0.0"/>
	<layer val="2"/>
	<labelMode val="1"/>
	<pointSize val="6"/>
	<pointStyle val="0"/>
</element>

<expression label="disc" exp="b^2 - 4*a*c" type="numeric"/>
<element type="numeric" label="disc">
	<show object="false" label="false" ev="4"/>
	<objColor r="0" g="0" b="0" alpha="0.0"/>
	<layer val="0"/>
	<labelMode val="0"/>
</element>
```

## 常见坑

1. **函数表达式的 `f(x) = ` 前缀必须有**；`type="function"`。漏了前缀会被当隐式曲线。
2. 函数求值器子集外（`Root/Extremum/Derivative`）→ 缓存留空靠重算；`Derivative(f)` 的输出是**函数对象**（out 也是 function type element）。
3. 参数滑杆范围过窄 → 观众看不到「开口翻转」的关键现象；范围设计是本题型的主要设计工作（对照 design.md 滑杆清单）。
4. `a` 滑杆变 0 → 二次变一次，顶点公式除零 → 用 `If(a==0, 占位, 顶点公式)` 或把 a 范围设为不含 0（±）两段：简单做法范围 [0.1,3]∪[-3,-0.1] 分两个滑杆，或在公式里 `If[a==0, (0,0), ...]`。
5. 动态文本放太多 → 遮挡图像；放到画布角落（absoluteScreenLocation），字号 16~20，文本行数 ≤4。
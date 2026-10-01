# locus-trace —— 轨迹三件套：Locus / CurveCartesian / trace

三条出轨迹的路线，按目标三选一。

- Locus（21 文件）：动点扫过的精确轨迹，随参数重算；NSolveODE 数值解的标准挂法 `Locus[数值解点, t]`。
- CurveCartesian（31 文件）：直接写参数式，适合波形族/解析曲线。
- trace（46+ 元素）：过程痕迹，不产生几何对象；复位需 `SetTrace[P,false]` 再置 true。
- 决策：解析可写→CurveCartesian；有动点/数值解→Locus；要过程感→trace。禁止手画折线当轨迹。
- 详见：`construction-language.md` §4.14。

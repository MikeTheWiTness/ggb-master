# vector-field-grid —— 矢量场点阵（Sequence 生成场线）

电场/磁场的标准呈现（箭头长度由场强公式决定）。

- 什么时候用：需要"大小+方向"（箭头随场强变化）的场分布；与 Slopefield 互补。
- 母本（四式，源于《用序列做电场线的方法》）：`Sequence[Vector[(i,j),(i,j)+k*E(i,j)], i, x0, x1, 1]` 嵌套生成点阵；`Flatten` 展平备用。
- 要点：网格 ≤21×21；k 为显示缩放（场强归一化后再乘）；场线长度必须由场强公式给出，禁止固定长示意线。
- 详见：`construction-language.md` §4.15；`design-rules.md` §0。

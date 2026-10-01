# nsolveode —— NSolveODE 数值解骨架（内置命令，许可范围）

三体/拉格朗日点/变加速/双杆等"解析式写不出"系统的标准做法：用 GeoGebra 内置求解器直接出轨迹。

- 什么时候用：解析解写不出、但规律由 ODE 决定（双摆、三体、拉格朗日点、变功率启动）。
- 母本（18 文件 25 处）：`NSolveODE[{θ', ω'}, 0, {θ0, ω0}, 8]` → numericalIntegral1/2，再接 `Locus[动点, t]` 出轨迹。
- ⚠ **输出形态随版本**（2026-08 REVIEW 修正）：老版本输出 `numericalIntegral1/2`（再接 Locus）；
  新版本（线框入磁样张实测）**直接输出 locus**，见 construction-language §4.14E。两形态下
  `Point[<输出>, 1]` 取终点（参数归一化 [0,1]）一律可用；新文件按 §4.14E 写法。
- 要点：a0 导数列表、a1 起始时间 0、a2 初值、a3 终止时间；状态向量写原生物理量（弧度制）；**禁止**手写积分递推（JS/Sequence 循环）。
- 详见：`construction-language.md` §5.3 / §4.14。

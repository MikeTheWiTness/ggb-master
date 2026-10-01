# 脚本优先 GeoGebra 命令语法，JavaScript 仅兜底

ADR-0002 确立了全交互含 JS 的范围，本条进一步规定优先级：按钮点击脚本、对象更新脚本等一切脚本逻辑，**先用 GeoGebra 自带命令语法**（SetValue / SetCoords / StartAnimation / If / Sequence 等）实现；只有当 ggb 语法表达不了（复杂循环、数据结构、精细事件控制）时才使用 `geogebra_javascript.js`。原因：ggb 脚本与构造同生命周期、在 Classic/网页端行为一致、可读性对教师用户友好；JS 调试难、端间差异大，是最贵的一层。

**Consequences**：interactivity.md 必须给出 ggb 脚本命令词汇表和"何时升级 JS"的判定清单；ggb_check 对 JS 只做语法检查，对 ggb 脚本做命令存在性与引用一致性检查。

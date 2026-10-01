# 全交互，包含 JavaScript 全局脚本

交互件范围定为全量：滑杆、动画、动态文本、复选框、按钮、InputBox，以及 `geogebra_javascript.js` + GeoGebra JS API。当时推荐的保守方案（不含 JS）被放弃，因为用户明确需要复杂交互逻辑的表达能力。

**Consequences**：references 必须覆盖 JS API（`ggbApplet.evalCommand`、`registerObjectUpdateListener` 等），ggb_check 增加 JS 语法检查层（`node --check`）；JS 的调试成本和安全面由校验层和题型手册的"常见坑"来对冲。

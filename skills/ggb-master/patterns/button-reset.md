# button-reset —— 复位按钮

把时间/参数/布尔全部清回初始值。

- 什么时候用：每份课件标配（与播放/暂停配对）。
- 母本：`t=0`（30 处）、`t=0 StartAnimation[t,false] ZoomIn[1]`（15 处）、批量 `SetValue(...)` 逐项（28 处）。
- 要点：先置零后停动画；对照 design.md 滑杆清单逐一复位（含布尔）；参数多时 RunClickScript 串联或 Execute 批量。
- 详见：`interactivity.md` §3.1。

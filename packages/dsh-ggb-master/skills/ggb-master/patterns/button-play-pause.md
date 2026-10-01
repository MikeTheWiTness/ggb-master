# button-play-pause —— 播放/暂停按钮

观众层最常用的交互件：一次点击同时切换动画与按钮文字。

- 什么时候用：任何带动画滑杆的课件；默认"打开不播、一点即播"。
- 母本：候选库 685 个按钮聚类，全形态与完整 XML 见 interactivity.md §3（含预定义隐藏布尔、两态 caption 的 3 种写法）。
- 要点：布尔先定义再翻转；SetCaption 用取反后的值；caption 初值与布尔初值一致。
- 详见：`interactivity.md` §3 / §3.1。

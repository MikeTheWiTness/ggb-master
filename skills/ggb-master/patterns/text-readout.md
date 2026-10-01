# text-readout —— 动态读数文本

把实时数值拼成画布文字。

- 什么时候用：需要读数/结论实时显示的课件（能量、速度、扫过面积…）。
- 母本：`<expression exp='"r=" + r + " 扫过面积=" + swept' type="text"/>` + element（isLaTeX=false + absoluteScreenLocation）。
- 要点：内容由 expression 决定（caption 只是代数区说明）；纯文本优先，公式大标题再 LaTeX；条件显示用 condition showObject。
- 详见：`construction-language.md` §4.10。

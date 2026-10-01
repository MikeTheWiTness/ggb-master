# image-element —— image 素材元素

符号/背景类的图片元素（科学对象禁止用图片冒充）。

- 什么时候用：元件装饰（坐标纸、题目截图）与宏之外的图片拼装；物理对象一律数学对象。
- 母本（电磁振荡样例）：`<element type="image" label="pic1"><file name="hash/xx.png"/><inBackground val="false"/><startPoint number="0" exp="G"/>…`。
- 要点：`<file name>` 是 zip 内路径=引用路径；素材放项目 media/<路径>；pack 按引用收图、缺失拒绝；未引用图片自动不带出。
- 详见：`construction-language.md` §4.12；工具库 `../macros/README.md`。

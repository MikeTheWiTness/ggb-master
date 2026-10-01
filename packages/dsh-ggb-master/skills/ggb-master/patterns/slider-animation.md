# slider-animation —— 滑杆 + 动画参数组

每份课件的基本构件：时间轴一根、物理量各一根。

- 什么时候用：所有模拟课件；时间轴固定命名 t。
- 母本（双星老样张，type=0 递增重来——新课件按下面要点改）：`<slider min="0.1" max="2" absoluteScreenLocation="true" width="200" x="42" y="39" fixed="false" horizontal="true" showAlgebra="true"/>` + `<animation step="0.1" speed="1" type="0" playing="false"/>`。
- 要点：主时钟 type=1（振荡）或过程演示 type=3（播完自停，interactivity §2.1）+ playing=false（打开不播）；物理量滑杆不与动画关联；布局横向一行、像素定位。
- 详见：`construction-language.md` §4.1；`interactivity.md` §2。

# button-toggle —— 显隐开关（按钮/复选框）

切换一组对象的可见性，文字随状态联动。

- 什么时候用：分层教学时（先基础知识层再进阶层）、多场景切换。
- 母本（28+17 处）：`SetValue(show1,!show1) If(show1,SetCaption(b1,"显示…"),SetCaption(b1,"隐藏…"))`。
- 要点：单对象用 `<condition showObject="show1"/>`（零脚本）；多对象/多视图用 onUpdate + SetVisibleInView 或 ShowLayer/HideLayer；布尔初值=画面初态。
- 详见：`interactivity.md` §3.1 / §4；`construction-language.md` §4.3。

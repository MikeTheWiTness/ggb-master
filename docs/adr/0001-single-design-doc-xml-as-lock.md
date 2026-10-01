# 单文档 design.md，geogebra.xml 即锁定

仿照对象 ppt-master 的招牌是 design_spec + spec_lock 双工件，但 ggb-master 只落盘一份 design.md（探究目标/参数/动画/布局/文字），不写 spec_lock。原因：ppt 需要 lock 是因为 SVG 只是中间语言、执行期要点散落在导出管线里；而 geogebra.xml 本身就是精确、可执行、可被 ggb_check 校验的最终构造，再锁一层只会制造两个需要保持同步的真相源。

**Consequences**：跨会话续做和 Modify 路线以 design.md + XML 本身为据；若未来出现"XML 无法表达的执行期决策"，再考虑重新引入锁定工件。

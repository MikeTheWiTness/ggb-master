# 宿主探针（真实 DSH 会话验收）

自动测试只锁定「随包产物彼此一致、且是 DSH 能读的形态」，不验证宿主运行行为。
以下步骤必须在真实 DSH 会话里执行一次并留痕（宿主版本、会话工作区、退出码、完整
stdout/stderr、产物路径、执行日期）。

1. **挂载**：安装 bundle，确认「插件」页列出 `dsh-ggb-master`、行 `preset-ggb-master` 激活。
   新开会话选 preset「GGB 课件」，确认会话 skill 目录里出现 `ggb-master`，加载它返回 SKILL.md 正文。
2. **工具与工作区**：打开独立工作区 A，调用原生工具
   `args: ["check", "<包目录>/skills/ggb-master/fixtures/kepler-baseline.xml", "--quiet"]`，
   确认 `exitCode: 0`、stdout 为 `OK`；再在独立工作区 B 重复一次。两次都不传 `cwd`，
   才能检验真实会话注入的工作区。
3. **路径约定**：在 A 里 `args: ["init", "__probe__"]`，确认骨架落在 `A/projects/__probe__/`
   （而不是宿主进程 cwd），随后 `args: ["check", "projects/__probe__/geogebra.xml"]` 通过，
   最后删除该目录。
4. **往返与打包**：用工作区里一份真实 `.ggb`（例如本机工作区的 `2025江苏高考真题.ggb`，
   或 `exports/` 下任一成品）验证 Modify 入口：
   `["unpack", "2025江苏高考真题.ggb", "-o", "projects/__probe__-modify/"]` →
   `["pack", "projects/__probe__-modify/", "-o", "exports/__probe__.ggb"]`，
   确认重打包后 `["check", "projects/__probe__-modify/geogebra.xml"]` 仍为 0 error。
5. **自检**：`args: ["selftest"]` 全绿（断言数应与脚本输出一致），确认临时目录已清理。
6. **摘除**：换回 `ptc` preset 新开会话，确认 skill 目录里没有 `ggb-master`、工具列表里没有 `ggb`；
   插件页停用 bundle 后再确认一次。这一步证明「可随时插拔」。
7. **失败面**：在没有工作区的会话里调用 `ggb` 应被拒；把 `command` 配成不存在的解释器路径应明确报错，
   不静默回退。

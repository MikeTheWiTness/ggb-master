# ADR-0006：DSH 插件包分发（skill + preset 一体挂载，2026-09-30）

## 状态

已接受（用户决策）。

## 决策

在仓库内新增自包含的 DSH 组合包 `packages/dsh-ggb-master/`，仿 `JiaoDuiAgentSkill`
的 `dsh-jiaodui` 形态，把 ggb-master 的「skill + 工作流」做成**可随时插拔**的插件包：

- `package.json` 声明 `dsh.bundle.patch = ./cordis.patch.yml`，同时是可挂载的插件入口；
- `cordis.patch.yml` 声明 agent preset「GGB 课件」（id `ggb-master`），preset 内：
  `skill-filesystem.customSkillDirs` 只挂本包 `skills/`，并挂 `./tools/index.js`
  注册原生工具 `ggb`（子命令 → 随包 Python 脚本，argv 透传）；
- `tools/index.js` 是薄壳：只做「子命令分发 + 受管子进程 + 结构化返回」，
  不含任何课件规划或构造判断；
- `skills/ggb-master/` 是开发源码的**随包副本**，使插件包复制到任何 profile 后自洽。

「插拔」语义：安装/启用 bundle 并在会话里选「GGB 课件」preset 即挂上；换回
`ptc` / `standard` preset 或停用 bundle 即摘掉，其它 preset 的会话完全不受影响。

## 理由

- skill 已是自包含分发单元（ADR-0005），但换主机仍要手动同步安装副本、并保证
  模型知道「先加载它」。bundle 让「安装即挂载」，把纪律变成机制。
- 原生工具走宿主平面 `ctx.subprocess`，不依赖 bash 沙箱；但它只是便捷入口——
  **脚本 CLI 永远是退路**，插件坏了 `python3 scripts/ggb_check.py` 照样能跑。
- 预设必须自带完整 plugins 列表（DSH 不提供继承），所以公共能力行与内置 `ptc`
  preset 保持同构，代价是公共能力变更时需要同步一次。

## 影响

- **副本从两份变三份**：开发源码 `skills/ggb-master/` → 随包副本
  `packages/dsh-ggb-master/skills/ggb-master/` 与安装副本 `~/.zcode/skills/ggb-master/` 等。
  `tools/sync_skill_copies.py` 的默认目标已含随包副本；`tests/test_dsh_plugin_package.py`
  逐文件比对源码与随包副本，漏同步会红。
- 安装/卸载只走 DSH 官方通道（插件页按本地路径安装，或 `plugin_manager install_bundle`），
  不手改 profile 的 `package.json` / `cordis.patch.yml`。
- 真实会话行为（skill 可见性、工具执行、工作区注入、插拔后消失）由
  `packages/dsh-ggb-master/host-probe/README.md` 的宿主探针验收；自动测试不替代它。

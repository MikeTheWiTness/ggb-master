# dsh-ggb-master

把 ggb-master 的 **GeoGebra 交互式模拟课件（.ggb）生产流程**接入 DSH profile 的
**自包含组合包（bundle）**：挂载随包的 ggb-master skill、注册一个 `ggb` 原生工具、
并声明一个「GGB 课件」agent preset——**工作流随时可插拔**。

本包只是「薄适配」：不含任何课件规划或构造判断，判断仍由宿主 agent 完成，
确定性仍由随包 Python 脚本完成。**脚本 CLI 永远是退路**——插件坏了，bash 里照样能跑。

## 结构

    packages/dsh-ggb-master/
      package.json           dsh.bundle.patch = ./cordis.patch.yml；同时是可挂载的插件入口
      cordis.patch.yml       自带组合包：插入 preset-ggb-master（含 skill 挂载 + 原生工具行）
      tools/index.js         宿主半侧插件：注册 ggb 原生工具（子命令 → 随包脚本）
      skills/ggb-master/     随包 skill（仓库 skills/ggb-master 的副本，sync 脚本与契约测试守一致性）
        scripts/             确定性工具链：project_manager / ggb_check / ggb_pack / ggb_unpack /
                             ggb_macro_preview / html_demo_check / selftest
        fixtures/            随包基准样例（开普勒、线框入磁 v-t），可作零素材冒烟输入
      locale/{zh,en}.json    插件管理页的标题与描述
      icon.svg               插件卡片图标
      host-probe/README.md   真实 DSH 会话的宿主验收步骤（自动测试不替代）
      README.md

## 它做了什么

- **agent preset「GGB 课件」（id `ggb-master`）**：自带完整 plugins 列表（与内置 `ptc` preset
  同构，含 bash / fs / subagent / todo / web / present / goal / plan / compaction），外加：
  - `skill-filesystem` 的 `customSkillDirs` 指向本包 `skills/`，所以 ggb-master skill
    只在这个 preset 的会话里可见（DSH 的 skill 发现按 preset 分层）；
  - `./tools/index.js` 注册原生工具 `ggb`。
- **原生工具 `ggb`**：`args[0]` 是子命令，其余参数原样透传，返回
  `exitCode / stdout / stderr / truncated`。它走宿主平面的 `ctx.subprocess`（子进程服务会清洗
  环境变量），不是 bash；每次调用把会话工作区同时设为 cwd 与 `GGB_ROOT`。

  | 子命令 | 随包脚本 | 典型调用 |
  | --- | --- | --- |
  | `init` | `project_manager.py init` | `["init", "单摆运动探究"]` |
  | `check` | `ggb_check.py` | `["check", "projects/单摆运动探究/geogebra.xml", "--fix"]` |
  | `pack` | `ggb_pack.py` | `["pack", "projects/单摆运动探究/", "-o", "exports/单摆运动探究.ggb"]` |
  | `unpack` | `ggb_unpack.py` | `["unpack", "exports/单摆运动探究.ggb", "-o", "projects/单摆运动探究-modify/"]` |
  | `macro-preview` | `ggb_macro_preview.py` | `["macro-preview", "skills/ggb-master/macros/", "--json"]` |
  | `html-demo-check` | `html_demo_check.py` | `["html-demo-check", "exports/demo.html"]` |
  | `selftest` | `selftest.py` | `["selftest"]` |

  退路：`args[0]` 也可以直接写随包脚本文件名（如 `ggb_check.py`）；再退一步，bash 直接
  `python3 <skill 目录>/scripts/ggb_check.py …` 与本工具等价。

## 安装

前置只有 **Python 3.10+ 的 `python3` 在 PATH 上**（脚本只用标准库，无 pip 依赖、无虚拟环境要求）。

- **图形界面**：侧栏「插件」页 → 按**本地路径**安装下面的包目录：
  `<仓库根>/packages/dsh-ggb-master`
- **creator 模式会话**：`plugin_manager`，`action: install_bundle`，
  `target` = 该包目录的绝对路径。

安装会把本包登记进 profile 的 `dsh.profile.bundles` 与 `dependencies`。
新增 bundle 可能经 HMR 立即生效；**替换已安装的包需要重启**才能加载新的 JS 模块代际。

## 插拔语义

| 想要的效果 | 操作 |
| --- | --- |
| 挂上工作流 | 安装 bundle，并在会话里选 preset「GGB 课件」（或设成默认 preset） |
| 临时摘掉 | 该会话换回 `ptc` / `standard` preset——公共能力不变，只是没有 ggb skill 挂载与 `ggb` 工具 |
| 彻底摘掉 | 插件页停用或移除 `dsh-ggb-master` bundle；profile 恢复原样 |

skill 挂载与原生工具都只挂在 preset 内，所以「插拔」不会污染其它 preset 的会话。

## 启用与验证

1. 安装后确认 bundle 在「插件」页列出、行 `preset-ggb-master` 激活。
2. **新开**一个会话（或把默认 preset 换成「GGB 课件」），确认会话的 skill 目录里出现 `ggb-master`。
3. 零素材冒烟——用随包基准样例跑质量门，应 `exitCode: 0` 且 stdout 为 `OK`：

       ggb  args: ["check", "<包目录>/skills/ggb-master/fixtures/kepler-baseline.xml", "--quiet"]

4. 完整工具链冒烟：`args: ["selftest"]`（会在当前工作区临时建 `projects/__selftest__/` 再清理，
   并跑样例/语料库/回填/往返/变异/JS/顺序/宏/预览断言）。
5. 真实宿主验收步骤见 `host-probe/README.md`。

> 同名 skill 提醒：本机可能同时存在 `~/.zcode/skills/ggb-master/` 等安装副本。
> 本 preset 只挂随包副本；若 harness 对同名 skill 报冲突，先停用/移除全局副本再启用本 preset。

## 配置（profile patch 按行 id 覆盖）

    - id: ggb-tools
      name: dsh-ggb-master
      config:
        command: /绝对路径/python3     # 省略时按 PATH 依次探测 python3、python
        timeoutMs: 300000
        maxOutputBytes: 65536

每次调用从会话读取工作区 W，同时设置 cwd 与 `GGB_ROOT`；并注入 `PYTHONDONTWRITEBYTECODE=1`，
避免在随包目录里留下 `__pycache__`。会话缺少工作区时拒绝执行。
产物路径沿用 skill 约定：`W/projects/<课件名>/`、`W/exports/<课件名>.ggb`。

## skill 三副本同步纪律

`skills/ggb-master/` 是开发源码；本包 `packages/dsh-ggb-master/skills/ggb-master/` 是随包副本
（ADR-0005 的自包含分发单元），`~/.zcode/skills/ggb-master/` 等是安装副本。
默认目标已含随包副本，改完源码一次同步：

```bash
python3 tools/sync_skill_copies.py
diff -rq skills/ggb-master packages/dsh-ggb-master/skills/ggb-master   # 仅 __pycache__ 差异为完成标准
```

契约测试 `tests/test_dsh_plugin_package.py` 会逐文件比对随包副本与源码，防止漏同步。

## 已知限制

- preset 的 plugins 列表是内置 `ptc` preset 的副本：DSH 的 preset 不提供继承，
  公共能力行变更时需要同步。这是「薄适配」当前最脆的一处。
- 原生工具**不是** bash 沙箱的替代：它只调用随包受信任脚本，不应对它传任意 shell。
- 无官方无头渲染器：视觉正确性仍靠「结构/数值校验 + 用户打开确认」，插件不改变这一点。

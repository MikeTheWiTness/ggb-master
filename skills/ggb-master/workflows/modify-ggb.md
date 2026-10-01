# modify-ggb —— Modify 补丁路线

> 读入已有 .ggb → 解包 → 理解构造 → 一句话确认改动点 → 补丁 XML → 校验 → 重打包。
> **不重生成整个构造**——补丁式修改是本路线的存在理由。

## 0. 流程总览

```
1 读入 .ggb
2 🛠 ggb_unpack.py 解包到工作目录
3 理解现有构造（读 XML + 对照 design.md 若在）
4 ⛔ 一句话确认改动点
5 补丁 XML（最小 diff）
6 🛠 ggb_check.py 五层校验（+ --fix 刷缓存）
7 🛠 ggb_pack.py 重打包 → exports/
```

> 路径中的 `~/.zcode/skills/ggb-master/` 是安装副本约定位置；其它主机/工具链以实际安装路径为准。

## 1. 解包（🛠）

```bash
python3 ~/.zcode/skills/ggb-master/scripts/ggb_unpack.py <文件.ggb> -o projects/<课件名>-modify/
```

解出的 `geogebra.xml` 可能来自任何来源（GeoGebra 桌面版导出、别的工具、旧版本）。
解包会保留图片子目录（哈希目录可还原）并把 `geogebra_macro.xml` 一并解出——
带图/带宏的成品修改后能原样回包。
先跑一次 `ggb_check.py` 建立基线：

- **基线全绿**：后续补丁的报错都归因于本次改动。
- **基线有错**：错误是原文件的，先向用户说明；修不修由用户定（默认只修阻碍本次改动的那部分）。
  已知合法来源：含 `NSolveODE` 的文件会带「内置数值 ODE」note（许可范围），不算错。

## 2. 理解现有构造

按依赖序读 `<construction>`，回答四个问题（写到回复里，供确认用）：

1. 有哪些滑杆/交互件？主时钟是谁？
2. 核心派生链是什么（哪些 expression 串起来）？
3. 用户要改的东西落在哪几个对象上？
4. 改动会不会波及其它对象（缓存值、布局、脚本引用）？

若项目目录里有 design.md，对照它理解原意图；没有就纯靠 XML。

## 3. ⛔ 一句话确认

把改动点压缩成一句：「我会把 X 的 Y 从 A 改成 B，涉及 N 个对象」。用户点头再动手。
（Modify 天然轻量：不做 design.md 重写，除非改动量大到接近重建——那转 Generate。）

## 4. 补丁纪律

1. **最小 diff**：只改必须改的对象/属性；不要顺手重排、重命名、重新缩进整个文件。
2. **改了 exp 必须刷缓存**：相关 `<value>/<coords>` 要么同步手算，要么删掉让 `ggb_check.py --fix` 填。
3. **新增对象**：遵守拓扑序（插在被引用者之后）；新 label 全局唯一；形态照金标准 §4。
4. **改布局**：交互件定位属性别混（金标准 §10 坑7）；文本挪动注意别遮挡。
5. **改脚本**：ggbscript 转义规则不变（`&quot;`、`&#xd;&#xa;`）；改完跑 L5。
6. **补/加宏**：新增标准元件（电路符号、地面等）时从 `macros/<类>/` 取 .ggt，
   把 `<macro>` 定义拼进目标 `geogebra_macro.xml`（去重 cmdName），调用名=工具名
   （construction-language §4.13）；check 自动把宏命令名加入白名单。
7. **⚠️ 工具重写警告**：`ggb_check.py --fix` 会用 ElementTree 重写整份 XML（规范化缩进、属性顺序保持）。
   对补丁场景这通常无害（GeoGebra 只认语义），但如果你在做逐字符 diff 或外部工具对接，
   先备份原文件。pack 前的 check 默认不带 --fix，不会动文件。

## 5. 校验与打包（🛠）

```bash
python3 ~/.zcode/skills/ggb-master/scripts/ggb_check.py projects/<课件名>-modify/geogebra.xml
python3 ~/.zcode/skills/ggb-master/scripts/ggb_check.py projects/<课件名>-modify/geogebra.xml --fix   # 需要时
python3 ~/.zcode/skills/ggb-master/scripts/ggb_pack.py projects/<课件名>-modify/ -o exports/<课件名>-<改动>.ggb
# 素材/宏随引用自动打包；未引用图片不带出
```

## 6. 收尾

报告：改了什么、校验结果、产物路径；提醒用户打开验证视觉效果。
若原文件有未修复的历史问题，列出来留给用户决定。
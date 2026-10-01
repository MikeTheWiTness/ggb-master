#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""project_manager.py —— init 项目骨架（Generate 路线第 2 步）。

用法:
    python3 project_manager.py init "<课件名>" [--force]

在工作区（环境变量 GGB_ROOT 指定，未指定则为当前工作目录 CWD）
下的 projects/<课件名>/ 建：
    design.md                 # 规划工件模板（Planner 填）
    geogebra.xml              # 最小 2D 骨架（Builder 填）
    geogebra_defaults2d.xml   # 权威默认样式（从 scripts/defaults/ 拷入）
    geogebra_defaults3d.xml   # 同上（3D 才需要，留着无害）
    geogebra_javascript.js    # 占位 function ggbOnInit() {}
    media/                    # 图片素材目录（<file name> 引用路径存放处）
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULTS_DIR = os.path.join(SCRIPTS_DIR, "defaults")


def find_workspace():
    """工作区定位：GGB_ROOT 环境变量 > 当前工作目录。projects/ 与 exports/ 都相对工作区。"""
    env = os.environ.get("GGB_ROOT")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    return os.path.abspath(os.getcwd())


WORKSPACE = find_workspace()
PROJECTS_DIR = os.path.join(WORKSPACE, "projects")

XML_SKELETON = '''<?xml version="1.0" encoding="utf-8"?>
<geogebra format="5.0" version="5.2.871.0" app="classic" platform="d" xsi:noNamespaceSchemaLocation="http://www.geogebra.org/apps/xsd/ggb.xsd" xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<gui>
	<window width="1200" height="800" />
	<perspectives>
<perspective id="tmp">
	<panes><pane location="" divider="0.8" orientation="1" /></panes>
	<views><view id="1" visible="true" inframe="false" stylebar="true" location="3" size="1200" window="100,100,600,400" /></views>
	<toolbar show="true" items="0 73 62 | 1 501 67 , 5 19 , 72 75 76 | 2 15 45 , 18 65 , 7 37 | 4 3 8 9 , 13 44 , 58 , 47 | 16 51 64 , 70 | 10 34 53 11 , 24  20 22 , 21 23 | 55 56 57 , 12 | 36 46 , 38 49  50 , 71  14  68 | 30 29 54 32 31 33 | 25 17 26 60 52 61 | 40 41 42 , 27 28 35 , 6" position="1" help="false" />
	<input show="true" cmd="true" top="algebra" />
	<dockBar show="false" east="false" />
</perspective>
	</perspectives>
	<labelingStyle  val="1"/>
	<font  size="18"/>
</gui>
<euclidianView>
	<viewNumber viewNo="1"/>
	<size  width="1200" height="700"/>
	<coordSystem xZero="560" yZero="380" scale="40" yscale="40"/>
	<evSettings axes="true" grid="false" gridIsBold="false" pointCapturing="3" rightAngleStyle="1" checkboxSize="26" gridType="3"/>
	<bgColor r="255" g="255" b="255"/>
	<axesColor r="37" g="37" b="37"/>
	<gridColor r="192" g="192" b="192"/>
	<lineStyle axes="1" grid="0"/>
	<axis id="0" show="true" label="" unitLabel="" tickStyle="1" showNumbers="true"/>
	<axis id="1" show="true" label="" unitLabel="" tickStyle="1" showNumbers="true"/>
</euclidianView>
<algebraView><mode val="1"/></algebraView>
<kernel>
	<continuous val="false"/>
	<usePathAndRegionParameters val="true"/>
	<decimals val="5"/>
	<angleUnit val="degree"/>
	<algebraStyle val="0" spreadsheet="0"/>
	<coordStyle val="0"/>
</kernel>
<tableview min="-2.0" max="2.0" step="1.0"/>
<scripting blocked="false" disabled="false"/>
<construction title="{title}" author="" date="">
</construction>
</geogebra>
'''

DESIGN_TEMPLATE = '''# 《{title}》 模拟课件设计

> 本文件是 Generate 路线的唯一规划工件。写满以下小节后交用户确认；
> 确认后 Builder 依据它写 geogebra.xml。术语与设计原则见 skill 的 references/（design-rules、planner）。

## 复杂度分级

低 / 中 / 高 （任一项命中即「高」→ 强制三步分步构建，见 planner.md §2 与 generate-ggb.md §5.1：
派生链≥10 个、含事件/拓扑/临界态、闭式公式含反函数选支）

## 探究目标

（一段话：观众拖什么滑杆 / 按什么按钮 / 看到什么变化 / 得出什么结论。
  默认开箱可演，不需要观众理解全部滑杆。）

## 模型层自检（物理公式由模型自推，此处只立自检手段——skill 不教公式推导）

- 状态时间函数（分段闭式）在此留一行总览即可，公式推导过程不留档。
- 守恒/初值对拍：守恒量写两条独立链（如 `pTotal=m1*v10+m2*v20` 与 `pNow=m1*u1+m2*u2`），
  t=0 时两者相等即初值编码正确（ggb_check 数值层自动校验）。
- 对拍独立性：两条链必须**独立推导**——共享同一错误假设时误差会被掩盖（环形磁场返工：位错被掩 2 m）。
- 分段边界连续：事件切换时刻两段速度/位移同值，If 段界用 `<=` 对齐。
- 量纲与量级：代入典型参数手算 1~2 个数，与物理直觉对照（如板块模型 v_C≈1.6 m/s 量级）。
- 数值对拍（可选）：同公式用 Python 独立复算，与 GeoGebra 缓存比对容差 <1e-9。

## 参数滑杆清单（教师层：一个物理量一个滑杆，不写死在公式里）

| 滑杆 label | 含义（caption） | 范围 min~max | 初值 | 步长 | 动画(step/speed/type/playing) |
|---|---|---|---|---|---|
| `t` | 主时钟 |  |  |  |  |
|  |  |  |  |  |  |

## 模型有效域（design-rules.md §1/§2：先写成立条件，再推滑杆范围）

- 解析解成立条件：（例：弹簧长 ℓ(t)=L₀+x(t) ≥ margin，不允许负值/互穿）
- 最坏参数组合推导：（例：A_max = |Δv|max·√(μ_max/k_min) = … ≤ L₀−margin ✓）
- 由此确定的滑杆上下限已回填上表。

## 演示机制（观众层：一键播放/重置，读数自动更新）

- 主时钟：`t` 滑杆，`type="1"`（振荡），`playing="true"`。
- 按钮：播放/暂停、重置（ggbscript 命令），可选复选框切换可见对象。
- 动态读数：哪些数值要实时显示在画面文本里。

## 画面布局与文字

- 坐标系：`coordSystem xZero=560 yZero=380 scale=40`；内容范围（画布 1200×700）。
- 布局：滑杆列 / 按钮区 / 文本说明区（像素坐标）。
- 文字：标题、说明 caption、动态读数格式（中文）。

## 素材清单（图片 / 宏工具）

| 素材 | 用途（caption/位置） | 来源（media/ 文件名 或 macros/<工具名>.ggt） | 引用路径 |
|---|---|---|---|
| 例：地面 | 底部平台 | media/地面212.png | 哈希 目录/地面212.png |
| 例：定值电阻 | 电路元件 | macros/circuit/定值电阻.ggt | 宏命令 定值电阻[A,B] |
'''

JS_PLACEHOLDER = 'function ggbOnInit() {}\n'


def init_project(name: str, force: bool = False) -> int:
    name = name.strip().strip("/").strip("\\")
    if not name:
        print("错误：课件名为空", file=sys.stderr)
        return 2
    if name in (".", "..") or "/" in name or "\\" in name:
        print(f"错误：课件名不能含路径分隔符：{name}", file=sys.stderr)
        return 2

    proj = os.path.join(PROJECTS_DIR, name)
    if os.path.exists(proj) and not force:
        print(f"已存在：{proj}（用 --force 覆盖）", file=sys.stderr)
        return 1
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    if os.path.exists(proj) and force:
        shutil.rmtree(proj)
    os.makedirs(proj, exist_ok=True)

    # 骨架 xml
    with open(os.path.join(proj, "geogebra.xml"), "w", encoding="utf-8") as f:
        f.write(XML_SKELETON.format(title=name))
    # design.md 模板
    with open(os.path.join(proj, "design.md"), "w", encoding="utf-8") as f:
        f.write(DESIGN_TEMPLATE.format(title=name))
    # 默认样式
    for d in ("geogebra_defaults2d.xml", "geogebra_defaults3d.xml"):
        src = os.path.join(DEFAULTS_DIR, d)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(proj, d))
    # JS 占位
    with open(os.path.join(proj, "geogebra_javascript.js"), "w", encoding="utf-8") as f:
        f.write(JS_PLACEHOLDER)
    # 素材目录
    os.makedirs(os.path.join(proj, "media"), exist_ok=True)

    print(f"已初始化项目：{proj}")
    for f in sorted(os.listdir(proj)):
        print("  -", f)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="project_manager.py", description="ggb-master 项目骨架初始化")
    sub = ap.add_subparsers(dest="cmd", required=True)
    init = sub.add_parser("init", help="初始化项目")
    init.add_argument("name", help="课件名（中文/英文均可，不含路径分隔符）")
    init.add_argument("--force", action="store_true", help="覆盖已存在目录")
    args = ap.parse_args()

    if args.cmd == "init":
        return init_project(args.name, force=args.force)
    ap.error("未知子命令")
    return 2


if __name__ == "__main__":
    sys.exit(main())

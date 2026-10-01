#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ggb_macro_preview.py —— 宏素材（.ggt）一键预览：取用评估不求拆包。

用法：
  python3 ggb_macro_preview.py macros/mechanics/滑轮.ggt      # 单个宏
  python3 ggb_macro_preview.py macros/                         # 整个库（摘要表）
  python3 ggb_macro_preview.py macros/ --json                  # 机器可读

输出：cmdName/工具说明/输入输出/构造规模/随机点检测/取用建议。
配合 SKILL.md 第 0 条「取用成本预算」：任何宏先预览定夺，禁止未经预览直接拆包细读。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from ggb_check import audit_macro_self_containment  # 自包含审计（单一事实源）
except ImportError:
    audit_macro_self_containment = None

# 构造规模阈值：低于此命令数，手绘通常更省（取用建议用）
HANDDRAW_CMDS = 4


def scan_ggt(path: str):
    """返回 (.ggt 信息 dict) 或 (错误字符串)。"""
    try:
        z = zipfile.ZipFile(path)
    except (zipfile.BadZipFile, OSError) as e:
        return None, f"错误：不是有效的 .ggt（{e}）"
    entry_names = set(z.namelist())
    if "geogebra_macro.xml" not in entry_names:
        return None, "错误：.ggt 内缺 geogebra_macro.xml"

    try:
        raw_xml = z.read("geogebra_macro.xml").decode("utf-8", "ignore")
    except ET.ParseError as e:
        return None, f"错误：宏 XML 解析失败（{e}）"

    try:
        root = ET.fromstring(raw_xml)
    except ET.ParseError as e:
        return None, f"错误：宏 XML 解析失败（{e}）"

    m = root if root.tag == "macro" else root.find("macro")
    if m is None:
        return None, "错误：找不到 <macro> 定义"

    cmd_name = m.get("cmdName", "")
    tool_help = m.get("toolHelp", "") or m.get("toolName", "")
    icon = m.get("iconFile", "")

    def attrs_of(tag, prefix="a"):
        el = m.find(tag)
        if el is None:
            return []
        return [el.get(f"{prefix}{i}") for i in range(20) if el.get(f"{prefix}{i}")]

    inputs = attrs_of("macroInput")
    outputs = attrs_of("macroOutput")

    cons = m.find("construction")
    n_cmd = 0
    n_elem = 0
    cmd_hist = {}
    elem_types = {}
    point_in = 0
    labels = []
    if cons is not None:
        for child in cons:
            if child.tag == "command":
                n_cmd += 1
                cmd_hist[child.get("name", "")] = cmd_hist.get(child.get("name", ""), 0) + 1
                if child.get("name", "") == "PointIn":
                    point_in += 1
            elif child.tag == "element":
                n_elem += 1
                t = child.get("type", "")
                elem_types[t] = elem_types.get(t, 0) + 1
                labels.append(child.get("label", ""))
            elif child.tag == "expression":
                n_elem += 1

    icons = [n for n in entry_names if n.lower().endswith((".png", ".jpg", ".jpeg"))]

    # 视图依附：Corner[n] 引用（全局合法、非残缺，但尺寸/定位随打开时的视图而定）
    corner_refs = len(re.findall(r"Corner\s*[\[(]", raw_xml))

    # 自包含审计：悬挂引用=引用未定义对象（脱离源场景即残缺），空 label=精炼残缺
    dangling, empty = [], []
    if audit_macro_self_containment is not None:
        _defined, dangling, empty = audit_macro_self_containment(root)

    # 输入标签的撇号形态（改名前缀要处理 T'）
    quoted = sorted({lb for lb in labels if "'" in lb})[:5]

    # 直抄片段是否已就绪（macros/snippets/<类>/<工具名>.md）
    snippet = ""
    if cmd_name:
        snip_candidates = [os.path.join("macros", "snippets", cat, cmd_name + ".md")
                           for cat in ("circuit", "mechanics", "misc", "field")]
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for rel in snip_candidates:
            if os.path.exists(os.path.join(base, rel)):
                snippet = rel
                break

    info = {
        "file": os.path.basename(path),
        "cmdName": cmd_name,
        "toolHelp": tool_help,
        "inputs": inputs,
        "outputs": outputs,
        "commands": n_cmd,
        "elements": n_elem,
        "top_commands": sorted(cmd_hist.items(), key=lambda kv: -kv[1])[:8],
        "point_in": point_in,
        "corner_refs": corner_refs,
        "icons": icons,
        "labels_with_apostrophe": quoted,
        "dangling": dangling,
        "empty_labels": empty,
        "snippet": snippet,
    }
    return info, None


def verdict(info: dict) -> str:
    """取用建议：手绘 / 直抄片段 / 用宏。残缺宏优先警示。"""
    if info.get("dangling") or info.get("empty_labels"):
        if info.get("dangling"):
            return (f"⚠ 残缺宏：悬挂引用 {', '.join(info['dangling'][:4])}"
                    "（引用源场景全局对象，脱离场景即失效，导入 GeoGebra 同样失败）")
        return "⚠ 残缺宏：存在空 label 元素（精炼提取残缺构造）"
    if info.get("snippet"):
        return f"直抄片段已就绪：{info['snippet']}（1 次读取即用）"
    n = info["commands"]
    if n <= HANDDRAW_CMDS and not info["point_in"]:
        return "手绘更省（命令数 ≤%d）" % HANDDRAW_CMDS
    if info["point_in"]:
        return "无直抄片段；用宏需注意 PointIn 随机点（直抄需先去随机化）"
    return "无直抄片段；可按需调用 .ggt"


def preview_file(path: str) -> tuple:
    info, err = scan_ggt(path)
    if err:
        return None, err
    return info, None


def render_one(info: dict) -> str:
    lines = [
        f"工具名：{info['cmdName']}  （{info['toolHelp'] or '无说明'}）",
        f"输入 {len(info['inputs'])} 个 → 输出 {len(info['outputs'])} 个",
        f"  输入：{', '.join(info['inputs']) or '—'}",
        f"  输出：{', '.join(info['outputs']) or '—'}",
        f"构造：{info['commands']} 条命令 / {info['elements']} 个元素",
        f"  高频命令：{', '.join(f'{k}×{v}' for k, v in info['top_commands'])}",
        f"随机点：{'⚠ ' + str(info['point_in']) + ' 处 PointIn（每次导入外观不同，直抄需去随机）'
                 if info['point_in'] else '无'}",
        *( [f"视图依附：Corner 引用 {info['corner_refs']} 处（尺寸/定位随打开时的视图而定）"]
           if info.get("corner_refs") else [] ),
        f"图标：{', '.join(info['icons']) or '无'}（仅工具栏图标，非构造素材）",
        f"撇号标签：{', '.join(info['labels_with_apostrophe']) or '无'}（改名前缀时注意）",
        f"自包含：{'✗ 悬挂引用 ' + ', '.join(info['dangling'][:6]) if info['dangling'] else ('✗ 空 label' if info['empty_labels'] else '✓（可独立直抄）')}",
        f"建议：{verdict(info)}",
    ]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ggb_macro_preview.py",
                                 description="ggb-master 宏素材一键预览（取用评估不求拆包）")
    ap.add_argument("target", help="单个 .ggt 文件或宏库目录（macros/）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if os.path.isdir(args.target):
        ggt_files = sorted(
            os.path.join(dp, f) for dp, _dn, fn in os.walk(args.target)
            for f in fn if f.endswith(".ggt"))
        if not ggt_files:
            print(f"错误：目录里没有 .ggt：{args.target}", file=sys.stderr)
            return 2
        if args.json:
            out = []
            for p in ggt_files:
                info, err = preview_file(p)
                out.append({"path": p, **info} if info else {"path": p, "error": err})
            print(json.dumps(out, ensure_ascii=False, indent=2))
            return 0
        print(f"{'工具名':<12}{'命令':>4}{'入':>3}{'出':>3}  建议")
        print("-" * 52)
        n_err = 0
        for p in ggt_files:
            info, err = preview_file(p)
            if err:
                print(f"{os.path.basename(p):<12}  {err}")
                n_err += 1
                continue
            print(f"{info['cmdName']:<12}{info['commands']:>4}{len(info['inputs']):>3}"
                  f"{len(info['outputs']):>3}  {verdict(info)}"
                  + ("  ⚠随机" if info["point_in"] else ""))
        print(f"\n共 {len(ggt_files)} 个宏，{n_err} 个读取失败。"
              "预览单宏详情：python3 ggb_macro_preview.py <文件.ggt>")
        return 1 if n_err else 0

    if not os.path.exists(args.target):
        print(f"错误：文件不存在 {args.target}", file=sys.stderr)
        return 2
    info, err = preview_file(args.target)
    if err:
        print(err, file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0
    print(render_one(info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
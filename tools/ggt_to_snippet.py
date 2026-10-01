#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ggt_to_snippet.py —— 把宏素材（.ggt）转为「可直抄 XML 片段」markdown 并自证。

背景（SKILL.md 第 0 条）：素材取用成本预算 ≤1 次读取。.ggt 是黑盒 zip，agent 评估成本
5+ 次调用；转换为带前缀的直抄片段后，取用 = 1 次读取。本脚本是维护工具（repo 侧），
产物进 `skills/ggb-master/macros/snippets/<类>/<工具>.md`。

转换规则（实证自 macros/ 全库）：
- 去壳：删 <macro> 包裹与 iconFile（95 个宏的 PNG 全部只是工具栏图标，无构造图片）；
- 标签改名：构造成员全部加前缀（默认 sP_），防多个片段同文件冲突；输入引用同步改；
- 去随机：PointIn[圆] 是随机点（滑轮/传送带每次导入外观不同）→ Point[圆, 0.5] 确定性；
- 输入的数值参数（构造里无对应元素）在测试文件里自动补自由数值。

用法：
  python3 tools/ggt_to_snippet.py skills/ggb-master/macros/mechanics/滑轮.ggt
  python3 tools/ggt_to_snippet.py --prefix hl_ --out-dir /tmp/snippets <file.ggt>
  python3 tools/ggb_macro_preview.py <file.ggt> --json | 配合选型
"""
from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET

SKILL_SCRIPTS = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                 "skills", "ggb-master", "scripts"))
CHECK_PY = os.path.join(SKILL_SCRIPTS, "ggb_check.py")

SKELETON = """<?xml version="1.0" encoding="utf-8"?>
<geogebra format="5.0" version="5.2.871.0" app="classic" platform="d" xsi:noNamespaceSchemaLocation="http://www.geogebra.org/apps/xsd/ggb.xsd" xmlns="" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" >
<gui>
\t<window width="1200" height="800" />
\t<perspectives>
<perspective id="tmp">
\t<panes><pane location="" divider="0.8" orientation="1" /></panes>
\t<views><view id="1" visible="true" inframe="false" stylebar="true" location="3" size="1200" window="100,100,600,400" /></views>
</perspective>
\t</perspectives>
</gui>
<euclidianView>
\t<viewNumber viewNo="1"/>
\t<size width="1200" height="760"/>
\t<coordSystem xZero="560" yZero="380" scale="50" yscale="50"/>
\t<evSettings axes="true" grid="false" gridIsBold="false" pointCapturing="3" rightAngleStyle="1" checkboxSize="26" gridType="3"/>
\t<bgColor r="255" g="255" b="255"/>
</euclidianView>
<kernel>
\t<continuous val="false"/>
\t<usePathAndRegionParameters val="true"/>
\t<decimals val="5"/>
\t<angleUnit val="degree"/>
</kernel>
<tableview min="-2.0" max="2.0" step="1.0"/>
<scripting blocked="false" disabled="false"/>
<construction title="snippet-test">
CONSTRUCTION
</construction>
</geogebra>
"""


def load_macro(path: str):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read("geogebra_macro.xml"))
    m = root if root.tag == "macro" else root.find("macro")
    if m is None:
        raise ValueError("找不到 <macro> 定义")

    def attrs_of(tag, prefix="a"):
        el = m.find(tag)
        if el is None:
            return []
        return [el.get(f"{prefix}{i}") for i in range(20) if el.get(f"{prefix}{i}")]

    inputs = attrs_of("macroInput")
    outputs = attrs_of("macroOutput")
    cons = m.find("construction")
    children = list(cons) if cons is not None else []
    return {"cmd": m.get("cmdName", ""), "help": m.get("toolHelp", "") or m.get("toolName", ""),
            "inputs": inputs, "outputs": outputs, "children": children, "root": root}


# GeoGebra 保留名：表达式/输入值里的这些 token 一律不当作对象标签改名。
# 单一事实源 = ggb_check.py 的 KNOWN_COMMANDS/FUNCTION_SUBSET/CONSTANTS/FREE_VARS；
# 下面这份本地集合仅作 ggb_check 不可导入时的兜底。
sys.path.insert(0, SKILL_SCRIPTS)
try:
    import ggb_check as _gc  # noqa: E402
    _RESERVED = set(_gc.KNOWN_COMMANDS) | set(_gc.FUNCTION_SUBSET) \
        | set(_gc.CONSTANTS) | set(_gc.FREE_VARS)
except Exception:
    _RESERVED = {
        "abs", "acos", "asin", "atan", "atan2", "ceil", "cos", "deg", "div", "exp",
        "floor", "ln", "log", "max", "min", "mod", "round", "sign", "sin", "sqrt",
        "tan", "x", "y", "z", "u", "v", "w", "r", "θ", "pi", "π", "e", "true",
        "false", "infinity",
        "Angle", "Append", "Arc", "Circle", "CircleArc", "CircumcircleArc",
        "Cross", "Curve", "CurveCartesian", "Dilate", "Direction", "Distance",
        "Div", "Dot", "Element", "Flatten", "If", "Intersect", "Iteration",
        "IterationList", "Join", "Length", "LineBisector", "Midpoint",
        "Mirror", "OrthogonalLine", "Point", "PointIn", "Polygon", "Polyline",
        "Reflect", "RemoveUndefined", "Rotate", "Segment", "Semicircle",
        "Sequence", "Slope", "Sum", "Tangent", "Translate", "UnitVector",
        "UnitOrthogonalVector", "Vector", "Zip",
    }
_IDENT_RE = re.compile(r"[^\W\d][\w]*(?:\{[^\}]+\}[\w]*)*'?")
_STR_RE = re.compile(r'"[^"]*"')
_BOUND_CMD_RE = re.compile(
    r"(?:Sequence|Zip|IterationList|Iteration|Curve|CurveCartesian)\s*[\[\(]")
# Curva vs Sequence 的绑定变量位置（第 2/3 顶层参数）
_BOUND_POS = {"Sequence": 1, "Zip": 1, "IterationList": 1, "Iteration": 1,
              "Curve": 2, "CurveCartesian": 2}


def canon_tok(t: str) -> str:
    """GeoGebra 下标写法 A_{1} ≡ A_1（与 ggb_check 审计口径一致）。"""
    return re.sub(r"\{([^}]*)\}", r"\1", t) if "{" in t else t


def rename_attr_value(v: str, mapping) -> str:
    return mapping.get(v, v)


def build_map(defined, prefix):
    out = {}
    for lab in sorted(defined, key=len, reverse=True):
        out[lab] = prefix + lab
    return out


def rename_expr(s: str, mapping) -> str:
    """按字符串字面量切段后逐段替换标签 token——下标花括号模式({…})会跨字符串边界
    吞成伪 token，必须先切段（电流表样张 "…\\scalebox{" + (LaTeX[aa]) 实证坑）。"""
    if not mapping:
        return s
    spans = [(m.start(), m.end()) for m in _STR_RE.finditer(s)]
    segments = []
    pos = 0
    for a, b in spans:
        segments.append((pos, s[pos:a]))
        pos = b
    segments.append((pos, s[pos:]))
    out = []
    for start, seg in segments:
        idx = 0
        for m in _IDENT_RE.finditer(seg):
            key = canon_tok(m.group(0))
            if key in mapping:
                out.append(seg[idx:m.start()])
                out.append(mapping[key])
                idx = m.end()
        out.append(seg[idx:])
    return "".join(out)


def transform(children, mapping):
    out = []
    for c in children:
        c2 = ET.Element(c.tag)
        for k, v in c.attrib.items():
            if k == "label":
                c2.set(k, rename_attr_value(v, mapping))
            elif k == "exp":
                c2.set(k, rename_expr(v, mapping))
            else:
                c2.set(k, v)
        if c.tag == "command":
            name = c.get("name", "")
            for el in c:
                c2el = ET.SubElement(c2, el.tag)
                for k, v in el.attrib.items():
                    if el.tag in ("input", "output"):
                        c2el.set(k, rename_expr(v, mapping))
                    else:
                        c2el.set(k, v)
            # PointIn → Point[路径, 0.5] 去随机
            if name == "PointIn":
                c2.set("name", "Point")
                inp = c2.find("input")
                if inp is not None and inp.get("a1") is None:
                    inp.set("a1", "0.5")
        else:
            for el in c:
                c2.append(transform([el], mapping)[0])
        out.append(c2)
    return out


def indent_xml(elem, level=0):
    pad = "\t" * level
    if len(elem):
        for i, ch in enumerate(elem):
            indent_xml(ch, level + 1)
    return elem


def to_xml_text(children) -> str:
    lines = []
    for c in children:
        el = indent_xml(c)
        lines.append(ET.tostring(el, encoding="unicode"))
    return "\n".join(lines)


def make_test_xml(children, undefined_inputs) -> str:
    body = to_xml_text(children)
    if undefined_inputs:
        extras = "\n".join(
            f'<element type="numeric" label="{u}"><show object="true" label="true" ev="4"/>'
            f'<objColor r="0" g="0" b="0" alpha="0.0"/><layer val="0"/><labelMode val="1"/>'
            f'<value val="1"/></element>'
            for u in undefined_inputs)
        body = extras + "\n" + body
    return SKELETON.replace("CONSTRUCTION", body)


def verify_test(workdir: str, test_xml: str) -> tuple:
    os.makedirs(workdir, exist_ok=True)
    xml_path = os.path.join(workdir, "geogebra.xml")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(test_xml)
    r = subprocess.run([sys.executable, CHECK_PY, xml_path], capture_output=True, text=True)
    if r.returncode != 0:
        return False, r.stdout
    r2 = subprocess.run([sys.executable, CHECK_PY, xml_path, "--fix"], capture_output=True, text=True)
    if r2.returncode != 0:
        return False, r2.stdout
    return True, "0 error（check + fix 通过）"


def gen_snippet_md(info, children_text, prefix) -> str:
    return f"""# 直抄片段：{info['cmd']}（源：宏库 .ggt）

- 用途：{info['help']}
- 输入 {len(info['inputs'])} 个 → 输出 {len(info['outputs'])} 个（输出对象按需保留/隐藏）。
- 已知坑：原宏用 PointIn 随机点，每次导入外观不同；本片段已确定性化（Point[路径, 0.5]）。
- **多片段同用时**：把下面的 `{prefix}` 全局替换为你项目内的唯一前缀，防标签冲突。
- 输入对象：片段自带输入定义（label 带 `{prefix}` 前缀）；替换 label 时同步替换片段内引用。

## XML 片段（贴进 <construction> 末尾）

```xml
{children_text}
```

## 取用步骤

1. 把 XML 片段贴进目标 geogebra.xml 的 `</construction>` 之前。
2. 若与其它片段共用，先全局替换 `{prefix}` 为唯一前缀。
3. 跑 `ggb_check.py <项目>/geogebra.xml --fix` 填缓存；再 `ggb_pack.py` 打包。
"""


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ggt_to_snippet.py",
                                 description=".ggt 宏 → 直抄片段 markdown + 测试自证")
    ap.add_argument("ggt", help="宏文件路径")
    ap.add_argument("--prefix", default="sP_", help="标签前缀（默认 sP_）")
    ap.add_argument("--out-dir", default=None, help="片段输出目录（默认 macros/snippets/<检测类>/）")
    ap.add_argument("--skip-test", action="store_true", help="跳过 test .ggb 自证")
    args = ap.parse_args(argv)

    if not os.path.exists(args.ggt):
        print(f"错误：文件不存在 {args.ggt}", file=sys.stderr)
        return 2
    try:
        info = load_macro(args.ggt)
    except (zipfile.BadZipFile, OSError, ET.ParseError, ValueError) as e:
        print(f"错误：读取宏失败（{e}）", file=sys.stderr)
        return 2

    defined, dangling, empty = _gc.audit_macro_self_containment(info["root"])
    if empty:
        print(f"宏不可直抄：{len(empty)} 处空 label（{', '.join(empty[:5])}）——"
              "精炼提取的残缺构造，导入 GeoGebra 也会报错", file=sys.stderr)
        return 1
    if dangling:
        print(f"宏不可直抄：{len(dangling)} 个引用未定义（自包含审计失败）："
              f"{', '.join(dangling[:12])}——原始宏引用了所属场景的全局对象，"
              "脱离场景即残缺（refine 提取产物），导入 GeoGebra 同样失败", file=sys.stderr)
        return 1

    mapping = build_map(defined, args.prefix)
    new_children = transform(info["children"], mapping)
    xml_text = to_xml_text(new_children)

    if not args.skip_test:
        with tempfile.TemporaryDirectory(prefix="ggt_snippet_") as tmp:
            undefined_inputs = [u for u in info["inputs"] if u not in {
                c.get("label") for c in info["children"]
                if c.tag in ("element", "expression") and c.get("label")}]
            ok, msg = verify_test(tmp, make_test_xml(new_children, undefined_inputs))
        if not ok:
            print(f"自证失败：{msg}", file=sys.stderr)
            return 1
    else:
        msg = "已跳过自证"

    # 输出目录：默认 macros/snippets/<类>/；类名从路径推断（mechanics/circuit/...）
    if args.out_dir is None:
        rel = os.path.relpath(args.ggt, start=os.path.commonpath([args.ggt]))
        parts = args.ggt.replace(os.sep, "/").split("/")
        cat = "misc"
        for i, p in enumerate(parts):
            if p in ("circuit", "mechanics", "misc", "field"):
                cat = p
        snip_root = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..",
            "skills", "ggb-master", "macros", "snippets"))
        args.out_dir = os.path.join(snip_root, cat)
    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, info["cmd"] + ".md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(gen_snippet_md(info, xml_text, args.prefix))

    print(f"片段已生成：{out_path}")
    print(f"输入：{', '.join(info['inputs']) or '—'} → 输出：{', '.join(info['outputs']) or '—'}")
    print(f"标签改名 {len(mapping)} 个（前缀 {args.prefix}）；自证：{msg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
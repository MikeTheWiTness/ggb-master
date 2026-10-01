#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ggb_pack.py —— 将项目工作目录打包为 .ggb（Generate 路线第 7 步）。

用法：
  python3 ggb_pack.py <项目目录> -o <输出.ggb> [--skip-check]

打包前默认先跑一次 ggb_check.py 五层校验（--skip-check 仅在排查时用）。
包内容 = 根级白名单文件 + 按引用收集的素材：
  - 引用源：geogebra.xml 的 image 元素 <file name>、geogebra_macro.xml 的 iconFile；
  - 素材定位：<项目>/media/<引用路径> 或 <项目>/<引用路径>（unpack 产物结构）；
  - zip 内路径 = 引用路径（与 <file name>/iconFile 严格一致）；
  - 缺失引用 → 拒绝打包（error）；目录内未引用图片 → 打印提示并不打包。
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import zipfile

ALLOWED = [
    "geogebra.xml",
    "geogebra_defaults2d.xml",
    "geogebra_defaults3d.xml",
    "geogebra_javascript.js",
    "geogebra_thumbnail.png",
    "geogebra_macro.xml",
]
IMG_EXT = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(SCRIPT_DIR, "ggb_check.py")


def collect_refs(proj: str) -> set[str]:
    """收集包内素材引用路径（image <file name> + 宏 iconFile）。"""
    refs = set()
    for fn in ("geogebra.xml", "geogebra_macro.xml"):
        p = os.path.join(proj, fn)
        if not os.path.exists(p):
            continue
        s = open(p, encoding="utf-8").read()
        # 自闭合标签可能带空格（XML 序列化差异）：name="..." 与 name="..." / 均接受
        refs |= set(re.findall(r'<file name="([^"]+)"\s*/>', s))
        if fn == "geogebra_macro.xml":
            refs |= set(re.findall(r'iconFile="([^"]+)"', s))
    return {r for r in refs if r}


def locate_media(proj: str, rel: str) -> str | None:
    """在项目目录下找素材：media/<rel> 或 <rel>（unpack 产物直接放根）。"""
    for cand in (os.path.join(proj, "media", rel), os.path.join(proj, rel)):
        if os.path.isfile(cand):
            return cand
    return None


def find_unreferenced(proj: str, refs: set[str]) -> list[str]:
    """media/ 与项目根下未引用的图片（排除缩略图与引用集）。"""
    found = set()
    for dirpath, _dirs, files in os.walk(proj):
        for fn in files:
            if not fn.lower().endswith(IMG_EXT) or fn == "geogebra_thumbnail.png":
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), proj)
            found.add(rel)
    return sorted(found - refs)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ggb_pack.py", description="ggb-master 打包")
    ap.add_argument("proj", help="项目目录（含 geogebra.xml）")
    ap.add_argument("-o", "--output", required=True, help="输出 .ggb 路径")
    ap.add_argument("--skip-check", action="store_true", help="跳过 ggb_check 质量门（排查用）")
    args = ap.parse_args(argv)

    xml_path = os.path.join(args.proj, "geogebra.xml")
    if not os.path.exists(xml_path):
        print(f"错误：{xml_path} 不存在", file=sys.stderr)
        return 2

    if not args.skip_check:
        r = subprocess.run([sys.executable, CHECK, xml_path, "--quiet"],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("质量门未通过，拒绝打包。请先修复 ggb_check 报错：", file=sys.stderr)
            print(r.stdout, file=sys.stderr)
            return 1

    out_dir = os.path.dirname(os.path.abspath(args.output)) or "."
    os.makedirs(out_dir, exist_ok=True)

    # 根级白名单文件
    files = []
    for name in ALLOWED:
        p = os.path.join(args.proj, name)
        if os.path.exists(p):
            files.append(p)
    if not files:
        print("错误：项目目录里没有任何可打包文件", file=sys.stderr)
        return 2

    # 素材：按引用收图
    refs = collect_refs(args.proj)
    media_src = {}
    missing = []
    for rel in sorted(refs):
        src = locate_media(args.proj, rel)
        if src is None:
            missing.append(rel)
        else:
            media_src[rel] = src
    if missing:
        print("错误：以下素材被引用但项目目录中找不到（放 <项目>/media/<路径> 或解包结果里）：",
              file=sys.stderr)
        for rel in missing:
            print(f"  - {rel}", file=sys.stderr)
        return 1

    with zipfile.ZipFile(args.output, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, arcname=os.path.basename(p))
        for rel, src in sorted(media_src.items()):
            z.write(src, arcname=rel)

    print(f"已打包 {len(files)} 个文件 + {len(media_src)} 张素材 → {args.output}")
    for f in files:
        print("  -", os.path.basename(f))
    for rel in sorted(media_src):
        print("  -", rel)

    leftover = find_unreferenced(args.proj, refs)
    if leftover:
        print("提示：以下图片未被任何引用，未打包（如需保留请先引用或删除）：")
        for rel in leftover:
            print("  -", rel)
    print("提示：请在 GeoGebra Classic / 网页端打开验证视觉效果（本工具链无视觉闭环）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())

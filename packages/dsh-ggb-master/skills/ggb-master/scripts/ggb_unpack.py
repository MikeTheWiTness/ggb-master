#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ggb_unpack.py —— 解包 .ggb 到工作目录（Modify 路线第 2 步）。

用法：
  python3 ggb_unpack.py <文件.ggb> [-o <输出目录>] [--force]

解出包内全部工作内容：根级白名单文件（xml/defaults/js/缩略图/宏）
放输出目录根，其余条目（图片素材等）按 zip 内相对路径原样解开，
保证 <file name> 引用路径在解包后可直接命中。
默认输出到 <文件同名目录>/。
"""
from __future__ import annotations

import argparse
import os
import sys
import zipfile

ALLOWED = {
    "geogebra.xml",
    "geogebra_defaults2d.xml",
    "geogebra_defaults3d.xml",
    "geogebra_javascript.js",
    "geogebra_thumbnail.png",
    "geogebra_macro.xml",
}


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ggb_unpack.py", description="ggb-master 解包")
    ap.add_argument("ggb", help=".ggb 文件路径")
    ap.add_argument("-o", "--output", help="输出目录（默认：<.ggb 同名目录>）")
    ap.add_argument("--force", action="store_true", help="覆盖已存在文件")
    args = ap.parse_args(argv)

    if not os.path.exists(args.ggb):
        print(f"错误：文件不存在 {args.ggb}", file=sys.stderr)
        return 2

    out = args.output or os.path.splitext(os.path.basename(args.ggb))[0]
    os.makedirs(out, exist_ok=True)

    try:
        zf = zipfile.ZipFile(args.ggb)
    except zipfile.BadZipFile:
        print(f"错误：{args.ggb} 不是有效的 zip 包", file=sys.stderr)
        return 2

    written = []
    for info in zf.infolist():
        if info.is_dir():
            continue
        base = os.path.basename(info.filename)
        if base in ALLOWED:
            dst = os.path.join(out, base)
        else:
            dst = os.path.join(out, info.filename)   # 素材等保留目录结构
        if os.path.exists(dst) and not args.force:
            print(f"跳过（已存在，--force 覆盖）：{dst}", file=sys.stderr)
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with zf.open(info) as src, open(dst, "wb") as f:
            f.write(src.read())
        written.append(info.filename)

    if not written:
        print("警告：包里没有可识别的工作文件", file=sys.stderr)
    else:
        print(f"已解包 {len(written)} 个文件 → {out}/")
        for w in written:
            print("  -", w)
    return 0


if __name__ == "__main__":
    sys.exit(main())
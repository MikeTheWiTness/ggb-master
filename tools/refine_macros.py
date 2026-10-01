#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""refine_macros.py —— 把提取出的宏候选归并为范式工具库。

归并键 = (图标 basename, 构造指纹, 输入数, 输出数)。
同键的 193 种 cmdName（含数字后缀副本）会合成一个工具，取"构造最完整"副本为 canonical，
并以"组内最常用 cmdName（去数字后缀）"作为工具名重写 cmdName：
  - 产出 macros/refined/<工具名>.ggt（内含 geogebra_macro.xml + 图标 PNG，可导入 GeoGebra）
  - 图标同步复制到 media/library/，并生成工具库索引

用法：
  python3 tools/refine_macros.py [--lib "samples"] [--out extractions]
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_patterns as ep  # noqa: E402


def icon_base(icon: str) -> str:
    return os.path.basename(icon) if icon else ''


def base_name(cmd: str) -> str:
    """去掉纯数字后缀：传送带1 → 传送带；R2 → R；电阻2点 保持原样。"""
    m = re.match(r'^(.*?)(\d+)$', cmd)
    return m.group(1) if m else cmd


def safe(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', '_', name)


# 无中文名工具的语义命名：键 = 图标文件名（无图标的用 cmdName 基名）。
# 依据：图标文件名 + 构造命令序列 + 入出口径（对照 refined-report.md 与原库用法）。
RENAME = {
    'qiangjiao1123.png': '强角',        # Tool3 族：PolyLine+Div+Sequence 的角分度工具
    '地面212.png': '地面',              # Tool4 族：地面/斜面底座
    '调R21.png': '变阻器三点',          # Tool5 族：3 输入滑动变阻器（调R 是 2 输入版）
    '垂线段.png': '垂线段',             # Tool63 族：ClosestPoint+Segment 垂直落线
    '定R.png': '定值电阻',              # R 族：2 点定值电阻（与"定R"组为不同构造版本）
    '定R123.png': '定值电阻_v2',        # 开普勒(2) 里的 3 点构造版
    '调R2123.png': '变阻器三点_v2',     # 开普勒(2) 里的 3 输入版
    '电阻箱3.png': '电阻箱三点',        # 开普勒(2) 里的 3 输入版（电阻箱组是 2 输入版）
    '小车.png': '小车',                 # littlecar 族
    '三点斜面.png': '三点斜面',         # threedot 族
    'Hy': 'α散射轨线',                  # α 粒子散射：入射点+质量+初速+电荷 → 轨道（CurveCartesian）
    'Hy1': 'α散射轨线_v2',              # 9 入能量精细版（E1/E2/E4）
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', default=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'samples'))
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'extractions'))
    args = ap.parse_args()
    out = args.out
    refined_dir = os.path.join(out, 'macros', 'refined')
    media_dir = os.path.join(out, 'media', 'library')
    # 生成物目录：先清空再重建，保证改名后不残留旧文件
    shutil.rmtree(refined_dir, ignore_errors=True)
    shutil.rmtree(media_dir, ignore_errors=True)
    os.makedirs(refined_dir, exist_ok=True)
    os.makedirs(media_dir, exist_ok=True)

    by_name = ep.extract_macros(args.lib)
    # 展平为定义列表，建组
    groups = collections.defaultdict(list)
    for cmd, defs in by_name.items():
        for d in defs:
            key = (icon_base(d['icon']), d['fingerprint'], len(d['input']), len(d['output']))
            groups[key].append((cmd, d))

    used_names = set()
    rows = []
    for key in sorted(groups, key=lambda k: -len(groups[k])):
        members = groups[key]
        # canonical：构造最完整者；平局优先来自成员最多的来源文件
        can = max(members, key=lambda m: (len(m[1]['comms']), m[1]['nels'],
                                          sum(1 for mm in members if mm[1]['file'] == m[1]['file'])))
        cmd, d = can
        base = base_name(cmd)
        # 组名：中文名（如 电阻箱/调R/定R）直接保留；
        # 非中文名才查 RENAME 语义命名表（键=图标名 → cmdName 原样 → 基名）。
        if re.search(r'[\u4e00-\u9fff]', base):
            name = base
        else:
            name = (RENAME.get(icon_base(d['icon']))
                    or RENAME.get(cmd)
                    or RENAME.get(base)
                    or base)
        if name in used_names:
            n = 2
            while f'{name}_v{n}' in used_names:
                n += 1
            name = f'{name}_v{n}'
        used_names.add(name)
        names = sorted(set(c for c, _ in members))
        inst = sorted(set(mm[1]['file'] for mm in members))
        # 重写 cmdName
        raw = d['raw']
        raw = re.sub(r'(<macro\s+cmdName=")[^"]*(")', rf'\g<1>{name}\g<2>', raw, count=1)
        ggt_path = os.path.join(refined_dir, f'{safe(name)}.ggt')
        try:
            with zipfile.ZipFile(os.path.join(args.lib, d['file'])) as src:
                icon_bytes = src.read(d['icon']) if d['icon'] else None
        except Exception:
            icon_bytes = None
        with zipfile.ZipFile(ggt_path, 'w', zipfile.ZIP_DEFLATED) as ggt:
            ggt.writestr('geogebra_macro.xml', raw)
            if icon_bytes and d['icon']:
                ggt.writestr(d['icon'], icon_bytes)
                cpy = os.path.join(media_dir, f'{safe(name)}__{icon_base(d["icon"])}')
                with open(cpy, 'wb') as fh:
                    fh.write(icon_bytes)
        rows.append({
            'name': name, 'names': names, 'help': d['toolHelp'] or '', 'in': len(d['input']),
            'out': len(d['output']), 'icon': icon_base(d['icon']) or '(无)',
            'files': len(inst), 'nnames': len(names),
            'canonical': d['file'], 'ncmd': len(d['comms']), 'nels': d['nels'],
            'ggt': os.path.basename(ggt_path),
        })

    rows.sort(key=lambda r: -r['files'])
    rep = ['# 宏工具库归并报告（193 → %d 个工具）\n' % len(rows), '',
           '归并键：图标 + 构造指纹 + 输入数 + 输出数。同名工具的数字后缀副本已并入；'
           '"变体别名"列是原 cmdName 合集（嵌入时须用"工具名"列作为命令名）。\n',
           '| 工具名 | 变体别名 | 签名(toolHelp) | 入 | 出 | 图标 | 文件数 | 别名数 | '
           'canonical 来源 | 构造 | .ggt |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        rep.append(f"| {r['name']} | {', '.join(r['names'])} | {r['help']} | {r['in']} | {r['out']} | "
                   f"{r['icon']} | {r['files']} | {r['nnames']} | {r['canonical']} | "
                   f"{r['ncmd']}c/{r['nels']}e | `{r['ggt']}` |")
    rep.append('\n---\n*由 tools/refine_macros.py 生成；工具名为调用命令名，与源库保持一致。*')
    with open(os.path.join(out, 'refined-report.md'), 'w') as fh:
        fh.write('\n'.join(rep))
    print(f'完成：193 种 → {len(rows)} 组工具；.ggt 在 {refined_dir}（{len(os.listdir(refined_dir))} 个），'
          f'图标在 {media_dir}')


if __name__ == '__main__':
    main()

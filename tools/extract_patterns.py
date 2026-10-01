#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_patterns.py —— 从成品 .ggb 库提取"范式单元"候选。

只做提取与归类，不改任何源文件；产物输出到 --out 目录（默认 extractions/）：
  macros/raw/<来源文件>/<n>_<cmdName>.xml    每个宏定义的原始 XML
  macros/canonical/<cmdName>.xml             每组推荐的完整副本
  patterns/<章节>__<文件>__按钮.md            按钮变体聚类报告
  patterns/构造手法.md                       场线/轨迹/ODE 等构造手法摘录
  media/manifest.md                          图片素材清单（引用级）
  report.md                                  总览报告

用法：
  python3 tools/extract_patterns.py [--lib "samples"] [--out extractions]
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

IMG_EXT = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg')


def iter_ggb(lib):
    for root, _dirs, fs in os.walk(lib):
        for f in sorted(fs):
            if f.lower().endswith('.ggb'):
                yield os.path.join(root, f)


def read_xml(path, entry):
    try:
        with zipfile.ZipFile(path) as z:
            return z.read(entry).decode('utf-8', 'ignore')
    except Exception:
        return None


def norm_id(value):
    """把 label 名替换成位置序号：label 统一规则 (num) → num"""
    return value.replace("(", "").replace(")", "") if value else value


# ---------------------------------------------------------------- 宏提取
def extract_macros(lib):
    """返回 {cmdName: [ {file, macro_xml, props, fingerprint, ncmd, nel} ]}"""
    by_name = collections.defaultdict(list)
    for p in iter_ggb(lib):
        mx = read_xml(p, 'geogebra_macro.xml')
        if mx is None:
            continue
        try:
            root = ET.fromstring(mx)
        except ET.ParseError:
            continue
        for i, m in enumerate(root.iter('macro')):
            cmd = m.get('cmdName') or m.get('toolName') or f'unnamed{i}'
            ins = [a.get('a0')] if m.find('macroInput') is None else [
                c.get(f'a{k}') for k in range(99)
                for c in [m.find('macroInput')] if c is not None and c.get(f'a{k}') is not None]
            outs = []
            mo = m.find('macroOutput')
            if mo is not None:
                outs = [mo.get(f'a{k}') for k in range(99) if mo.get(f'a{k}') is not None]
            comms = [c.get('name') for c in m.iter('command')]
            nels = len(list(m.iter('element')))
            # 指纹：命令名序列 + 每类元素计数（用于判断同名宏构造是否一致）
            ecnt = collections.Counter((e.get('type') or '?') for e in m.iter('element'))
            fingerprint = (tuple(comms), tuple(sorted(ecnt.items())))
            sub = ET.tostring(m, encoding='unicode')
            by_name[cmd].append({
                'file': p, 'i': i, 'raw': sub, 'input': ins, 'output': outs,
                'toolHelp': m.get('toolHelp', ''), 'icon': m.get('iconFile', ''),
                'toolName': m.get('toolName', ''), 'comms': comms, 'nels': nels,
                'ecnt': ecnt, 'fingerprint': fingerprint,
                'copyCaptions': m.get('copyCaptions', ''),
            })
    return by_name


def pick_canonical(group):
    """每组选构造最完整者（命令数最多，其次元素多）"""
    return max(group, key=lambda d: (len(d['comms']), d['nels']))


def dump_macro_candidates(by_name, out):
    raw_dir = os.path.join(out, 'macros', 'raw')
    can_dir = os.path.join(out, 'macros', 'canonical')
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(can_dir, exist_ok=True)
    lines = []
    for cmd, group in sorted(by_name.items()):
        can = pick_canonical(group)
        safe = re.sub(r'[\\/:*?"<>|]', '_', cmd)
        with open(os.path.join(can_dir, f'{safe}.xml'), 'w') as fh:
            fh.write(can['raw'])
        for d in group:
            src = re.sub(r'[\\/:*?"<>|]', '_', d['file'])[:120]
            ddir = os.path.join(raw_dir, src)
            os.makedirs(ddir, exist_ok=True)
            with open(os.path.join(ddir, f'{d["i"]}_{safe}.xml'), 'w') as fh:
                fh.write(d['raw'])
        # 一致性分组
        fp_groups = collections.defaultdict(list)
        for d in group:
            fp_groups[d['fingerprint']].append(os.path.basename(d['file']))
        same = max((v for v in fp_groups.values()), key=len)
        lines.append(
            f"| {cmd} | {d['toolHelp']} | {len(d['input'])} | {len(d['output'])} | "
            f"{can['icon']} | {len(group)} | {can['file']} | {len(can['comms'])} cmds / {can['nels']} els | "
            f"同构最大组 {len(same)} 文件 |")
    return lines


# ---------------------------------------------------------------- 按钮提取
# 行为签名：把脚本中每条命令变成"命令名(参数个数)"并按序去重归一
def button_signature(script: str) -> str:
    """行为签名：按出现顺序取命令名（方括号/圆括号两种调用形态），赋值算 Assign。"""
    if not script:
        return '(空)'
    cmds = []
    for token in re.findall(r'\b([A-Za-z_][A-Za-z0-9_]*)\s*[\[(]', script):
        cmds.append(token)
    seen = []
    for c in cmds:
        if c not in seen:
            seen.append(c)
    return '+'.join(seen) if seen else '(赋值)'


def extract_buttons(lib):
    """返回 {sig: [ {file, caption, script} ]}"""
    by_sig = collections.defaultdict(list)
    for p in iter_ggb(lib):
        xml = read_xml(p, 'geogebra.xml')
        if xml is None:
            continue
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            continue
        for el in root.iter('element'):
            if el.get('type') != 'button':
                continue
            cap = el.find('caption')
            cap = cap.get('val') if cap is not None else ''
            gs = el.find('ggbscript')
            script = gs.get('val') if gs is not None else ''
            by_sig[button_signature(script)].append(
                {'file': p, 'caption': cap, 'script': script})
    return by_sig


# ---------------------------------------------------------------- 构造手法
def scan_techniques(lib):
    """统计/摘录：NSolveODE、SlopeField、Sequence+Vector、Zip+Flatten、Rotate+Locus、image"""
    tech = {
        'NSolveODE': [], 'SlopeField': [], 'SeqVec': [], 'ZipFlatten': [],
        'RotLocus': [], 'Locus': [], 'CurveCartesian': [], 'image': [],
    }
    for p in iter_ggb(lib):
        xml = read_xml(p, 'geogebra.xml')
        if xml is None:
            continue
        t = lambda n: f'<command name="{n}">'
        if t('NSolveODE') in xml:
            for m in re.finditer(r'<command name="NSolveODE">.*?</command>', xml, re.S):
                tech['NSolveODE'].append((p, re.sub(r'\s+', ' ', m.group(0))))
        if t('SlopeField') in xml:
            for m in re.finditer(r'<command name="SlopeField">.*?</command>', xml, re.S):
                tech['SlopeField'].append((p, re.sub(r'\s+', ' ', m.group(0))))
        if t('Sequence') in xml and t('Vector') in xml:
            for m in re.finditer(r'<command name="Sequence">.*?</command>', xml, re.S):
                if 'Vector' in m.group(0):
                    tech['SeqVec'].append((p, re.sub(r'\s+', ' ', m.group(0))))
        if t('Zip') in xml and t('Flatten') in xml:
            tech['ZipFlatten'].append(p)
        if t('Rotate') in xml and t('Locus') in xml:
            tech['RotLocus'].append(p)
        if t('Locus') in xml:
            tech['Locus'].append(p)
        if t('CurveCartesian') in xml:
            tech['CurveCartesian'].append(p)
        if 'type="image"' in xml:
            tech['image'].append(p)
    return tech


# ---------------------------------------------------------------- 素材清单
def collect_media(lib):
    """图片素材：引用级（image 元素 file 名）与文件级（zip 内图，非缩略图）"""
    used = collections.Counter()   # 被引用的素材名 → 文件数
    used_files = collections.defaultdict(list)
    pooled = collections.Counter()  # zip 内素材名 → 文件数
    pooled_files = collections.defaultdict(list)
    for p in iter_ggb(lib):
        try:
            with zipfile.ZipFile(p) as z:
                names = z.namelist()
                xml = z.read('geogebra.xml').decode('utf-8', 'ignore')
        except Exception:
            continue
        for n in names:
            if n.lower().endswith(IMG_EXT) and 'thumbnail' not in n.lower():
                base = os.path.basename(n)
                pooled[base] += 1
                pooled_files[base].append((p, n))
        for m in re.finditer(r'<file name="([^"]*)"/>', xml):
            if not m.group(1):
                continue
            base = os.path.basename(m.group(1))
            used[base] += 1
            used_files[base].append((p, m.group(1)))
    return used, used_files, pooled, pooled_files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lib', default=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'samples'))
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), 'extractions'))
    args = ap.parse_args()
    out = args.out
    os.makedirs(out, exist_ok=True)

    # 1. 宏
    by_name = extract_macros(args.lib)
    macro_lines = dump_macro_candidates(by_name, out)

    # 2. 按钮
    by_sig = extract_buttons(args.lib)
    top_sigs = sorted(by_sig.items(), key=lambda x: -len(x[1]))

    # 3. 构造手法
    tech = scan_techniques(args.lib)

    # 4. 素材
    used, used_files, pooled, pooled_files = collect_media(args.lib)

    # ---------------- 报告
    rep = []
    rep.append('# 范式单元提取报告（候选）\n')
    rep.append(f'- 源库：`{args.lib}`')
    rep.append(f'- 宏工具种类：**{len(by_name)}** 种；宏定义总数：'
               f'{sum(len(v) for v in by_name.values())}')
    rep.append(f'- 按钮元素：**{sum(len(v) for v in by_sig.values())}** 个，'
               f'行为类型 {len(by_sig)} 种（前 15 见下）')
    rep.append(f'- 被引用的图片素材：**{len(used)}** 种；zip 内图片素材：**{len(pooled)}** 种'
               f'（其中 {len(set(pooled) - set(used))} 种未被引用=打包残留）\n')

    rep.append('## 一、宏工具候选\n（完整性按命令数最多者；"同构最大组"=指纹一致的来源文件数）\n')
    rep.append('| 工具名 | 签名(toolHelp) | 入参 | 出参 | 图标 | 来源文件数 | 推荐副本 | 构造规模 | 备注 |')
    rep.append('|---|---|---|---|---|---|---|---|---|')
    rep += macro_lines
    rep.append('')

    rep.append('## 二、按钮行为变体（前 15）\n')
    rep.append('| 行为签名 | 数量 | 代表 caption | 代表脚本（缩写） | 代表文件 |')
    rep.append('|---|---|---|---|---|')
    for sig, items in top_sigs[:15]:
        it = items[0]
        s = ' '.join(it['script'].split())
        if len(s) > 120:
            s = s[:117] + '…'
        rep.append(f"| {sig if sig != '(空)' else '空'} | {len(items)} | "
                   f"{it['caption'] or '(无)'} | {s} | {os.path.basename(it['file'])} |")
    rep.append('')
    rep.append('## 三、构造手法摘录\n')
    rep.append(f'- NSolveODE：{len(tech["NSolveODE"])} 处（{len(set(p for p,_ in tech["NSolveODE"]))} 个文件）')
    rep.append(f'- SlopeField：{len(tech["SlopeField"])} 处（{len(set(p for p,_ in tech["SlopeField"]))} 个文件）')
    rep.append(f'- Sequence(构造含 Vector)：{len(tech["SeqVec"])} 处（{len(set(p for p,_ in tech["SeqVec"]))} 个文件）')
    rep.append(f'- Zip+Flatten：{len(tech["ZipFlatten"])} 个文件；Rotate+Locus 整合法：{len(tech["RotLocus"])} 个文件')
    rep.append(f'- Locus：{len(tech["Locus"])} 个文件；CurveCartesian：{len(tech["CurveCartesian"])} 个文件；'
               f'image 元素：{len(tech["image"])} 个文件')
    rep.append('\n（每个手法的具体命令体见 `patterns/构造手法.md`）\n')

    rep.append('## 四、图片素材清单\n'
               f'（**引用级** {len(used)} 种；供建 media-library 用；只列被 ≥2 个文件引用的，'
               f'完整清单见 `media/manifest.md`）\n')
    rep.append('| 素材文件 | 引用它的文件数 | 推荐来源文件（zip 内路径） |')
    rep.append('|---|---|---|')
    for base, n in used.most_common(60):
        if n < 2:
            continue
        p, inner = used_files[base][0]
        rep.append(f"| {base} | {n} | `{os.path.basename(p)}` → `{inner}` |")
    rep.append('')
    rep.append('---\n*由 tools/extract_patterns.py 自动生成；候选供人工精炼成范式单元（patterns+macros 两库）。*')

    with open(os.path.join(out, 'report.md'), 'w') as fh:
        fh.write('\n'.join(rep))

    # 构造手法详录
    tl = ['# 构造手法摘录（候选）\n']
    tl.append('## NSolveODE（全部实例）\n')
    for p, cmd in tech['NSolveODE']:
        tl.append(f'- `{os.path.basename(p)}`\n  - {cmd}\n')
    tl.append('## SlopeField（全部实例）\n')
    for p, cmd in tech['SlopeField']:
        tl.append(f'- `{os.path.basename(p)}`\n  - {cmd}\n')
    tl.append('## Sequence 内含 Vector（全部实例）\n')
    for p, cmd in tech['SeqVec']:
        tl.append(f'- `{os.path.basename(p)}`\n  - {cmd}\n')
    tl.append('## Zip+Flatten 文件\n')
    for p in tech['ZipFlatten']:
        tl.append(f'- `{os.path.basename(p)}`\n')
    tl.append('## Rotate+Locus 文件\n')
    for p in tech['RotLocus']:
        tl.append(f'- `{os.path.basename(p)}`\n')
    tl.append('## Locus 文件\n')
    for p in tech['Locus']:
        tl.append(f'- `{os.path.basename(p)}`\n')
    tl.append('## CurveCartesian 文件\n')
    for p in tech['CurveCartesian']:
        tl.append(f'- `{os.path.basename(p)}`\n')
    os.makedirs(os.path.join(out, 'patterns'), exist_ok=True)
    with open(os.path.join(out, 'patterns', '构造手法.md'), 'w') as fh:
        fh.write('\n'.join(tl))

    # 素材明细
    ml = ['# 图片素材清单（引用级 → 来源文件）\n']
    for base, n in used.most_common():
        src = ', '.join(f'`{os.path.basename(p)}`→`{inner}`' for p, inner in used_files[base][:3])
        ml.append(f'## {base}（{n} 文件引用）\n{src}\n')
    ml.append('\n## 仅 zip 内残留（未被引用）样例\n')
    for base in sorted(set(pooled) - set(used))[:30]:
        p, inner = pooled_files[base][0]
        ml.append(f'- {base}（`{os.path.basename(p)}` → `{inner}`）\n')
    os.makedirs(os.path.join(out, 'media'), exist_ok=True)
    with open(os.path.join(out, 'media', 'manifest.md'), 'w') as fh:
        fh.write(''.join(ml))

    print(f'完成。宏工具 {len(by_name)} 种；按钮 {sum(len(v) for v in by_sig.values())} 个；'
          f'素材引用级 {len(used)} 种。产物 → {out}')


if __name__ == '__main__':
    main()

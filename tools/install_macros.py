#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""install_macros.py —— 把精炼宏工具库安装进 skill 目录（P1 落位）。

从 extractions/refined-report.md 读归并结论 → 按语义分类拷贝 .ggt 到
skills/ggb-master/macros/<类>/，并生成自包含 README.md（工具名/签名/入出/共享数/别名，
不含任何仓库路径）。

用法：
  python3 tools/install_macros.py [--refined extractions/macros/refined]
                                   [--report extractions/refined-report.md]
                                   [--dst skills/ggb-master/macros]
"""
from __future__ import annotations

import argparse
import os
import re
import shutil

# 工具名 → 分类目录（未列出的归 misc）
CATEGORY = {}
def _cat(cat, names):
    for n in names:
        CATEGORY[n] = cat

_cat('circuit', """mA表 mV表 二极管 二极管_v2 光敏电阻 光敏电阻_v2 分压变阻器 变压器 变阻器三点 变阻器三点_v2
定R 定值电阻 定值电阻_v2 小灯泡 灯泡 开关 开关_v2 微安表 检流计 热敏电阻 电动机 电压表 电压表_v2
电流表 电流表_v2 电流计 电源 电源_v2 电源_v3 电阻 电阻2点 电阻_v2 电阻箱 电阻箱_v2 电阻箱_v3
电阻箱adjust 电阻箱三点 调R 滑R 滑R三点 限流变阻器 限流变阻器_v2 电感 电感_v2 电容 电容器 电容器_v2""".split())
_cat('field', """匀强电场或磁场 圆出磁场 圆进磁场 圆形磁场 矩形磁场 矩形进磁场 方形出 正Q 负Q 正电荷 负电荷
出电流 进电流 纸面向外电流 纸面向里电流""".split())
_cat('mechanics', """三点斜面 传送带 凹槽 半圆槽 圆弧 圆环 地面 垂线 垂线段 定长直线 小物块 小车
折线弹簧 螺旋弹簧 滑轮 细杆 转轴 强角 贝塞尔曲线 正交分解 矢量分解 椭圆 正弦曲线 指数曲线 箭头
距离度量 长度度量 长度度量_v2 填充""".split())
# 其余（数轴/坐标系/标尺/α散射轨线等）归 misc


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--refined', default=None)
    ap.add_argument('--report', default=None)
    ap.add_argument('--dst', default=None)
    args = ap.parse_args()
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    refined = args.refined or os.path.join(root, 'extractions', 'macros', 'refined')
    report = args.report or os.path.join(root, 'extractions', 'refined-report.md')
    dst = args.dst or os.path.join(root, 'skills', 'ggb-master', 'macros')

    rows = []
    for line in open(report, encoding='utf-8'):
        if not line.strip().startswith('|'):
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 8 or cells[0] == '工具名' or cells[0].startswith('-'):
            continue
        rows.append({
            'name': cells[0], 'aliases': cells[1], 'help': cells[2],
            'n_in': cells[3], 'n_out': cells[4], 'icon': cells[5],
            'n_files': cells[6], 'ncmd': cells[8],
        })

    for cat in ('circuit', 'field', 'mechanics', 'misc'):
        os.makedirs(os.path.join(dst, cat), exist_ok=True)
    moved, skipped = 0, []
    for r in rows:
        cat = CATEGORY.get(r['name'], 'misc')
        src = os.path.join(refined, f"{r['name']}.ggt")
        if not os.path.exists(src):
            skipped.append(r['name'])
            continue
        shutil.copy2(src, os.path.join(dst, cat, f"{r['name']}.ggt"))
        r['cat'] = cat
        moved += 1

    # 自包含 README
    cats_desc = {
        'circuit': '电路符号（电阻/电源/开关/电表/电感电容/二极管/变阻器等）',
        'field': '场与电荷符号（正负电荷/进出电流视图/磁场区域标记/匀强场）',
        'mechanics': '力学元件（滑轮/弹簧/传送带/物块/斜面/旋转件/分解工具）',
        'misc': '标尺与坐标系（数轴/坐标纸/坐标轴/区间/散射轨线等）',
    }
    lines = ['# 宏工具库（自定义工具）',
             '',
             '> 106 个可复用自定义工具（.ggt），来自对真实 GeoGebra 成品的提取与归并；',
             '> 每个 .ggt 可直接导入 GeoGebra「我的工具」，或在 Modify/Generate 时把其',
             '> `geogebra_macro.xml` 定义拼入目标课件（见 references/construction-language.md §4.13）。',
             '',
             '导入后调用即命令：`定值电阻[A,B]`（A/B 为两个端点)。**工具名即命令名**；',
             ' `_v2/_v3` 后缀是不同作者的同名构造版本，按需选用。',
             '',
             '## 分类',
             '']
    for cat in ('circuit', 'field', 'mechanics', 'misc'):
        lines.append(f'- `{cat}/` — {cats_desc[cat]}')
    lines += ['', '## 全表', '', '| 工具名 | 签名 | 入 | 出 | 共享文件数 | 原 cmdName 别名 | 分类 |',
              '|---|---|---|---|---|---|---|']
    for r in sorted(rows, key=lambda r: r['name']):
        lines.append(f"| {r['name']} | {r['help']} | {r['n_in']} | {r['n_out']} | {r['n_files']} | "
                     f"{r['aliases']} | {r['cat']} |")
    lines.append('')
    lines.append('> 来源说明：工具从公开分享的真实课件提取归并（含官网作者 Roman Chijner / Stephen Jull 与'
                 '多位一线教师作品），供借鉴复用。')
    with open(os.path.join(dst, 'README.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f'安装完成：{moved} 个 .ggt → {dst}（跳过 {skipped or "无"}）；README 已生成')
    from collections import Counter
    print('  分类统计:', dict(Counter(r['cat'] for r in rows)))


if __name__ == '__main__':
    main()

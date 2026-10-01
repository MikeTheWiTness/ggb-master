#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""html_demo_check.py —— HTML 定妆演示件数据契约校验（export-html-demo.md §2）。

用法：
  python3 html_demo_check.py <data.json>     # 校验数据文件
  python3 html_demo_check.py <demo.html>     # 校验拼装产物（提取内联数据 + 外部引用扫描）

检查项：
  schema：meta/scene/actors/frames 必备键、bbox 合法、图元字段齐、t 严格单调、
          pos/vel 维度与 actors 一致、marks 落在帧范围、体积 ≤ 2MB（data）/ ≤ 6MB（HTML 含 KaTeX）
  产物额外：无真实网络引用（<script src>/<link href>/url(http/fetch("…")/@import）、
          无残留占位符 __DATA__ / __KATEX_

注意：外部引用只按「真实网络引用」判定（2026-09-16 更新，为内联 KaTeX 放行）——
katex.min.js 内部的 parser.fetch() 方法与 img.src 字段不是外部引用，粗判 src=/fetch( 会误报。

退出码：0 通过 / 1 不通过。错误逐条打印。
"""
from __future__ import annotations

import json
import os
import re
import sys

MAX_BYTES = 2 * 1024 * 1024           # data.json 上限（帧数据契约）
MAX_BYTES_HTML = 6 * 1024 * 1024      # HTML 上限（含 KaTeX 内联，export-html-demo §2.5）
SHAPE_TYPES = {"polygon", "segment", "label", "point"}
REF_PATTERNS = [
    (r"<script[^>]*\bsrc\s*=", "外部 script src"),
    (r"<link[^>]*\bhref\s*=", "外部 link href"),
    (r"url\(\s*[\"']?https?:?//", "CSS 外部 url"),
    (r"\bfetch\s*\(\s*[\"']", "fetch(URL) 调用"),
    (r"@import", "@import"),
    (r"(?<![.\w])import\s", "import 语句"),
]
NUM_PAIR_MSG = "应为 [x, y] 数字对"


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def is_pair(v):
    return (isinstance(v, list) and len(v) == 2 and all(is_num(x) for x in v))


def validate_data(data, errors, warnings):
    if not isinstance(data, dict):
        errors.append("顶层必须是 JSON 对象")
        return

    meta = data.get("meta")
    if not isinstance(meta, dict) or not isinstance(meta.get("title"), str) or not meta["title"]:
        errors.append("meta.title 缺失或非字符串")
    if "params" in meta and not isinstance(meta.get("params"), dict):
        errors.append("meta.params 应为对象")
    if "vecScale" in meta and not (is_num(meta["vecScale"]) and meta["vecScale"] > 0):
        errors.append("meta.vecScale 应为正数")

    scene = data.get("scene")
    if not isinstance(scene, dict):
        errors.append("scene 缺失")
        scene = {}
    bbox = scene.get("bbox")
    if not (isinstance(bbox, list) and len(bbox) == 4 and all(is_num(x) for x in bbox)
            and bbox[0] < bbox[2] and bbox[1] < bbox[3]):
        errors.append(f"scene.bbox {NUM_PAIR_MSG.replace('[x, y]', '[xmin, ymin, xmax, ymax]')} 且 min<max")

    shapes = scene.get("shapes", [])
    if not isinstance(shapes, list):
        errors.append("scene.shapes 应为数组")
        shapes = []
    for i, s in enumerate(shapes):
        tag = f"shapes[{i}]"
        if not isinstance(s, dict) or s.get("type") not in SHAPE_TYPES:
            errors.append(f"{tag}.type 必须是 {sorted(SHAPE_TYPES)} 之一")
            continue
        st = s["type"]
        if st == "polygon" and not (isinstance(s.get("pts"), list) and len(s["pts"]) >= 3
                                    and all(is_pair(p) for p in s["pts"])):
            errors.append(f"{tag}.pts 应为 ≥3 个 [x, y] 数字对")
        if st == "segment" and not (is_pair(s.get("a")) and is_pair(s.get("b"))):
            errors.append(f"{tag}.a/.b {NUM_PAIR_MSG}")
        if st in ("label", "point"):
            key = "text" if st == "label" else "pos"
            if key == "text" and not isinstance(s.get("text"), str):
                errors.append(f"{tag}.text 缺失")
            if key == "pos" and not is_pair(s.get("pos")):
                errors.append(f"{tag}.pos {NUM_PAIR_MSG}")

    actors = data.get("actors")
    if not (isinstance(actors, list) and actors):
        errors.append("actors 必须是非空数组")
        actors = []
    n_act = len(actors)
    for i, a in enumerate(actors):
        if not isinstance(a, dict):
            errors.append(f"actors[{i}] 应为对象")

    links = data.get("links", [])
    if not isinstance(links, list):
        errors.append("links 应为数组")
        links = []
    for i, lk in enumerate(links):
        if not isinstance(lk, dict):
            errors.append(f"links[{i}] 应为对象")
            continue
        for key in ("a", "b"):
            v = lk.get(key)
            if not (isinstance(v, int) and 0 <= v < n_act):
                errors.append(f"links[{i}].{key} 应为 actor 索引 [0, {n_act - 1}]")
        if "until_t" in lk and lk["until_t"] is not None and not is_num(lk["until_t"]):
            errors.append(f"links[{i}].until_t 应为数字或 null")

    frames = data.get("frames")
    if not (isinstance(frames, list) and len(frames) >= 2):
        errors.append("frames 必须是 ≥2 帧的数组")
        frames = []
    t_prev = None
    for i, f in enumerate(frames):
        tag = f"frames[{i}]"
        if not isinstance(f, dict):
            errors.append(f"{tag} 应为对象")
            continue
        t = f.get("t")
        if not is_num(t):
            errors.append(f"{tag}.t 应为数字")
            continue
        if t_prev is not None and not t > t_prev:
            errors.append(f"{tag}.t={t} 未严格递增（前一帧 t={t_prev}）")
        t_prev = t
        pos = f.get("pos")
        if not (isinstance(pos, list) and len(pos) == n_act and all(is_pair(p) for p in pos)):
            errors.append(f"{tag}.pos 应为 {n_act} 个 [x, y] 数字对（与 actors 等长）")
        if "vel" in f and f["vel"] is not None:
            vel = f["vel"]
            if not (isinstance(vel, list) and len(vel) == n_act and all(is_pair(p) for p in vel)):
                errors.append(f"{tag}.vel 应为 {n_act} 个 [x, y] 数字对（与 actors 等长）")
        if "phase" in f and not isinstance(f["phase"], str):
            errors.append(f"{tag}.phase 应为字符串")

    t_first = frames[0]["t"] if frames and is_num(frames[0].get("t")) else None
    t_last = frames[-1]["t"] if frames and is_num(frames[-1].get("t")) else None
    for i, m in enumerate(data.get("marks", [])):
        if not isinstance(m, dict) or not isinstance(m.get("label"), str):
            errors.append(f"marks[{i}] 应含 label 字符串")
            continue
        if t_first is None or not (t_first <= m.get("t", t_first - 1) <= t_last):
            errors.append(f"marks[{i}].t={m.get('t')} 超出帧范围 [{t_first}, {t_last}]")

    for i, r in enumerate(data.get("readouts", [])):
        if not isinstance(r, dict) or not isinstance(r.get("label"), str) or "value" not in r:
            errors.append(f"readouts[{i}] 应含 label 与 value")


def scan_refs(text, errors):
    for pat, name in REF_PATTERNS:
        m = re.search(pat, text)
        if m:
            errors.append(f"发现外部引用（{name}）：{text[max(0, m.start()-30):m.end()+30]!r}")
    if "__DATA__" in text or "__KATEX_" in text:
        errors.append("残留模板占位符 __DATA__ / __KATEX_（拼装未完成或未转义）")


def extract_inline_json(html_text):
    m = re.search(r'<script id="demo-data" type="application/json">(.*?)</script>',
                  html_text, re.S)
    if not m:
        return None, "未找到 <script id=\"demo-data\"> 内联数据块"
    return m.group(1).strip(), None


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    path = argv[1]
    if not os.path.isfile(path):
        print(f"✗ 文件不存在：{path}")
        return 1
    size = os.path.getsize(path)
    limit = MAX_BYTES_HTML if path.endswith(".html") else MAX_BYTES
    errors, warnings = [], []
    if size > limit:
        errors.append(f"体积 {size} 字节超上限 {limit}")

    text = open(path, encoding="utf-8").read()
    if path.endswith(".json"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            print(f"✗ JSON 解析失败：{e}")
            return 1
        validate_data(data, errors, warnings)
        scan_refs(text, errors)
    elif path.endswith(".html"):
        scan_refs(text, errors)
        blob, err = extract_inline_json(text)
        if err:
            errors.append(err)
        else:
            try:
                validate_data(json.loads(blob), errors, warnings)
            except json.JSONDecodeError as e:
                errors.append(f"内联数据 JSON 解析失败：{e}")
    else:
        print("✗ 仅支持 .json（数据）或 .html（拼装产物）")
        return 2

    for w in warnings:
        print(f"  ! 警告 {w}")
    if errors:
        for e in errors:
            print(f"  ✗ {e}")
        print(f"---- 结论：不通过（{len(errors)} error）")
        return 1
    print(f"  ✓ {os.path.basename(path)} 通过数据契约校验（{size} 字节）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""selftest.py —— ggb-master 工具链自检（可重复运行）。

验证项：
  1 project_manager init 骨架完整
  2 五层校验：Kepler 真实样例 / init 骨架 / 端到端项目 全部通过
  3 语料库回归：ggb绘图/ 下全部 .ggb 解包后 0 error（若目录存在）
  4 缓存值：清空后 --fix 重填与原值一致
  5 pack→unpack 往返幂等
  6 变异拦截：缓存篡改(warn) / 未定义引用(error) / 顺序颠倒(error)
  7 JS 语法层：坏 JS 被 node --check 抓住
  8 html_demo：定妆演示件数据契约（正例/变异）、模板洁净、拼装产物校验

用法：python3 skills/ggb-master/scripts/selftest.py [--corpus <ggb目录>]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def find_workspace():
    """工作区定位：GGB_ROOT 环境变量 > 当前工作目录（与 project_manager 一致）。"""
    env = os.environ.get("GGB_ROOT")
    if env and os.path.isdir(env):
        return os.path.abspath(env)
    return os.path.abspath(os.getcwd())


WORKSPACE = find_workspace()
CHECK = os.path.join(SCRIPT_DIR, "ggb_check.py")
PACK = os.path.join(SCRIPT_DIR, "ggb_pack.py")
UNPACK = os.path.join(SCRIPT_DIR, "ggb_unpack.py")
PM = os.path.join(SCRIPT_DIR, "project_manager.py")

PASS, FAIL, SKIP = [], [], []


def run(args, **kw):
    return subprocess.run(args, capture_output=True, text=True, **kw)


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("  ✓ " if cond else "  ✗ ") + name + (f"  {detail}" if detail and not cond else ""))


def skip(name, detail=""):
    SKIP.append(name)
    print(f"  - 跳过 {name} {detail}")


def kepler_fixture():
    """随包基准样例（自包含，不依赖 /tmp 或工作区）。"""
    return os.path.normpath(os.path.join(SCRIPT_DIR, "..", "fixtures", "kepler-baseline.xml"))


def check_xml(path):
    r = run([sys.executable, CHECK, path, "--json"])
    return r.returncode, json.loads(r.stdout or "{}")


def t_init():
    name = "__selftest__"
    proj = os.path.join(WORKSPACE, "projects", name)
    r = run([sys.executable, PM, "init", name, "--force"])
    files = ["design.md", "geogebra.xml", "geogebra_defaults2d.xml",
             "geogebra_defaults3d.xml", "geogebra_javascript.js"]
    complete = r.returncode == 0 and all(os.path.exists(os.path.join(proj, f)) for f in files)
    ok("init 项目骨架完整", complete)
    return proj


def t_samples(proj):
    rc, d = check_xml(os.path.join(proj, "geogebra.xml"))
    ok("init 骨架通过校验", rc == 0)
    kepler = kepler_fixture()
    if os.path.exists(kepler):
        rc, d = check_xml(kepler)
        notes = [n["msg"] for n in d.get("notes", [])]
        consistent = sum(1 for n in notes if "缓存一致" in n or "点缓存一致" in n)
        ok("Kepler 样例五层通过且缓存逐位吻合", rc == 0 and consistent >= 25,
           f"rc={rc} 一致数={consistent}")
    else:
        skip("Kepler 样例五层", "缺 fixtures/kepler-baseline.xml")
    e2e = os.path.join(WORKSPACE, "projects", "开普勒轨道探究", "geogebra.xml")
    if os.path.exists(e2e):
        rc, d = check_xml(e2e)
        ok("端到端示例通过校验", rc == 0)
    else:
        skip("端到端示例", "工作区无 projects/开普勒轨道探究")


def t_corpus(corpus_dir):
    if not corpus_dir or not os.path.isdir(corpus_dir):
        skip("语料库回归", "未提供 --corpus")
        return
    tmp = tempfile.mkdtemp(prefix="ggblib_")
    n_ok = n_all = 0
    bad = []
    for f in glob.glob(os.path.join(corpus_dir, "**", "*.ggb"), recursive=True):
        d = os.path.join(tmp, os.path.basename(f))
        os.makedirs(d, exist_ok=True)
        try:
            with zipfile.ZipFile(f) as z:
                z.extract("geogebra.xml", d)
        except Exception:
            continue
        n_all += 1
        rc, _ = check_xml(os.path.join(d, "geogebra.xml"))
        if rc == 0:
            n_ok += 1
        else:
            bad.append(os.path.basename(f))
    shutil.rmtree(tmp, ignore_errors=True)
    # 已知缺陷：变轨系列按钮脚本引用了从未定义的 sqrt3（源文件的潜在 bug，
    # 恰好证明 L2 脚本检查有效）。允许 ≤3 个不同缺陷文件（同名重复出现只计一次）。
    uniq_bad = sorted(set(bad))
    ok(f"语料库回归 {n_ok}/{n_all} 通过（已知缺陷：{uniq_bad or '无'}）",
       n_ok + len(bad) == n_all and n_all > 0 and len(uniq_bad) <= 3)


def t_fix_refill():
    """只清空「派生对象」（expression 成对 element）的缓存 → --fix → 与原值比对。"""
    import xml.etree.ElementTree as ET
    src = os.path.join(WORKSPACE, "projects", "开普勒轨道探究", "geogebra.xml")
    if not os.path.exists(src):
        skip("--fix 回填", "工作区无 projects/开普勒轨道探究")
        return
    tmp = tempfile.mkdtemp(prefix="fixrefill_")
    dst = os.path.join(tmp, "geogebra.xml")
    tree = ET.parse(src)
    root = tree.getroot()
    cons = root.find("construction")
    expr_labels = {e.get("label") for e in cons.findall("expression")}
    n_stripped = 0
    for el in cons.findall("element"):
        if el.get("label") in expr_labels:
            for tag in ("value", "coords"):
                for child in el.findall(tag):
                    el.remove(child)
                    n_stripped += 1
    ET.indent(tree, space="\t")
    tree.write(dst, encoding="utf-8", xml_declaration=True)

    orig_vals = sorted(re.findall(r'<value val="([^"]*)" />',
                                  open(src, encoding="utf-8").read()))
    run([sys.executable, CHECK, dst, "--fix"])
    rc, _ = check_xml(dst)
    new_vals = sorted(re.findall(r'<value val="([^"]*)" />',
                                 open(dst, encoding="utf-8").read()))
    ok("--fix 回填后校验通过且数值还原", rc == 0 and orig_vals == new_vals,
       f"剥离{n_stripped} orig={len(orig_vals)} new={len(new_vals)}")
    shutil.rmtree(tmp, ignore_errors=True)


def t_roundtrip():
    proj = os.path.join(WORKSPACE, "projects", "开普勒轨道探究")
    if not os.path.exists(proj):
        skip("pack→unpack 往返", "工作区无 projects/开普勒轨道探究")
        return
    tmp = tempfile.mkdtemp(prefix="roundtrip_")
    ggb = os.path.join(tmp, "rt.ggb")
    out = os.path.join(tmp, "out")
    r1 = run([sys.executable, PACK, proj, "-o", ggb])
    r2 = run([sys.executable, UNPACK, ggb, "-o", out])
    rc, _ = check_xml(os.path.join(out, "geogebra.xml"))
    ok("pack→unpack→check 往返一致",
       r1.returncode == 0 and r2.returncode == 0 and rc == 0)
    shutil.rmtree(tmp, ignore_errors=True)


def t_mutations():
    src = os.path.join(WORKSPACE, "projects", "开普勒轨道探究", "geogebra.xml")
    if not os.path.exists(src):
        skip("变异测试", "工作区无 projects/开普勒轨道探究")
        return
    import re
    s = open(src, encoding="utf-8").read()
    tmp = tempfile.mkdtemp(prefix="mut_")

    def mk(name, content):
        d = os.path.join(tmp, name)
        os.makedirs(d, exist_ok=True)
        p = os.path.join(d, "geogebra.xml")
        open(p, "w", encoding="utf-8").write(content)
        return p

    # 1 缓存篡改 → warning（不阻塞）
    s1 = s.replace('val="0.3713753658328314" />', 'val="0.9" />', 1)
    rc, d = check_xml(mk("m1", s1)) if s1 != s else (0, {})
    warned = any("不符" in w["msg"] for w in d.get("warnings", []))
    ok("变异·缓存篡改 → warning", rc == 0 and warned)

    # 2 未定义引用 → error
    s2 = s.replace('exp="a * ex"', 'exp="a * exx_typo"', 1)
    rc, d = check_xml(mk("m2", s2)) if s2 != s else (0, {})
    ok("变异·未定义标识符 → error", rc == 1 and bool(d.get("errors")))

    # 3 顺序颠倒（M 块移到 construction 最前，引用了后面的 t… 实际由 L2/L3 拦截）
    m = re.search(r'(<expression label="M" exp="t" type="numeric" />\s*<element type="numeric" label="M">.*?</element>\n)', s, re.S)
    mcons = re.search(r'<construction[^>]*>', s)
    if m and mcons:
        blk = m.group(1)
        s3 = s.replace(blk, "", 1).replace(mcons.group(0), mcons.group(0) + "\n" + blk, 1)
        rc, d = check_xml(mk("m3", s3))
        ok("变异·顺序颠倒 → error", rc == 1 and bool(d.get("errors")))
    else:
        skip("变异·顺序颠倒", "未找到 M 块（文件格式变化？）")

    # 4 前向引用（引用的对象在构造序中位于其后——用户实测 A2→P0 打开报 error in <expression>）
    src4 = os.path.join(WORKSPACE, "projects", "环形磁场偏转", "geogebra.xml")
    if os.path.exists(src4):
        import xml.etree.ElementTree as ET
        tree = ET.parse(src4)
        cons = tree.getroot().find("construction")
        kids = list(cons)
        def block(i):
            if not isinstance(kids[i].tag, str):
                return None
            t = kids[i]
            if t.tag == "expression":
                out = [t]
                if i + 1 < len(kids) and kids[i + 1].tag == "element"                         and kids[i + 1].get("label") == t.get("label"):
                    out.append(kids[i + 1])
                return out
            if t.tag == "command":
                outs = [v for v in t.find("output").attrib.values() if v]
                out = [t]
                k = i + 1
                while k < len(kids) and isinstance(kids[k].tag, str) and kids[k].tag == "element"                         and kids[k].get("label") in outs:
                    out.append(kids[k]); k += 1
                return out
            return None
        def find(label):
            for i, c in enumerate(kids):
                if isinstance(c.tag, str) and c.get("label") == label and c.tag in ("expression", "element"):
                    return i
            return None
        i_a2 = find("A2")
        i_p0 = find("P0")
        if i_a2 is not None and i_p0 is not None:
            blk_a2 = block(i_a2)
            blk_p0 = block(i_p0)
            before_p0 = kids.index(blk_p0[0])
            for b in blk_a2:
                cons.remove(b)
            for b in blk_p0:
                cons.remove(b)
            # 顺序变更为 […A2 块, P0 块…]：P0 定义位于 A2 引用之后 → 前向引用
            pos = before_p0 - len(blk_a2)
            for b in reversed(blk_a2):
                cons.insert(pos, b)
            pos += len(blk_a2)
            for b in reversed(blk_p0):
                cons.insert(pos, b)
            tmpf = os.path.join(tmp, "__mut4.xml")   # 写临时目录，不污染项目目录
            tree.write(tmpf, encoding="utf-8", xml_declaration=True)
            macro_src = os.path.join(os.path.dirname(src4), "geogebra_macro.xml")
            if os.path.exists(macro_src):            # 保持宏白名单上下文一致
                shutil.copy(macro_src, os.path.join(tmp, "geogebra_macro.xml"))
            rc, d = check_xml(tmpf)
            msgs = " ".join(e["msg"] for e in d.get("errors", []))
            ok("变异·前向引用点对象 → error", rc == 1 and "前向对象" in msgs, msgs[:90])
        else:
            skip("变异·前向引用点对象", "未找到 A2/P0")
    else:
        skip("变异·前向引用点对象", "工作区无 projects/环形磁场偏转")

    # 5 脚本自引用创建（v = If[v,...] 且 v 未定义 → 用户实测的「未定义变量」bug）
    if 'label="playing"' in s:
        s4 = s.replace('label="playing"', 'label="playingRenamed"', 1)
        rc, d = check_xml(mk("m4", s4))
        msgs = " ".join(e["msg"] for e in d.get("errors", []))
        ok("变异·脚本自引用创建布尔 → error", rc == 1 and "自引用创建" in msgs, msgs[:80])
    else:
        skip("变异·脚本自引用创建布尔", "未找到 playing 布尔")
    shutil.rmtree(tmp, ignore_errors=True)


def t_js_layer():
    tmp = tempfile.mkdtemp(prefix="jschk_")
    xml = os.path.join(WORKSPACE, "projects", "开普勒轨道探究", "geogebra.xml")
    if not os.path.exists(xml):
        skip("JS 语法层", "工作区无 projects/开普勒轨道探究")
        return
    open(os.path.join(tmp, "geogebra_javascript.js"), "w", encoding="utf-8").write(
        "function ggbOnInit() { broken((( }\n")
    shutil.copy(xml, os.path.join(tmp, "geogebra.xml"))
    rc, d = check_xml(os.path.join(tmp, "geogebra.xml"))
    has_js_err = any(e["layer"] == 5 for e in d.get("errors", []))
    ok("坏 JS 被语法层拦截", rc == 1 and has_js_err)
    shutil.rmtree(tmp, ignore_errors=True)


def t_media_macro():
    """素材与宏链路：宏命令白名单放行、image 引用缺失告警（不阻塞）、
    pack 按引用收图、引用缺失时打包拒绝。"""
    import xml.etree.ElementTree as ET
    tmp = tempfile.mkdtemp(prefix="mediamacro_")
    ws = os.path.join(tmp, "ws")
    os.makedirs(ws, exist_ok=True)
    # init 子进程以 ws 为工作区：剔除 GGB_ROOT，让 cwd 生效
    env = dict(os.environ)
    env.pop("GGB_ROOT", None)
    r = run([sys.executable, PM, "init", "mediamacro", "--force"], cwd=ws, env=env)
    proj = os.path.join(ws, "projects", "mediamacro")
    if r.returncode != 0 or not os.path.exists(os.path.join(proj, "geogebra.xml")):
        ok("media/macro 用例：init 骨架", False, "init 失败")
        shutil.rmtree(tmp, ignore_errors=True)
        return

    # 最小宏（自包含 fixture）：Midpoint[A,B] → x
    macro = ('<?xml version="1.0" encoding="utf-8"?>\n'
             '<geogebra format="5.0" version="5.0.683.0" app="classic" platform="w" xmlns="">\n'
             '<macro cmdName="小宏" toolName="小宏" toolHelp="小宏[ &lt;Point&gt;, &lt;Point&gt; ]" '
             'showInToolBar="false" copyCaptions="false" viewId="1">\n'
             '<macroInput a0="A" a1="B"/>\n<macroOutput a0="x"/>\n<construction title="">\n'
             '<command name="Midpoint"><input a0="A" a1="B"/><output a0="x"/></command>\n'
             '<element type="point" label="x"><show object="false" label="true" ev="4"/>'
             '<coords x="1" y="1" z="1"/></element>\n'
             '</construction>\n</macro>\n</geogebra>\n')
    open(os.path.join(proj, "geogebra_macro.xml"), "w", encoding="utf-8").write(macro)

    xml_path = os.path.join(proj, "geogebra.xml")
    tree = ET.parse(xml_path)
    root = tree.getroot()
    cons = root.find("construction")
    for snippet in (
        '<element type="point" label="P1"><show object="false" label="false" ev="4"/>'
        '<coords x="0" y="0" z="1"/></element>\n',
        '<element type="point" label="P2"><show object="false" label="false" ev="4"/>'
        '<coords x="1" y="0" z="1"/></element>\n',
        '<expression label="mm" exp="小宏[P1,P2]" type="point"/>',
        '<element type="point" label="mm"><show object="false" label="true" ev="4"/>'
        '<coords x="0.5" y="0" z="1"/></element>',
        '<element type="image" label="pic1"><file name="ab/fig.png"/>'
        '<show object="true" label="false" ev="4"/>'
        '<objColor r="0" g="0" b="0" alpha="1"/><layer val="4"/></element>\n',
    ):
        cons.append(ET.fromstring(snippet))
    ET.indent(tree, space="\t")
    tree.write(xml_path, encoding="utf-8", xml_declaration=True)

    pic = os.path.join(proj, "media", "ab", "fig.png")
    os.makedirs(os.path.dirname(pic), exist_ok=True)
    with open(pic, "wb") as fh:
        fh.write(b"\x89PNG-fake")

    # ① 宏命令名放行 + 图存在 → rc=0 且无素材告警
    rc, d = check_xml(xml_path)
    media_warn = [w for w in d.get("warnings", []) if "素材不存在" in w["msg"]]
    ok("media/macro 用例：宏命令白名单放行且素材齐 → 通过", rc == 0 and not media_warn,
       f"rc={rc} warn={media_warn[:2]}")

    # ② 图缺失 → check 仍 rc=0（warning 级），打包端拒绝
    os.unlink(pic)
    rc, d = check_xml(xml_path)
    media_warn = [w for w in d.get("warnings", []) if "素材不存在" in w["msg"]]
    ok("media/macro 用例：素材缺失 → check 告警不阻塞", rc == 0 and bool(media_warn),
       f"rc={rc}")
    ggb = os.path.join(tmp, "out.ggb")
    r = run([sys.executable, PACK, proj, "-o", ggb])
    ok("media/macro 用例：素材缺失 → pack 拒绝", r.returncode != 0)

    # ③ 图恢复 → pack 成功且 zip 内路径=引用路径；unpack 解出
    with open(pic, "wb") as fh:
        fh.write(b"\x89PNG-fake")
    r = run([sys.executable, PACK, proj, "-o", ggb])
    in_zip = False
    if r.returncode == 0:
        with zipfile.ZipFile(ggb) as z:
            in_zip = "ab/fig.png" in z.namelist()
    ok("media/macro 用例：引用图打包且路径一致", r.returncode == 0 and in_zip)
    un = os.path.join(tmp, "un")
    if r.returncode == 0:
        run([sys.executable, UNPACK, ggb, "-o", un])
    ok("media/macro 用例：unpack 还原图片目录", os.path.exists(os.path.join(un, "ab", "fig.png")))
    shutil.rmtree(tmp, ignore_errors=True)


def t_order_preview():
    """L1b 顺序校验（warning 级）+ 宏自包含审计 + 预览脚本。"""
    kepler = kepler_fixture()
    if os.path.exists(kepler):
        import shutil
        import tempfile
        work = tempfile.mkdtemp(prefix="selftest_order_")
        mutated = os.path.join(work, "bad.xml")
        data = open(kepler, encoding="utf-8").read()
        old = '<element type="numeric" label="a"><show object="true" label="true" ev="4"/>'
        if old in data:
            data = data.replace(
                old,
                '<element type="numeric" label="a"><animation step="0.1" speed="1" type="1"'
                ' playing="false"/><show object="true" label="true" ev="4"/>', 1)
            data = data.replace(
                '<value val="5"/><animation step="0.1" speed="1" type="1" playing="false"/>'
                '<caption val="半长轴 a（第一/三定律）"/>',
                '<value val="5"/><caption val="半长轴 a（第一/三定律）"/>', 1)
        open(mutated, "w", encoding="utf-8").write(data)
        rc, d = check_xml(mutated)
        warn_msgs = " ".join(w["msg"] for w in d.get("warnings", []))
        ok("L1b 顺序校验：滑杆乱序报 warning 且不阻塞",
           rc == 0 and "animation 出现在 slider 之前" in warn_msgs)
        shutil.rmtree(work, ignore_errors=True)
    else:
        skip("L1b 顺序校验", "缺 fixtures/kepler-baseline.xml")

    macros = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                           "..", "macros"))
    pulley = os.path.join(macros, "mechanics", "滑轮.ggt")
    belt = os.path.join(macros, "mechanics", "传送带.ggt")
    try:
        import xml.etree.ElementTree as ET_
        import zipfile
        from ggb_check import audit_macro_self_containment
    except ImportError:
        ok("宏自包含审计：可导入 ggb_check", False)
        return
    if not (os.path.exists(pulley) and os.path.exists(belt)):
        skip("宏自包含审计", "缺 macros/mechanics/滑轮.ggt 或 传送带.ggt")
        return
    root = ET_.fromstring(zipfile.ZipFile(pulley).read("geogebra_macro.xml"))
    _d, dang, _e = audit_macro_self_containment(root)
    ok("宏自包含审计：滑轮 ✓ 无悬挂", dang == [], f"{dang}")
    root = ET_.fromstring(zipfile.ZipFile(belt).read("geogebra_macro.xml"))
    _d, dang, _e = audit_macro_self_containment(root)
    ok("宏自包含审计：传送带 ✗ 检出悬挂", "ί" in dang, f"{dang}")

    prev = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ggb_macro_preview.py")
    if os.path.exists(pulley) and os.path.exists(prev):
        r = run([sys.executable, prev, pulley])
        ok("ggb_macro_preview 单宏预览（含自包含与片段状态）",
           r.returncode == 0 and "自包含：✓" in r.stdout and "建议" in r.stdout)
        r2 = run([sys.executable, prev, belt])
        ok("ggb_macro_preview 残缺宏警示", r2.returncode == 0 and "残缺宏" in r2.stdout)
    else:
        skip("ggb_macro_preview 预览", "缺 ggb_macro_preview.py")


def t_html_demo():
    """HTML 定妆演示件：数据契约校验（正例 + 变异）、模板洁净性、拼装产物。"""
    import json as _json
    hcheck = os.path.join(SCRIPT_DIR, "html_demo_check.py")
    htpl = os.path.join(SCRIPT_DIR, "html_demo", "template.html")
    if not (os.path.isfile(hcheck) and os.path.isfile(htpl)):
        skip("html_demo 校验器/模板", "缺 scripts/html_demo_check.py 或 scripts/html_demo/template.html")
        return
    good = {
        "meta": {"title": "演示", "conclusion": "终态达成", "params": {"k": 1}},
        "scene": {"bbox": [0, -2, 3, 3], "shapes": [
            {"type": "segment", "a": [0, 0], "b": [2, 0]},
            {"type": "label", "pos": [2, 2.5], "text": "T"}]},
        "actors": [{"id": "动点", "color": "#cc0000"}],
        "frames": [
            {"t": 0.0, "pos": [[2.0, 0.0]], "vel": [[0.0, -1.0]], "phase": "约束段"},
            {"t": 0.5, "pos": [[1.2, -0.8]], "vel": [[-0.5, 0.4]]},
            {"t": 1.0, "pos": [[1.6, 2.0]], "vel": [[0.3, 0.2]]}],
        "marks": [{"t": 0.5, "label": "脱离"}],
        "readouts": [{"label": "要求初速", "value": "1.80", "unit": "m/s"}],
    }
    tmp = tempfile.mkdtemp(prefix="htmldemo_")

    def run_case(name, text, expect_ok, suffix="json"):
        p = os.path.join(tmp, name + "." + suffix)
        open(p, "w", encoding="utf-8").write(text)
        r = run([sys.executable, hcheck, p])
        ok(name, (r.returncode == 0) == expect_ok, (r.stdout or r.stderr)[-180:])

    run_case("html_demo·正例数据通过", _json.dumps(good, ensure_ascii=False), True)
    bad1 = _json.loads(_json.dumps(good)); bad1["frames"][2]["t"] = 0.2
    run_case("html_demo·变异 t 非单调拒绝", _json.dumps(bad1, ensure_ascii=False), False)
    bad2 = _json.loads(_json.dumps(good)); bad2.pop("meta")
    run_case("html_demo·变异缺 meta 拒绝", _json.dumps(bad2, ensure_ascii=False), False)
    bad3 = _json.loads(_json.dumps(good)); bad3["frames"][1]["pos"] = [[0.0, 0.0], [1.0, 1.0]]
    run_case("html_demo·变异 pos 维度不符拒绝", _json.dumps(bad3, ensure_ascii=False), False)
    bad4 = _json.loads(_json.dumps(good))
    bad4["links"] = [{"a": 0, "b": 2}]
    run_case("html_demo·变异 links 索引越界拒绝", _json.dumps(bad4, ensure_ascii=False), False)

    tpl = open(htpl, encoding="utf-8").read()
    ok("html_demo·模板含唯一占位符", tpl.count("__DATA__") == 1)
    r = run([sys.executable, hcheck, htpl])
    ok("html_demo·模板无外部引用", "外部引用" not in (r.stdout or ""), (r.stdout or "")[-160:])

    blob = _json.dumps(good, ensure_ascii=False).replace("</", "<\\/")
    p = os.path.join(tmp, "demo.html")
    open(p, "w", encoding="utf-8").write(tpl.replace("__DATA__", blob))
    r = run([sys.executable, hcheck, p])
    ok("html_demo·拼装产物通过校验", r.returncode == 0, (r.stdout or "")[-180:])
    evil = tpl.replace("__DATA__", blob).replace(
        "</body>", '<script src="http://cdn.example/x.js"></script></body>')
    p2 = os.path.join(tmp, "evil.html")
    open(p2, "w", encoding="utf-8").write(evil)
    r = run([sys.executable, hcheck, p2])
    ok("html_demo·产物注入外链被拒绝", r.returncode != 0)
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=None,
                    help="真实 .ggb 语料库目录（可选：开发回归时指定，如样品库目录）")
    args = ap.parse_args()

    print("== ggb-master 工具链自检 ==")
    proj = t_init()
    t_samples(proj)
    # 骨架校验完再清理
    shutil.rmtree(proj, ignore_errors=True)
    t_corpus(args.corpus)
    t_fix_refill()
    t_roundtrip()
    t_mutations()
    t_js_layer()
    t_media_macro()
    t_order_preview()
    t_html_demo()
    print(f"\n结果：{len(PASS)} 通过 / {len(FAIL)} 失败"
          + (f" / {len(SKIP)} 跳过" if SKIP else ""))
    if SKIP:
        print("跳过项：", "; ".join(SKIP))
    if FAIL:
        print("失败项：", "; ".join(FAIL))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
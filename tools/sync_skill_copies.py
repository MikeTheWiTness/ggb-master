#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""sync_skill_copies.py —— 开发仓库 skills/ggb-master → 安装副本 / 随包副本同步。

ADR-0005：skill 为自包含分发单元，改动后必须同步所有副本。本脚本：

- 把开发源码逐文件复制（覆盖）到各副本（默认随包副本
  packages/dsh-ggb-master/skills/ggb-master，以及安装副本 ~/.zcode/skills/ggb-master 与
  ~/.workbuddy/skills/ggb-master；--targets 可换）；
- 不删除副本里多余的文件，只报告（防误删本地定制）；
- workbuddy 副本做路径定制：文件内 `~/.zcode/skills/ggb-master` →
  `~/.workbuddy/skills/ggb-master`（SKILL.md 里的脚本路径约定）；
- 排除 .DS_Store / __pycache__ / *.pyc；
- 结束自动 diff 自证：剩余差异应只有 workbuddy 的路径定制。

用法：
  python3 tools/sync_skill_copies.py            # 同步随包副本 + 两个安装副本
  python3 tools/sync_skill_copies.py --dry-run  # 只打印将复制的文件
  python3 tools/sync_skill_copies.py --targets ~/custom/skills/ggb-master
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys

REPO_DIR = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DEV_DIR = os.path.join(REPO_DIR, "skills", "ggb-master")
BUNDLE_DIR = os.path.join(REPO_DIR, "packages", "dsh-ggb-master", "skills", "ggb-master")
EXCLUDE = (".DS_Store", "__pycache__", ".pyc")
PATH_MARK = "~/.zcode/skills/ggb-master"          # 文件中出现的路径约定
PATH_SUB = "~/.workbuddy/skills/ggb-master"       # workbuddy 定制的替换值


def walk_files(root: str):
    for dp, _dn, fn in os.walk(root):
        for f in sorted(fn):
            if any(x in f for x in EXCLUDE) or f.endswith(".pyc"):
                continue
            yield os.path.join(dp, f)


def rel_of(path: str) -> str:
    return os.path.relpath(path, DEV_DIR)


def sync_to(target: str, install_paths: bool, dry_run: bool):
    print(f"== 同步 → {target}")
    copied = 0
    for src in walk_files(DEV_DIR):
        rel = rel_of(src)
        dst = os.path.join(target, rel)
        if dry_run:
            print(f"  将复制 {rel}")
            copied += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if install_paths:
            with open(src, encoding="utf-8", errors="replace") as f:
                data = f.read()
            if PATH_MARK in data:
                data = data.replace(PATH_MARK, PATH_SUB)
                with open(dst, "w", encoding="utf-8") as f:
                    f.write(data)
                print(f"  {rel}（路径已定制 → {PATH_SUB}）")
            else:
                shutil.copy2(src, dst)
        else:
            shutil.copy2(src, dst)
        copied += 1
    print(f"  复制 {copied} 个文件")
    # 报告安装副本里的多余文件（不删除）
    extra = []
    if os.path.isdir(target):
        for src in walk_files(target):
            rel = rel_of(src)
            if not os.path.exists(os.path.join(DEV_DIR, rel)):
                extra.append(rel)
    if extra:
        print(f"  ⚠ 副本有 {len(extra)} 个源中没有的文件（未删除，人工确认）：")
        for e in extra:
            print(f"    {e}")

    # diff 自证
    if not dry_run:
        r = subprocess.run(["diff", "-rq", DEV_DIR, target],
                           capture_output=True, text=True)
        out = [ln for ln in r.stdout.splitlines()
               if not any(x in ln for x in (".DS_Store", "__pycache__"))]
        if out:
            print(f"  diff 剩余差异 {len(out)} 行（应为路径定制类）：")
            for ln in out[:12]:
                print(f"    {ln}")
        else:
            print("  diff 自证：无差异 ✓")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sync_skill_copies.py",
                                 description="ggb-master 开发源码 → 随包副本 / 安装副本同步（ADR-0005）")
    ap.add_argument("--targets",
                    default=f"~/.zcode/skills/ggb-master,~/.workbuddy/skills/ggb-master,{BUNDLE_DIR}",
                    help="逗号分隔的副本路径（默认：两个安装副本 + DSH 插件包随包副本）")
    ap.add_argument("--no-path-replace", action="store_true",
                    help="不执行 workbuddy 路径定制（所有副本原样复制）")
    ap.add_argument("--dry-run", action="store_true", help="只打印计划")
    args = ap.parse_args(argv)

    if not os.path.isdir(DEV_DIR):
        print(f"错误：找不到开发源码 {DEV_DIR}", file=sys.stderr)
        return 2

    targets = [os.path.expanduser(t.strip()) for t in args.targets.split(",") if t.strip()]
    if not targets:
        print("错误：--targets 为空", file=sys.stderr)
        return 2

    for t in targets:
        # 路径定制按目标路径内容判断：workbuddy 副本才替换，与 --targets 顺序无关
        customize = (not args.no_path_replace) and ("workbuddy" in t)
        sync_to(t, install_paths=customize, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
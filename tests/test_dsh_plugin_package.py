"""dsh-ggb-master 插件包的打包契约测试。

只锁定「随包产物彼此一致、且是 DSH 能读的形态」，不验证宿主运行行为
（安装与实际会话需要真实 DSH profile，见 packages/dsh-ggb-master/host-probe/README.md）。
YAML 用例需要 pyyaml；脚本冒烟用例用当前解释器。
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
PKG = ROOT / "packages" / "dsh-ggb-master"
SKILL_SRC = ROOT / "skills" / "ggb-master"
SKILL_PKG = PKG / "skills" / "ggb-master"
SCRIPTS = SKILL_PKG / "scripts"


class _Loader(yaml.SafeLoader):
    """保留 !!js 表达式原文——这里只做结构检查，不求值。"""


def _js(loader: yaml.SafeLoader, node: yaml.Node) -> str:
    return loader.construct_scalar(node)  # type: ignore[arg-type]


_Loader.add_constructor("tag:yaml.org,2002:js", _js)
_Loader.add_constructor("!js", _js)


def _load_patch() -> list:
    with (PKG / "cordis.patch.yml").open(encoding="utf-8") as fh:
        return yaml.load(fh, Loader=_Loader)


def _preset_config() -> dict:
    rows = _load_patch()[0]["insert"]
    row = next(r for r in rows if r["id"] == "preset-ggb-master")
    return row["config"]


def _preset_plugins() -> dict:
    return {p["id"]: p for p in _preset_config()["plugins"]}


def test_manifest_declares_bundle_plugin_and_display_metadata():
    manifest = json.loads((PKG / "package.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "dsh-ggb-master"
    assert manifest["type"] == "module"
    assert manifest["dsh"]["bundle"]["patch"] == "./cordis.patch.yml"
    assert (PKG / manifest["dsh"]["bundle"]["patch"]).is_file()
    # 同名包既要能被相对路径挂载，也要能按包名解析（自引用 package.json）
    assert manifest["exports"]["."] == "./tools/index.js"
    assert manifest["exports"]["./package.json"] == "./package.json"
    assert manifest["icon"].startswith("./")
    assert (PKG / "locale" / "zh.json").is_file()
    assert (PKG / "locale" / "en.json").is_file()
    for locale in ("zh", "en"):
        meta = json.loads((PKG / "locale" / f"{locale}.json").read_text(encoding="utf-8"))["meta"]
        assert meta["title"].strip() and meta["description"].strip()


def test_preset_declares_ggb_master_with_full_agent_capabilities():
    config = _preset_config()
    assert config["id"] == "ggb-master"
    assert config["name"] == "GGB 课件"
    assert isinstance(config["order"], int)
    assert config["description"].strip()
    plugins = _preset_plugins()
    # 预设必须自带完整 plugins 列表（DSH 不提供继承）：抽查核心能力仍在
    for required in ("persona", "tool-bash", "tool-fs", "tool-skill", "tool-todo", "tool-web"):
        assert required in plugins, f"preset 缺少公共能力：{required}"
    assert "tool-subagent" in {p["id"] for p in plugins["delegation"]["config"]}


def test_preset_mounts_bundled_skill_dir_and_native_tool():
    plugins = _preset_plugins()
    dirs = plugins["skill-filesystem"]["config"]["customSkillDirs"]
    assert len(dirs) == 1
    assert "'skills'" in dirs[0] and "baseUrl" in dirs[0]
    assert "resolve('dsh-ggb-master/package.json')" in dirs[0]
    assert plugins["ggb-tools"]["name"] == "dsh-ggb-master"
    assert plugins["ggb-tools"]["config"]["timeoutMs"] > 0


def test_native_tool_module_is_dependency_free_and_wired():
    source = (PKG / "tools" / "index.js").read_text(encoding="utf-8")
    assert "export function apply" in source
    assert "export const inject" in source
    assert "ctx.tools.register" in source
    assert "ctx.subprocess.spawn" in source
    # 只用 Node 内建模块：profile 里解析不到随 DSH 安装的 @deepseek-ai/* 包
    assert 'from "@deepseek-ai/' not in source
    assert "from '@deepseek-ai/" not in source
    assert 'import("@deepseek-ai/' not in source
    # 路径约定：会话工作区同时进 cwd 与 GGB_ROOT
    assert "GGB_ROOT" in source


def test_native_tool_subcommands_all_resolve_to_bundled_scripts():
    source = (PKG / "tools" / "index.js").read_text(encoding="utf-8")
    block = source.split("const COMMANDS = {", 1)[1].split("}", 1)[0]
    mapping = dict(re.findall(r"['\"]?([\w-]+)['\"]?:\s*'([^']+\.py)'", block))
    # SKILL.md 里点名的工具必须都在
    assert set(mapping) >= {
        "init", "check", "pack", "unpack", "macro-preview", "html-demo-check", "selftest",
    }
    for sub, script in mapping.items():
        assert (SCRIPTS / script).is_file(), f"子命令 {sub} 指向的随包脚本不存在：{script}"


def test_bundled_check_tool_passes_on_bundled_fixture():
    """零素材冒烟：随包基准样例必须过五层质量门。"""
    fixture = SKILL_PKG / "fixtures" / "kepler-baseline.xml"
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "ggb_check.py"), str(fixture), "--quiet"],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK" in result.stdout


def test_skill_frontmatter_is_discoverable():
    text = (SKILL_PKG / "SKILL.md").read_text(encoding="utf-8")
    assert text.startswith("---")
    assert "\nname: ggb-master\n" in text
    assert "\ndescription:" in text


def _skill_files(root: Path) -> set[str]:
    """比较交付文件，排除 Finder 元数据与 Python 字节码缓存。"""
    return {
        str(p.relative_to(root))
        for p in root.rglob("*")
        if p.is_file() and p.name != ".DS_Store" and "__pycache__" not in p.parts
    }


def test_bundled_skill_has_no_extra_files():
    assert _skill_files(SKILL_PKG) == _skill_files(SKILL_SRC)


@pytest.mark.parametrize("relative", sorted(_skill_files(SKILL_SRC)))
def test_bundled_skill_matches_repo_source(relative: str):
    src = (SKILL_SRC / relative).read_bytes()
    dst = (SKILL_PKG / relative).read_bytes()
    assert src == dst, f"随包 skill 与仓库 skills/ggb-master 不一致：{relative}；请跑 tools/sync_skill_copies.py，勿手改"


def test_sync_script_keeps_bundle_copy_in_default_targets():
    source = (ROOT / "tools" / "sync_skill_copies.py").read_text(encoding="utf-8")
    assert 'BUNDLE_DIR = os.path.join(REPO_DIR, "packages", "dsh-ggb-master", "skills", "ggb-master")' in source
    assert "{BUNDLE_DIR}" in source

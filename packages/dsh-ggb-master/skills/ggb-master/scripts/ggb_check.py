#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ggb_check.py —— ggb-master 五层校验（质量门）。

五层职责（construction-language.md；症状→处置速查见 failure-recovery.md §1）：
  1 结构合法：XML 可解析、顶层结构、construction 内元素形态。
  2 引用一致：label 唯一、expression/command 引用对象已定义。
  3 依赖拓扑：无循环、无先用后定义。
  4 数值重算：内置求值器（常见函数子集）重算并校验/填充缓存值。
  5 JS 语法：geogebra_javascript.js 用 node --check 检查。

用法：
  python3 ggb_check.py <geogebra.xml> [--fix] [--json] [--quiet]

退出码：0=通过（警告不影响） 1=失败 2=用法/IO 错误。
--fix  五层全部 0 error 时，把可计算的缓存值缺失/不符写入修正（<value>/<coords>）。
"""
from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------- 常量

def _arr(P):
    if isinstance(P, tuple):
        return P
    return (P, 0)


FUNCTION_SUBSET = {
    # (函数名, 元数, 实现)
    "sqrt": (1, lambda x: math.sqrt(x)),
    "abs": (1, abs),
    "min": (2, min),
    "max": (2, max),
    "sin": (1, lambda x: math.sin(x)),
    "cos": (1, lambda x: math.cos(x)),
    "tan": (1, lambda x: math.tan(x)),
    "asin": (1, lambda x: math.asin(x)),
    "acos": (1, lambda x: math.acos(x)),
    "atan": (1, lambda x: math.atan(x)),
    "ln": (1, math.log),
    "log": (1, lambda x: math.log10(x)),
    "exp": (1, math.exp),
    "floor": (1, math.floor),
    "ceil": (1, math.ceil),
    "round": (1, round),
    "sign": (1, lambda x: float((x > 0) - (x < 0))),
    "deg": (1, lambda x: math.radians(x)),
    "atan2": (2, math.atan2),
    "Mod": (2, lambda a, b: a - b * math.floor(a / b)),
    "x": (1, lambda P: P[0] if isinstance(P, tuple) else _arr(P)[0]),
    "y": (1, lambda P: P[1] if isinstance(P, tuple) else _arr(P)[1]),
    "If": (3, lambda c, a, b: a if c else b),
    "if": (3, lambda c, a, b: a if c else b),
}
CONSTANTS = {
    "pi": math.pi,
    "pi_": math.pi,
    "π": math.pi,
    "e": math.e,
    "true": True,
    "false": False,
}

# GeoGebra 常见命令/几何函数名（引用提取时放行，不做未定义引用报警）
KNOWN_COMMANDS = set("""
Area Distance Length Midpoint Slope Segment Line Ray Vector Polygon Circle Ellipse
Hyperbola Parabola Conic Function Curve Locus Intersect Point Vertex Focus Radius
Tangent Diameter Angle Sector Arc Textfield Sum Product Sequence Random Between AngleBisector
SetValue StartAnimation SetCaption SetVisibleInView SetColor SetTrace SetLineThickness
SetPointSize CenterView ZoomIn ZoomOut Execute RunClickScript ShowLayer HideLayer
Pan SetActiveView If if Degree Distance ABS abs sqrt sin cos tan sqrtPI Root
Min Max Average Median Mean ExtremePoint Corner CornerSurroundings X Y RootList
ConvexHull CircumcircularArc CircumcircleSector SemiCircumference Enlarge Dilate
Translate Rotate Reflect Stretch Shear AffineMap Image Slider Checkbox Button
Text Zip UnitVector CurVec UnitPerpendicularVector UnitOrthogonalVector
IterationList Iteration CurveCartesian Surface OrthogonalLine OrthogonalVector
CircleArc CircleSector CircumcircleArc CircumcircleSector Semicircle
RandomElement Element Take Append Join Flatten Unique Sort Reverse Insert Remove
LaTeX Name Numerator Denominator Derivative Integral Sum If
asind acosd atand sgn cbrt Mod mod
Div PointIn LineBisector Direction Cross Dot Mirror arg
cosh sinh nCr KeepIf LeftSide RightSide Center Polyline PointOn
""".split())

CONSTANTS |= {"ℯ": math.e}

# 函数自变量白名单（f(x)= 里的 x 等，不当作对象引用）
FREE_VARS = {"x", "y", "z", "u", "v", "w", "r", "θ"}

# GeoGebra 内置对象（轴线/坐标面等），非 construction 定义，引用检查放行
BUILTIN_OBJS = {"xAxis", "yAxis", "zAxis", "xOyPlane", "xOzPlane", "yOzPlane"}


class Issue:
    def __init__(self, layer: int, level: str, msg: str, where: str = ""):
        self.layer = layer
        self.level = level          # error | warning | note
        self.msg = msg
        self.where = where

    def to_dict(self):
        return {"layer": self.layer, "level": self.level, "where": self.where, "msg": self.msg}

    def __str__(self):
        loc = f"[{self.where}] " if self.where else ""
        return f"L{self.layer} {self.level.upper():7s} {loc}{self.msg}"


# ---------------------------------------------------------------- 表达式求值器（第四层用）

class EvalError(Exception):
    pass


class _Tokenizer:
    def __init__(self, s: str):
        self.s = s
        self.i = 0
        self.n = len(s)

    def tokens(self):
        out = []
        while self.i < self.n:
            c = self.s[self.i]
            if c.isspace():
                self.i += 1
                continue
            # 数字
            if c.isdigit() or (c == "." and self.i + 1 < self.n and self.s[self.i + 1].isdigit()):
                j = self.i
                while j < self.n and (self.s[j].isdigit() or self.s[j] == "."):
                    j += 1
                # 指数（仅当 e 后跟数字或 +/-数字，避免吃掉常量 e）
                if j < self.n and self.s[j] in "eE":
                    k = j + 1
                    if k < self.n and self.s[k] in "+-":
                        k += 1
                    if k < self.n and self.s[k].isdigit():
                        while k < self.n and (self.s[k].isdigit() or self.s[k] == "."):
                            k += 1
                        j = k
                out.append(("NUM", self.s[self.i:j]))
                self.i = j
                continue
            # 字符串
            if c == '"':
                j = self.i + 1
                while j < self.n and self.s[j] != '"':
                    j += 1
                if j >= self.n:
                    raise EvalError("字符串未闭合")
                out.append(("STR", self.s[self.i + 1:j]))
                self.i = j + 1
                continue
            # 多字符运算符
            two = self.s[self.i:self.i + 2]
            if two in ("==", "!=", "<=", ">=", "&&", "||"):
                out.append(("OP", two))
                self.i += 2
                continue
            # 单字符
            if c in "+-*/^(),<>=!°∧∨¬≤≥≠":
                out.append(("OP", c))
                self.i += 1
                continue
            # 标识符
            if c.isalpha() or c == "_" or ord(c) > 127:
                j = self.i
                while j < self.n and (self.s[j].isalnum() or self.s[j] == "_" or ord(self.s[j]) > 127):
                    j += 1
                out.append(("ID", self.s[self.i:j]))
                self.i = j
                continue
            raise EvalError(f"无法识别的字符 {c!r} @{self.i}")
        out.append(("END", ""))
        return out


class Evaluator:
    """GeoGebra 表达式求值子集。支持四则/幂/比较/逻辑/If 与 FUNCTION_SUBSET。
    三角函数恒按弧度（与 GeoGebra 对裸数字的行为一致，见 construction-language.md §10 坑3）。
    """

    def __init__(self, env: dict):
        self.env = env          # label -> 数值/布尔

    def eval(self, expr: str):
        toks = _Tokenizer(expr).tokens()
        self.toks = toks
        self.pos = 0
        v = self._expr()
        if self._cur()[0] != "END":
            raise EvalError(f"多余内容：{self._cur()}")
        return v

    def _cur(self):
        return self.toks[self.pos]

    def _adv(self):
        t = self.toks[self.pos]
        self.pos += 1
        return t

    def _accept(self, op):
        if self._cur()[0] == "OP" and self._cur()[1] == op:
            self.pos += 1
            return True
        return False

    def _skip_expr(self):
        """不吃掉一个完整表达式（停在顶层逗号/右括号），不求值——惰性 If 的未选中分支。"""
        depth = 0
        while True:
            t = self._cur()
            if t[0] == "END":
                raise EvalError("If 分支未闭合")
            if t[0] == "OP" and t[1] == "(":
                depth += 1
            elif t[0] == "OP" and t[1] == ")":
                if depth == 0:
                    return
                depth -= 1
            elif t[0] == "OP" and t[1] == "," and depth == 0:
                return
            self._adv()

    def _expect(self, op):
        if not self._accept(op):
            raise EvalError(f"期望 {op!r}，实际 {self._cur()!r}")

    def _expr(self):
        return self._or()

    def _or(self):
        v = self._and()
        while True:
            t = self._cur()
            if t[0] == "OP" and t[1] in ("∨", "||") or (t[0] == "ID" and t[1] in ("or", "OR")):
                self._adv()
                r = self._and()
                v = _truthy(v) or _truthy(r)
            elif t[0] == "ID" and t[1] == "or":
                self._adv()
                r = self._and()
                v = _truthy(v) or _truthy(r)
            else:
                break
        return v

    def _and(self):
        v = self._not()
        while True:
            t = self._cur()
            if t[0] == "OP" and t[1] in ("∧", "&&") or (t[0] == "ID" and t[1] in ("and", "AND")):
                self._adv()
                r = self._not()
                v = _truthy(v) and _truthy(r)
            elif t[0] == "ID" and t[1] == "and":
                self._adv()
                r = self._not()
                v = _truthy(v) and _truthy(r)
            else:
                break
        return v

    def _not(self):
        t = self._cur()
        if t[0] == "OP" and t[1] in ("¬", "!"):
            self._adv()
            return not _truthy(self._not())
        if t[0] == "ID" and t[1] in ("not", "NOT"):
            self._adv()
            return not _truthy(self._not())
        return self._cmp()

    def _cmp(self):
        v = self._add()
        while True:
            t = self._cur()
            if t[0] != "OP":
                break
            op = t[1]
            if op not in ("<", ">", "<=", ">=", "==", "!=", "≤", "≥", "≠"):
                break
            self._adv()
            r = self._add()
            if op in ("<",):
                v = v < r
            elif op in ("<=", "≤"):
                v = v <= r
            elif op in (">",):
                v = v > r
            elif op in (">=", "≥"):
                v = v >= r
            elif op == "==":
                v = v == r
            elif op in ("!=", "≠"):
                v = v != r
        return v

    def _add(self):
        v = self._mul()
        while True:
            t = self._cur()
            if t[0] == "OP" and t[1] in ("+", "-"):
                self._adv()
                r = self._mul()
                if isinstance(v, str) or isinstance(r, str):
                    v = str(v) + str(r)      # 字符串拼接（文本诊断用）
                elif t[1] == "+":
                    v = v + r
                else:
                    v = v - r
            else:
                break
        return v

    def _mul(self):
        v = self._pow()
        while True:
            t = self._cur()
            if t[0] == "OP" and t[1] in ("*", "/"):
                self._adv()
                r = self._pow()
                v = v * r if t[1] == "*" else v / r
            else:
                break
        return v

    def _pow(self):
        v = self._unary()
        if self._accept("^"):
            r = self._pow()      # 右结合
            v = v ** r
        return v

    def _unary(self):
        t = self._cur()
        if t[0] == "OP" and t[1] in ("-", "+"):
            self._adv()
            v = self._unary()
            return -v if t[1] == "-" else v
        return self._atom()

    def _atom(self):
        t = self._cur()
        if t[0] == "NUM":
            self._adv()
            return self._maybe_deg(float(t[1]))
        if t[0] == "STR":
            self._adv()
            return t[1]
        if t[0] == "ID":
            name = t[1]
            self._adv()
            if name in ("min", "max"):
                # 支持多参数：min(min(a,b),c) 由括号嵌套处理；GeoGebra 也允许直接 min(a,b,c)
                self._expect("(")
                args = [self._expr()]
                while self._accept(","):
                    args.append(self._expr())
                self._expect(")")
                if name == "min":
                    v = min(args)
                else:
                    v = max(args)
                return v
            if name in FUNCTION_SUBSET:
                arity, fn = FUNCTION_SUBSET[name]
                if name in ("If", "if"):
                    # If 必须惰性：与 GeoGebra 一致——未选中分支不求值
                    # （否则 acos 越界等在分支里直接炸，见双分支轨迹链）
                    self._expect("(")
                    cond = self._expr()
                    self._expect(",")
                    if _truthy(cond):
                        v = self._expr()
                        self._expect(",")
                        self._skip_expr()
                    else:
                        self._skip_expr()
                        self._expect(",")
                        v = self._expr()
                    self._expect(")")
                    return v
                self._expect("(")
                args = []
                for _ in range(arity):
                    args.append(self._expr())
                    if _ < arity - 1:
                        self._expect(",")
                self._expect(")")
                return fn(*args)
            if name in CONSTANTS:
                return CONSTANTS[name] if name != "e" else math.e
            if name in self.env:
                return _fresh(self.env[name])
            raise EvalError(f"未定义标识符 {name}")
        if t[0] == "OP" and t[1] == "(":
            self._adv()
            v = self._expr()
            self._expect(")")
            return self._maybe_deg(v)
        raise EvalError(f"意外记号 {t!r}")

    def _maybe_deg(self, v):
        if self._cur()[0] == "OP" and self._cur()[1] == "°":
            self._adv()
            return math.radians(v)
        return v


def _fresh(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v
    return v


def _truthy(v):
    if isinstance(v, str):
        return True if v else False
    return bool(v)


def try_eval(expr: str, env: dict):
    """返回 (ok, value)。ok=False 表示求值器子集外（依赖 GeoGebra 重算）。"""
    try:
        return True, Evaluator(env).eval(expr)
    except EvalError:
        return False, None
    except Exception:
        return False, None


# ---------------------------------------------------------------- 标识符/引用提取

# 标识符：Unicode 字母/下划线开头，含 GeoGebra 下标写法 B_{1} / ω_1 / a_{o} / circle_{l}ight、撇号后缀 F'
_IDENT_RE = re.compile(r"[^\W\d][\w]*(?:\{[^\}]+\}[\w]*)*'?")
_STR_RE = re.compile(r'"[^"]*"')

# 绑定变量在第 2 个输入参数位置（a1）的命令：Sequence[expr,var,...] / Zip[expr,var,list]
_COMMANDS_WITH_BOUND_VAR = {"Sequence", "Zip", "IterationList"}
# Curve/CurveCartesian 的变量位不一（a1 或 a2），凡「恰好是裸标识符」的输入值都按绑定变量处理
_BARE_BOUND_CMDS = {"Curve", "CurveCartesian"}


def _is_bare_identifier(s: str) -> bool:
    return bool(_IDENT_RE.fullmatch(s))


def command_bound_vars(name: str, attrs) -> set:
    """返回命令输入里属于绑定变量（循环/曲线参数）的值集合。"""
    if name in _COMMANDS_WITH_BOUND_VAR and len(attrs) > 1:
        v = attrs[1][1].strip()
        return {v} if v else set()
    if name in _BARE_BOUND_CMDS:
        return {val.strip() for _, val in attrs if _is_bare_identifier(val.strip())}
    return set()


def _canon_lab(s: str) -> str:
    return re.sub(r"\{([^}]*)\}", r"\1", s) if "{" in s else s


def audit_macro_self_containment(root) -> tuple:
    """宏自包含审计（2026-08 重构）：返回 (defined_labels, dangling_refs, empty_label_list)。

    供 skill 侧 ggb_macro_preview.py 与仓库侧 tools/ggt_to_snippet.py 共用（单一事实源）。
    悬挂引用 = 构造里引用但从未定义的对象：refine 提取时把源场景的全局对象带进了宏，
    脱离场景即残缺，导入 GeoGebra 同样会失败。空 label = 精炼提取的残缺构造。
    """
    m = root if root.tag == "macro" else root.find("macro")

    def attrs_of(tag):
        el = m.find(tag) if m is not None else None
        if el is None:
            return []
        return [el.get(f"a{i}") for i in range(20) if el.get(f"a{i}")]

    if m is None:
        return set(), [], ["无 <macro> 定义"]
    inputs = attrs_of("macroInput")
    children = list(m.find("construction")) if m.find("construction") is not None else []
    defined = set(inputs)
    empty = []
    for c in children:
        if c.tag in ("element", "expression"):
            lab = c.get("label", "")
            if not lab:
                empty.append(f"{c.get('type', '?')}(元素)")
            else:
                defined.add(_canon_lab(lab))
        elif c.tag == "command":
            out = c.find("output")
            if out is not None:
                defined |= {_canon_lab(v) for v in out.attrib.values() if v}

    refs = set()
    _reserved_ci = {s.lower() for s in KNOWN_COMMANDS} | {s.lower() for s in set(CONSTANTS)} | {s.lower() for s in set(FUNCTION_SUBSET)}

    def _is_reserved(tok: str) -> bool:
        return tok.lower() in _reserved_ci or tok in FREE_VARS

    for c in children:
        stripped = _STR_RE.sub("", c.get("exp", "")) if c.tag == "expression" else None
        if stripped is not None:
            refs |= ({_canon_lab(t) for t in _IDENT_RE.findall(stripped)
                      if not _is_reserved(t)} - _bound_vars(stripped))
        elif c.tag == "command":
            name = c.get("name", "")
            inp = c.find("input")
            attrs = sorted(inp.attrib.items(), key=lambda kv: int(kv[0][1:])) \
                if inp is not None else []
            bound = command_bound_vars(name, attrs)
            for _k, v in attrs:
                if not v or v in bound:
                    continue
                vs = _STR_RE.sub("", v)
                refs |= ({_canon_lab(t) for t in _IDENT_RE.findall(vs)
                          if not _is_reserved(t)}
                         - bound - _bound_vars(vs))
    return defined, sorted(refs - defined), empty

# Sequence[expr, var, ...] / Zip[expr, var, ...] / Curve[..., var, ...] 的绑定变量（第 2/3 顶层参数）
_BOUND_CMDS = {"Sequence": 1, "Zip": 1, "IterationList": 1, "Iteration": 1,
               "Curve": 2, "CurveCartesian": 2}


def _bound_vars(exp: str) -> set:
    """提取 Sequence/Zip/Curve 等命令绑定变量（语法作用域内，非对象引用）。"""
    bound = set()
    for m in re.finditer(r"(?:%s)\s*[\[\(]" % "|".join(_BOUND_CMDS), exp):
        var_pos = _BOUND_CMDS[re.sub(r"[\[\(]\s*$", "", m.group(0)).strip()]
        i, depth, commas = m.end(), 0, 0
        while i < len(exp):
            c = exp[i]
            if c in "[(":
                depth += 1
            elif c in "])":
                if depth == 0:
                    break
                depth -= 1
            elif c == "," and depth == 0:
                commas += 1
                if commas == var_pos:
                    j = i + 1
                    while j < len(exp) and exp[j].isspace():
                        j += 1
                    vm = _IDENT_RE.match(exp[j:])
                    if vm:
                        bound.add(vm.group(0))
                    break
            i += 1
    return bound


_ASSIGN_RE = re.compile(r"([^\W\d][\w]*(?:\{[^\}]+\}[\w]*)*)\s*=(?![=>])")
_SCRIPT_IDENT = re.compile(r"[^\W\d][\w]*(?:\{[^\}]+\}[\w]*)*'?")


def analyze_script(script_text: str, resolvable):
    """逐行分析 ggbscript（已 XML 反转义），带「可用性」跟踪：
      - 先 `n = 0` 再 `n = n + 1`：第二行的 n 已由前一行创建 → 合法；
      - 首次创建即自引用（v = If[v,...] 且 v 无静态定义）→ ('selfref', v)，GeoGebra 求值 RHS 即报错；
      - 引用无出处名字 → ('undefined', name)。
    返回 (created, problems)；problems 为 [(name, kind)]。
    字符串字面量剔除。"""
    created, problems = set(), []
    text = _STR_RE.sub(" ", script_text)

    def check(ref, kind_hint=None):
        if ref in created or resolvable(ref):
            return
        problems.append((ref, kind_hint or "undefined"))

    for raw in text.replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            continue
        m = _ASSIGN_RE.match(line)
        if m:
            name = m.group(1)
            rhs_ids = {t.group(0) for t in _SCRIPT_IDENT.finditer(line[m.end():])}
            for r in sorted(rhs_ids):
                if r == name:
                    check(r, kind_hint="selfref")     # 首次创建即自引用
                else:
                    check(r)
            created.add(name)
        else:
            for t in _SCRIPT_IDENT.finditer(line):
                check(t.group(0))
    return created, problems


def extract_references(exp: str):
    """从表达式提取可能引用对象 label 的标识符集合（尽力而为）。
    放行：常量、已知命令、函数自变量、绑定变量；跳过 GeoGebra 内部下划线开头标识符。"""
    exp = html.unescape(exp)
    exp = _STR_RE.sub(" ", exp)          # 去掉字符串字面量
    bound = _bound_vars(exp)
    refs = set()
    for m in _IDENT_RE.finditer(exp):
        tok = m.group(0)
        if tok.startswith("_"):
            continue                      # GeoGebra 内部遗留命名
        if tok in FUNCTION_SUBSET or tok in KNOWN_COMMANDS or tok in CONSTANTS or tok in FREE_VARS:
            continue
        if tok in bound:
            continue
        refs.add(tok)
    return refs


def extract_point_refs(exp: str):
    """点表达式 (a*cos(E)-c, b*sin(E)) 的引用 —— 与通用一致。"""
    return extract_references(exp)


# ---------------------------------------------------------------- 五层校验

LAYER_NAMES = {1: "结构合法", 2: "引用一致", 3: "依赖拓扑", 4: "数值重算", 5: "JS 语法"}


class GgbCheck:
    def __init__(self, xml_path: str, fix: bool = False):
        self.xml_path = xml_path
        self.project_dir = os.path.dirname(os.path.abspath(xml_path))
        self.fix = fix
        self.issues: list[Issue] = []
        self.root = None
        self.construction = None
        self.labels: dict[str, dict] = {}     # label -> 描述
        self.order: list[dict] = []           # 文档顺序的构造条目
        self.macro_cmds: set[str] = self._load_macro_cmds()   # 自定义工具命令名（引用放行）

    def _load_macro_cmds(self) -> set:
        """读取同目录 geogebra_macro.xml 的 <macro cmdName>，作为用户命令白名单。"""
        path = os.path.join(self.project_dir, "geogebra_macro.xml")
        if not os.path.exists(path):
            return set()
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as e:
            self.warn(1, f"geogebra_macro.xml 解析失败（宏命令白名单为空）：{e}")
            return set()
        return {m.get("cmdName") for m in root.iter("macro") if m.get("cmdName")}

    # ---- 上报 ----
    def err(self, layer, msg, where=""):
        self.issues.append(Issue(layer, "error", msg, where))

    def warn(self, layer, msg, where=""):
        self.issues.append(Issue(layer, "warning", msg, where))

    def note(self, layer, msg, where=""):
        self.issues.append(Issue(layer, "note", msg, where))

    def has_errors(self):
        return any(i.level == "error" for i in self.issues)

    # ---- L1 结构 ----
    def layer1(self):
        try:
            parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
            self.root = ET.parse(self.xml_path, parser=parser).getroot()
        except ET.ParseError as e:
            self.err(1, f"XML 解析失败：{e}")
            return
        if self.root.tag != "geogebra":
            self.err(1, f"根元素应为 <geogebra>，实际 <{self.root.tag}>")
        cons = self.root.find("construction")
        if cons is None:
            self.err(1, "缺少 <construction> 容器")
            return
        self.construction = cons
        for child in cons:
            if not isinstance(child.tag, str):
                continue          # 注释等非元素节点（--fix 时需保留）
            tag = child.tag
            label = child.get("label", "")
            if tag in ("expression", "element"):
                if not label:
                    self.err(1, f"<{tag}> 缺少 label", where="构造")
                    continue
                self.order.append({"kind": tag, "label": label, "node": child})
            elif tag == "command":
                name = child.get("name", "")
                outs = [v for k, v in child.attrib.items() if k.startswith("a")]
                inputs = {k: v for k, v in child.attrib.items() if k.startswith("a")}
                # output 属性名形如 a0,a1...；input 也是 a0,a1... —— 用有无 output 区分靠 <output> 子元素
                in_el = child.find("input")
                out_el = child.find("output")
                if in_el is None or out_el is None:
                    self.err(1, f"<command name={name}> 缺少 <input> 或 <output>", where=label)
                    continue
                out_labels = [v for v in out_el.attrib.values() if v]
                if len(out_labels) != len(out_el.attrib):
                    self.note(1, f"<command name={name}> 存在空输出 label，已忽略", where=name)
                self.order.append({"kind": "command", "name": name,
                                   "node": child, "out_labels": out_labels})
            else:
                self.warn(1, f"construction 内未知元素 <{tag}>，跳过", where=label)
        # element/expression 配对
        i = 0
        while i < len(self.order):
            item = self.order[i]
            if item["kind"] == "expression":
                nxt = self.order[i + 1] if i + 1 < len(self.order) else None
                if nxt is None or nxt["kind"] != "element" or nxt["label"] != item["label"]:
                    self.err(1, f"<expression label={item['label']}> 之后必须紧随同 label 的 <element>",
                             where=item["label"])
                item["paired"] = bool(nxt)
                if nxt:
                    nxt["paired"] = True
            i += 1

    # ---- 预备：label 表 ----
    def build_label_index(self):
        self.cmd_outputs: set[str] = set()
        for item in self.order:
            if item["kind"] == "command":
                self.cmd_outputs.update(item["out_labels"])
        for item in self.order:
            if item["kind"] == "command":
                for lab in item.get("out_labels", []):
                    self.labels.setdefault(lab, {"defined": True, "kind": "command-out",
                                                 "node": item["node"]})
                continue
            if item["kind"] == "element" and (item.get("paired") or item["label"] in self.cmd_outputs):
                continue
            node = item["node"]
            kind = node.get("type", "")
            self.labels.setdefault(item["label"], {"defined": True, "kind": kind,
                                                   "node": node, "kind_tag": item["kind"]})

    # ---- L2 引用一致 ----
    def layer2(self):
        # 下标两种写法等价：B_{1} ≡ B_1（GeoGebra 语义），比较前规范化
        def canon(s: str) -> str:
            return re.sub(r"\{([^}]*)\}", r"\1", s)

        # 1) label 唯一：expression+element 成对算一次定义；command 输出算一次
        seen = {}
        for item in self.order:
            if item["kind"] == "element" and (item.get("paired") or item["label"] in self.cmd_outputs):
                continue          # 声明块 element，由 expression/command 统一登记
            if item["kind"] == "command":
                for lab in item["out_labels"]:
                    if lab in seen:
                        self.err(2, f"label 重复定义：{lab}", where=lab)
                    seen.setdefault(lab, item)
                continue
            lab = item["label"]
            if lab in seen:
                self.err(2, f"label 重复定义：{lab}", where=lab)
            seen.setdefault(lab, item)
        seen_c = {canon(k): k for k in seen}

        def unresolved(ref: str) -> bool:
            return (canon(ref) not in seen_c and ref not in BUILTIN_OBJS
                    and ref not in CONSTANTS and ref not in FUNCTION_SUBSET
                    and ref not in KNOWN_COMMANDS and ref not in FREE_VARS
                    and ref not in self.macro_cmds)

        # 全文件脚本赋值目标（运行时创建的对象，跨脚本可见）
        script_created = set()
        for item in self.order:
            node = item.get("node")
            if node is None or not isinstance(node.tag, str) or node.tag != "element":
                continue
            gs = node.find("ggbscript")
            if gs is None:
                continue
            for attr in ("val", "onUpdate"):
                body = gs.get(attr)
                if body:
                    script_created |= analyze_script(body, lambda r: not unresolved(r))[0]

        # 2) command input 引用（input 值多为表达式/字面量，按表达式提取标识符校验）
        for item in self.order:
            if item["kind"] != "command":
                continue
            name = item["name"]
            if name in ("NSolveODE", "NSolve"):
                self.note(2, f"命令 {name} 为内置数值 ODE（许可范围），导数/初值变量按函数自变量处理，跳过引用检查",
                          where=name)
                continue
            in_el = item["node"].find("input")
            attrs = sorted(in_el.attrib.items(), key=lambda kv: int(kv[0][1:]))
            bound = command_bound_vars(name, attrs)
            bound_c = {canon(b) for b in bound}
            for v in attrs:
                val = v[1]
                if not val or canon(val) in bound_c:
                    continue
                for ref in extract_references(val):
                    if ref in BUILTIN_OBJS or canon(ref) in bound_c:
                        continue
                    if unresolved(ref):
                        self.err(2, f"command {name} 输入引用未定义对象 {ref}", where=ref)
        # 3) 表达式引用：未定义标识符为 error（Builder 拼写错误的主战场）；
        #    含内置数值 ODE（NSolveODE，许可范围）的文件对未定义引用降级为 warning——ODE 导数变量按函数自变量处理。
        has_ode = any(i["kind"] == "command" and i["name"] in ("NSolveODE", "NSolve")
                      for i in self.order)
        for item in self.order:
            node = item.get("node")
            if node is None or not isinstance(node.tag, str) or node.tag != "expression":
                continue
            exp = node.get("exp", "")
            for ref in extract_references(exp):
                if unresolved(ref):
                    msg = f"表达式引用未定义标识符 {ref}"
                    if has_ode:
                        self.warn(2, msg + "（文件含内置数值 ODE）", where=item["label"])
                    else:
                        self.err(2, msg, where=item["label"])
        # 4) ggbscript 脚本引用（点击 val / 更新 onUpdate）：
        #    - 静态可解析（对象/命令/常量）→ 通过；但 u/v/w 不豁免——它们是
        #      「翻转布尔」等脚本的常见变量名，必须真实存在（实测教训）；
        #    - 赋值 RHS 自引用且无静态定义（v = If[v,...] 且 v 不存在）→ error；
        #    - 其余脚本运行时创建的对象 → warning；完全无出处的名字 → error。
        script_created_c = {re.sub(r"\{([^}]*)\}", r"\1", c) for c in script_created}
        _no_exempt = {"u", "v", "w"}

        def script_resolvable(ref: str) -> bool:
            if ref in _no_exempt:
                return canon(ref) in seen_c or ref in CONSTANTS or ref in KNOWN_COMMANDS \
                    or ref in FUNCTION_SUBSET
            return not unresolved(ref)

        for item in self.order:
            node = item.get("node")
            if node is None or not isinstance(node.tag, str) or node.tag != "element":
                continue
            gs = node.find("ggbscript")
            if gs is None:
                continue
            for attr in ("val", "onUpdate"):
                body = gs.get(attr)
                if not body:
                    continue
                created_local, problems = analyze_script(body, script_resolvable)
                for ref, kind in sorted(problems):
                    cref = re.sub(r"\{([^}]*)\}", r"\1", ref)
                    if has_ode:
                        self.warn(2, f"ggbscript {attr} 未定义变量 {ref}"
                                     "（文件含内置数值 ODE）", where=item["label"])
                    elif kind == "selfref":
                        self.err(2, f"ggbscript {attr} 自引用创建 {ref}：变量不存在，"
                                    "GeoGebra 求值 RHS 即报「未定义变量」。"
                                    "请先定义隐藏布尔/数值自由对象再在脚本里引用",
                                 where=item["label"])
                    elif cref in script_created_c:
                        self.warn(2, f"ggbscript {attr} 的 {ref} 由脚本运行时赋值创建"
                                     "（建议改为预定义自由对象，行为更可控）", where=item["label"])
                    else:
                        self.err(2, f"ggbscript {attr} 引用未定义变量 {ref}", where=item["label"])

    # ---- L2b 素材一致性（image 引用 / 残留）----
    def layer_media(self):
        """image 元素的 <file name> 与宏 iconFile 的可达性（warning 级）+ 未引用残留提醒。

        硬性错误由打包器（ggb_pack.py 按引用收图）承担；本层只告警，
        因为 checker 常以单文件视角被调用（语料库解包、临时目录），
        不能假定项目媒体文件齐全。
        """
        IMG = (".png", ".jpg", ".jpeg", ".gif", ".bmp", ".svg")
        refs = set()
        for el in self.construction.iter("element"):
            if el.get("type") != "image":
                continue
            f = el.find("file")
            if f is None or not (f.get("name") or ""):
                continue
            name = f.get("name")
            refs.add(name)
            if not (os.path.exists(os.path.join(self.project_dir, name))
                    or os.path.exists(os.path.join(self.project_dir, "media", name))):
                self.warn(2, f"image 引用的素材不存在：{name}", where=el.get("label", ""))
        macro_path = os.path.join(self.project_dir, "geogebra_macro.xml")
        if os.path.exists(macro_path):
            try:
                mroot = ET.parse(macro_path).getroot()
                for m in mroot.iter("macro"):
                    icon = m.get("iconFile") or ""
                    if icon:
                        refs.add(icon)
                        if not (os.path.exists(os.path.join(self.project_dir, icon))
                                or os.path.exists(os.path.join(self.project_dir, "media", icon))):
                            self.warn(2, f"宏图标引用不存在：{icon}", where=m.get("cmdName", ""))
            except ET.ParseError:
                pass
        # 残留：目录里放了图片但没有任何引用（排除自带的缩略图）
        if not refs:
            return
        present = set()
        for dirpath, _dirs, files in os.walk(self.project_dir):
            for fn in files:
                if fn.lower().endswith(IMG) and fn != "geogebra_thumbnail.png":
                    rel = os.path.relpath(os.path.join(dirpath, fn), self.project_dir)
                    if rel != "geogebra_thumbnail.png":
                        # 素材统一以"引用路径"表述：media/ 前缀是存放约定，不计入
                        present.add(rel[len("media/"):] if rel.startswith("media/") else rel)
        for rel in sorted(present - refs):
            self.warn(2, f"图片未被任何引用（打包时不会带出，建议移除）：{rel}")

    # ---- L3 依赖拓扑 ----
    def layer3(self):
        # 严格顺序检查：引用者必须在前向定义之后（成对 element 跳过）。
        # 豁免：内建对象（轴线）、函数定义的自引用（f(x)=… 的 f）、命令绑定变量。
        has_ode = any(i["kind"] == "command" and i["name"] in ("NSolveODE", "NSolve")
                      for i in self.order)

        def canon(s_: str) -> str:
            return re.sub(r"\{([^}]*)\}", r"\1", s_)

        defined_at = {}
        for pos, item in enumerate(self.order):
            if item["kind"] == "element" and (item.get("paired") or item["label"] in self.cmd_outputs):
                continue
            self_labels = []
            if item["kind"] == "command":
                refs = []
                if item["name"] not in ("NSolveODE", "NSolve"):
                    in_el = item["node"].find("input")
                    if in_el is not None:
                        attrs = sorted(in_el.attrib.items(), key=lambda kv: int(kv[0][1:]))
                        bound = command_bound_vars(item["name"], attrs)
                        for v in attrs:
                            if v[1] in bound:
                                continue
                            refs.extend(r for r in extract_references(v[1]) if r not in bound)
                out_labels = [o for o in item["out_labels"] if o]
            else:
                node = item["node"]
                if node.tag == "expression":
                    exp = node.get("exp", "")
                    refs = [r for r in extract_references(exp) if r != item["label"]]
                    self_labels = [item["label"]]
                else:
                    refs = []
                out_labels = [item["label"]]
            for ref in refs:
                cref = canon(ref)
                if ref in BUILTIN_OBJS or ref in CONSTANTS or ref in FUNCTION_SUBSET \
                        or ref in KNOWN_COMMANDS or ref in FREE_VARS or ref in self.macro_cmds:
                    continue
                if cref not in defined_at:
                    msg = (f"引用前向对象 {ref}：其定义位于本对象之后（或不存在），"
                           "GeoGebra 打开可能报 error in <expression>")
                    if has_ode:
                        self.warn(3, msg + "（文件含内置数值 ODE）",
                                  where=item.get("label", ""))
                    else:
                        self.err(3, msg, where=item.get("label", ""))
                elif defined_at[cref] > pos:
                    self.err(3, f"先用后定义：{ref} 在位置 {defined_at[cref]} 定义，位置 {pos} 已引用",
                             where=item.get("label", ""))
            for lab in out_labels:
                defined_at[canon(lab)] = pos

    # ---- L4 数值重算 ----
    def layer4(self):
        env: dict = {}        # label -> 已知数值
        # 先收自由对象初值（滑杆/布尔/自由点）
        for item in self.order:
            node = item.get("node")
            if node is None or node.tag != "element":
                continue
            lab = item["label"]
            v = node.find("value")
            if v is not None and v.get("val"):
                try:
                    val = parse_bool_num(v.get("val"))
                    env[lab] = val
                except ValueError:
                    pass
        # 依次处理每个 expression：可算则校验/填充
        n = len(self.order)
        for pos, item in enumerate(self.order):
            node = item.get("node")
            if node is None or node.tag != "expression":
                continue
            lab = item["label"]
            exp = node.get("exp", "")
            if re.search(r"(?:\bmin|\bmax)\s*\([^()]*,[^()]*\)", exp, re.I):
                self.warn(4, "表达式含 min(…,…)/max(…,…) 多参调用：GeoGebra 表达式层解析"
                             "可能失败（实测 sEff 案例报 error in <expression>），"
                             "请改用 If(a < b, a, b) 钳制", where=lab)
            type_ = node.get("type", "")
            elem = None
            if pos + 1 < n and self.order[pos + 1]["kind"] == "element" \
                    and self.order[pos + 1]["label"] == lab:
                elem = self.order[pos + 1]["node"]
            is_bool = type_ == "boolean" or (type_ == "" and looks_boolean(exp))
            if type_ in ("numeric", "boolean") or (type_ == "" and looks_boolean(exp)):
                self._check_numeric(env, lab, exp, elem, boolean=is_bool)
            elif type_ == "point":
                self._check_point(env, lab, exp, elem)
            else:
                self.note(4, f"求值器不处理 {type_ or '未标注'} 类型（GeoGebra 加载重算）", where=lab)
        # 滑杆值范围检查
        for item in self.order:
            node = item.get("node")
            if node is None or node.tag != "element":
                continue
            sl = node.find("slider")
            v = node.find("value")
            if sl is not None and v is not None and v.get("val"):
                try:
                    val = float(v.get("val"))
                    lo = float(sl.get("min", "-inf"))
                    hi = float(sl.get("max", "inf"))
                    if not (lo <= val <= hi):
                        self.warn(4, f"滑杆初值 {val} 超出范围 [{lo}, {hi}]", where=item["label"])
                except ValueError:
                    pass

    def _check_numeric(self, env, lab, exp, elem, boolean):
        ok, val = try_eval(exp, env)
        where = lab
        if not ok:
            self.note(4, f"表达式求值子集外，依赖 GeoGebra 重算：{exp}", where=lab)
            return
        if boolean:
            val = _truthy(val)
        self._compare_and_store(lab, elem, "value", "val", val, boolean=boolean)
        # 已求得的值进入环境，供后续表达式引用
        env[lab] = val

    def _check_point(self, env, lab, exp, elem):
        # 期待 (xexpr, yexpr)
        inner = exp.strip()
        if not (inner.startswith("(") and inner.endswith(")")):
            self.note(4, "点表达式未按 (x,y) 形式，跳过缓存校验", where=lab)
            return
        parts = split_top_level_commas(inner[1:-1])
        if len(parts) < 2:
            self.note(4, "点表达式无法拆分为 (x,y)，跳过", where=lab)
            return
        okx, x = try_eval(parts[0], env)
        oky, y = try_eval(parts[1], env)
        if not (okx and oky):
            self.note(4, "点坐标含子集外成分，依赖重算", where=lab)
            return
        # 检验/填充 <coords>
        elem_val = None
        if elem is not None:
            elem_val = elem.find("coords")
        old = elem_val.get("x") if elem_val is not None and elem_val.get("x") is not None else None
        if old is not None:
            try:
                oldx = float(old)
                oldy = float(elem_val.get("y", 0))
                dx = abs(oldx - x)
                dy = abs(oldy - y)
                tol = 1e-6 * max(1.0, abs(x), abs(oldx))
                if dx > tol or dy > tol:
                    if self.fix:
                        elem_val.set("y", fmt_float(y))
                        elem_val.set("x", fmt_float(x))
                        self.note(4, f"修复点坐标 ({oldx},{oldy})→({fmt_float(x)},{fmt_float(y)})", where=lab)
                    else:
                        self.warn(4, f"点缓存与公式不符：({oldx},{oldy}) vs ({fmt_float(x)},{fmt_float(y)})",
                                  where=lab)
                else:
                    self.note(4, f"点缓存一致 ({fmt_float(x)},{fmt_float(y)})", where=lab)
            except (ValueError, TypeError):
                self.note(4, "点缓存值非数值，跳过", where=lab)
        else:
            if self.fix and elem is not None:
                if elem_val is None:
                    elem_val = ET.SubElement(elem, "coords")
                    elem_val.set("z", "1.0")
                elem_val.set("x", fmt_float(x))
                elem_val.set("y", fmt_float(y))
                self.note(4, f"填充点坐标 ({fmt_float(x)},{fmt_float(y)})", where=lab)
            else:
                self.note(4, "点缺少缓存 <coords>，--fix 可填充", where=lab)
        env[lab] = (x, y)

    def _compare_and_store(self, lab, elem, tag, attr, expected, boolean=False):
        """数值缓存值校验/填充。expected 为已算值。"""
        val_el = elem.find(tag) if elem is not None else None
        old = val_el.get(attr) if val_el is not None and val_el.get(attr) else None
        if old is None or old == "":
            if self.fix and elem is not None:
                if val_el is None:
                    val_el = ET.SubElement(elem, tag)
                val_el.set(attr, fmt_val(expected))
                self.note(4, f"填充缓存值 {fmt_val(expected)}", where=lab)
            else:
                self.note(4, f"缺少缓存 <{tag}>，--fix 可填充 {fmt_val(expected)}", where=lab)
            return
        try:
            oldn = parse_bool_num(old)
        except ValueError:
            self.warn(4, f"缓存值 {old!r} 不是数值/布尔", where=lab)
            return
        if isinstance(expected, bool):
            if oldn != expected:
                if self.fix and val_el is not None:
                    val_el.set(attr, fmt_val(expected))
                    self.note(4, f"修复布尔缓存 {old}→{fmt_val(expected)}", where=lab)
                else:
                    self.warn(4, f"缓存与公式不符：{old} vs {expected}", where=lab)
            else:
                self.note(4, f"缓存一致 {fmt_val(expected)}", where=lab)
            return
        exp_num = float(expected)
        r_tol = 1e-6 * max(1.0, abs(exp_num), abs(oldn))
        if abs(oldn - exp_num) > r_tol:
            if self.fix and val_el is not None:
                val_el.set(attr, fmt_float(exp_num))
                self.note(4, f"修复缓存值 {old}→{fmt_float(exp_num)}", where=lab)
            else:
                self.warn(4, f"缓存与公式不符：{old} vs {fmt_float(exp_num)}", where=lab)
        else:
            self.note(4, f"缓存一致 {fmt_float(exp_num)}", where=lab)

    # ---- L5 JS 语法 ----
    def layer5(self):
        js = os.path.join(self.project_dir, "geogebra_javascript.js")
        if not os.path.exists(js):
            self.note(5, "无 geogebra_javascript.js（可选），跳过")
            return
        text = open(js, encoding="utf-8").read()
        if not text.strip():
            self.note(5, "geogebra_javascript.js 为空，跳过")
            return
        try:
            r = subprocess.run(["node", "--check", js], capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            self.warn(5, "未找到 node，跳过 JS 语法检查（建议装 node）")
            return
        except subprocess.TimeoutExpired:
            self.warn(5, "node --check 超时，跳过")
            return
        if r.returncode != 0:
            self.err(5, f"JS 语法错误：\n{r.stderr.strip()}")
        else:
            self.note(5, "JS 语法通过")

    # ---- L1b 形态：element 子元素顺序（金标准 §4/§10 坑2 机器化，warning 级 2026-08） ----
    # 只查高置信规则：两种已实证的滑杆形态（新：value→slider→…→animation→caption；
    # 旧：show→…→slider→value→animation→caption）都放行，仅拦截明显反序。
    def layer1b_order(self):
        for item in self.order:
            node = item.get("node")
            if node is None or not isinstance(node.tag, str) or node.tag != "element":
                continue
            lab = item.get("label", "")
            tags = [c.tag for c in node if isinstance(c.tag, str)]
            ggbscript_pos = tags.index("ggbscript") if "ggbscript" in tags else -1
            # 规则 1/2：滑杆 numeric —— animation 须在 slider 之后；caption 须在 animation 之后
            if node.find("slider") is not None:
                if "animation" in tags:
                    if tags.index("animation") < tags.index("slider"):
                        self.warn(1, "滑杆元素里 animation 出现在 slider 之前：金标准顺序 "
                                     "value→slider→lineStyle→show→objColor→layer→labelMode→"
                                     "animation（construction §4.1/§10 坑2），此形态在网页版"
                                     "可能使 value 失效", where=lab)
                if "caption" in tags and "animation" in tags \
                        and tags.index("caption") < tags.index("animation"):
                    self.warn(1, "滑杆元素里 caption 出现在 animation 之前：caption 应为"
                                 "最后的状态位（construction §4.1）", where=lab)
            # 规则 3：ggbscript 应为 element 末尾（按钮除外——按钮实测形态是
            #         ggbscript→caption→font，见 construction §4.4）
            if ggbscript_pos >= 0 and node.get("type") != "button" \
                    and ggbscript_pos != len(tags) - 1:
                self.warn(1, "ggbscript 不是 element 最后一个子元素：实测形态里更新脚本"
                             "恒在末尾（线框入磁样张），靠后的状态位可能失效", where=lab)
            # 规则 4：button —— ggbscript 须在 caption 之前
            if node.get("type") == "button" and ggbscript_pos >= 0 and "caption" in tags \
                    and tags.index("caption") < ggbscript_pos:
                self.warn(1, "按钮点击脚本 ggbscript 出现在 caption 之后：金标准 §4.4 "
                             "形态为 ggbscript→caption→font", where=lab)
            # 规则 5：boolean 自由对象 —— checkbox 须在 value 之后
            if node.get("type") == "boolean" and node.find("checkbox") is not None \
                    and "value" in tags and tags.index("checkbox") < tags.index("value"):
                self.warn(1, "boolean 元素里 checkbox 出现在 value 之前（金标准 §4.3 "
                             "顺序 value→…→checkbox→labelOffset→caption）", where=lab)
            # 规则 6：text —— 屏幕定位与世界坐标锚定二选一
            if node.get("type") == "text" and node.find("absoluteScreenLocation") is not None \
                    and node.find("startPoint") is not None:
                self.warn(1, "text 元素同时含 absoluteScreenLocation 与 startPoint：屏幕"
                             "定位与世界坐标锚定二选一（construction §4.10）", where=lab)

    # ---- 主流程 ----
    def run(self):
        self.layer1()
        self.layer1b_order()
        if not self.has_errors():
            self.build_label_index()
            self.layer2()
        self.layer_media()
        if not self.has_errors():
            self.layer3()
        if not self.has_errors():
            self.layer4()
        if not self.has_errors():
            self.layer5()
        if self.fix and not self.has_errors():
            try:
                ET.indent(self.root, space="\t")
            except Exception:
                pass
            ET.ElementTree(self.root).write(self.xml_path, encoding="utf-8", xml_declaration=True)
        return self


# ---------------------------------------------------------------- 工具函数

def parse_bool_num(s):
    s2 = s.strip().lower()
    if s2 == "true":
        return True
    if s2 == "false":
        return False
    return float(s2)


def looks_boolean(exp):
    """表达式类型未标注时，若含比较/逻辑运算则视作布尔。"""
    return any(op in exp for op in ("==", "!=", "<", ">", "∧", "∨", "¬", "≤", "≥"))


def split_top_level_commas(s):
    parts, depth, buf = [], 0, []
    for ch in s:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    if buf or parts:
        parts.append("".join(buf).strip())
    return parts


def fmt_float(x):
    if float(x) == int(x) and abs(x) < 1e15:
        return str(int(x))
    s = repr(float(x))
    return s


def fmt_val(x):
    if isinstance(x, bool):
        return "true" if x else "false"
    if isinstance(x, str):
        return x
    return fmt_float(x)


def render_report(issues, layers):
    lines = []
    for layer in sorted(layers):
        sub = [i for i in issues if i.layer == layer]
        if not sub:
            continue
        lines.append(f"── 第{layer}层 {LAYER_NAMES[layer]}")
        for i in sub:
            lines.append(f"   {i}")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ggb_check.py", description="ggb-master 五层校验")
    ap.add_argument("xml", help="geogebra.xml 路径")
    ap.add_argument("--fix", action="store_true", help="可算的缺失/不符缓存值写回文件")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    ap.add_argument("--quiet", action="store_true", help="只输出结论")
    args = ap.parse_args(argv)

    if not os.path.exists(args.xml):
        print(f"错误：文件不存在 {args.xml}", file=sys.stderr)
        return 2

    chk = GgbCheck(args.xml, fix=args.fix)
    try:
        chk.run()
    except Exception as e:
        print(f"内部错误：{e}", file=sys.stderr)
        return 2

    errs = chk.has_errors()
    if args.json:
        print(json.dumps({
            "ok": not errs,
            "errors": [i.to_dict() for i in chk.issues if i.level == "error"],
            "warnings": [i.to_dict() for i in chk.issues if i.level == "warning"],
            "notes": [i.to_dict() for i in chk.issues if i.level == "note"],
        }, ensure_ascii=False, indent=2))
    else:
        if not args.quiet:
            layers = sorted({i.layer for i in chk.issues})
            report = render_report(chk.issues, layers)
            if report:
                print(report)
            n_e = sum(1 for i in chk.issues if i.level == "error")
            n_w = sum(1 for i in chk.issues if i.level == "warning")
            print(f"---- 结论：{'失败' if errs else '通过'}（{n_e} error / {n_w} warning）")
        else:
            print("FAIL" if errs else "OK")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

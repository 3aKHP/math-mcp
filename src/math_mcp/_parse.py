"""
math_mcp._parse
共享解析辅助函数：表达式解析、矩阵/向量/数据解析。
"""
from __future__ import annotations

import re
from typing import Any

from sympy import Matrix, Symbol, sstr
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

# ── 解析配置 ────────────────────────────────────────────────────────────────────

_TRANSFORMATIONS = standard_transformations + (
    implicit_multiplication_application,  # 2x → 2*x, x y → x*y
    convert_xor,                          # x^2 → x**2
)

# ── 辅助函数 ────────────────────────────────────────────────────────────────────


def _parse(s: str, local_dict: dict | None = None):
    """安全解析数学表达式字符串。"""
    s = s.strip()
    if not s:
        raise ValueError("empty expression")
    return parse_expr(s, transformations=_TRANSFORMATIONS, local_dict=local_dict or {})


def _extract_func_names(expr_str: str) -> list[str]:
    """提取表达式中形如 f(x) 的未定义函数名。"""
    names: list[str] = []
    seen: set[str] = set()
    # 匹配标识符后跟括号，排除已知的 SymPy 函数
    _KNOWN = {"Derivative", "Integral", "Limit", "Sum", "Product", "sin", "cos", "tan",
              "exp", "log", "sqrt", "Abs", "sign", "re", "im", "conjugate", "erf", "erfc",
              "gamma", "beta", "zeta", "Piecewise", "And", "Or", "Not", "Matrix", "Eq"}
    for m in re.finditer(r"([a-zA-Z_]\w*)\s*\(", expr_str):
        name = m.group(1)
        if name not in _KNOWN and name not in seen:
            seen.add(name)
            names.append(name)
    return names


def _maybe_eval(expr: Any, precision: int = 50) -> str:
    """如果表达式无数值自由符号则求值，否则返回符号形式。"""
    if hasattr(expr, "free_symbols") and not expr.free_symbols:
        try:
            return str(expr.evalf(precision))
        except Exception:
            pass
    return sstr(expr)


def _parse_subs(subs_str: str) -> dict:
    """解析替换字符串 'x=5,y=10' 为 {x: 5, y: 10}。"""
    result: dict = {}
    if not subs_str.strip():
        return result
    for part in subs_str.split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"invalid substitution: {part}")
        k, v = part.split("=", 1)
        result[Symbol(k.strip())] = _parse(v.strip())
    return result


def _parse_matrix(s: str) -> Matrix:
    """解析矩阵字符串 '[[a,b],[c,d]]' 或 '[[a,b,c],[d,e,f],[g,h,i]]'。"""
    s = s.strip()
    # 允许 numpy 风格的分号分隔: "[1,2;3,4]"
    if ";" in s:
        rows = s.split(";")
    else:
        # 找到最外层 [[...], [...]] 的结构
        s = s.strip()
        if not (s.startswith("[") and s.endswith("]")):
            raise ValueError("matrix must be wrapped in brackets: [[a,b],[c,d]]")
        # 去掉最外层括号后拆分各行
        inner = s[1:-1].strip()
        # 找 ]...分隔...[
        rows = []
        depth = 0
        current: list[str] = []
        for ch in inner:
            if ch == "[":
                depth += 1
                if depth == 1:
                    current = []
                    continue
            if ch == "]":
                depth -= 1
                if depth == 0:
                    rows.append("".join(current))
                    continue
            if depth > 0:
                current.append(ch)
    data = []
    for row_str in rows:
        row_str = row_str.strip().rstrip(",").strip()
        if not row_str:
            continue
        elems = [e.strip() for e in row_str.split(",") if e.strip()]
        data.append([_parse(e) for e in elems])
    if not data:
        raise ValueError("empty matrix")
    ncols = len(data[0])
    for i, row in enumerate(data):
        if len(row) != ncols:
            raise ValueError(f"row {i} has {len(row)} columns, expected {ncols}")
    return Matrix(data)


def _parse_vector(s: str) -> Matrix:
    """解析向量字符串 '[a,b,c]' 为列矩阵。"""
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    parts = [p.strip() for p in s.split(",") if p.strip()]
    if not parts:
        raise ValueError("empty vector")
    return Matrix([[_parse(p)] for p in parts])


def _parse_data(s: str):
    """解析数据列表 '[1,2,3,4,5]' 或 '1,2,3,4,5'。"""
    s = s.strip()
    if s.startswith("[") and s.endswith("]"):
        s = s[1:-1]
    parts = [p.strip() for p in s.split(",") if p.strip()]
    result = []
    for p in parts:
        expr = _parse(p)
        if expr.free_symbols:
            raise ValueError(f"data contains free symbol: {p}")
        result.append(float(expr.evalf()))
    return result


def _parse_xy_data(s: str):
    """解析配对数据 '[[x1,y1],[x2,y2],...]' 或 '[x1,y1;x2,y2;...]'。"""
    s = s.strip()
    pairs = []
    if ";" in s:
        # 分号分隔
        chunks = s.split(";")
    else:
        # [[x1,y1],[x2,y2],...]
        if s.startswith("[[") and s.endswith("]]"):
            inner = s[2:-2]
            chunks = inner.split("],[")
        elif s.startswith("[") and s.endswith("]"):
            inner = s[1:-1]
            chunks = inner.split("],[")
        else:
            chunks = s.split(";")
    for chunk in chunks:
        chunk = chunk.strip().strip("[").strip("]")
        parts = [p.strip() for p in chunk.split(",") if p.strip()]
        if len(parts) != 2:
            raise ValueError(f"expected [x,y] pair, got: {chunk}")
        x = float(_parse(parts[0]).evalf())
        y = float(_parse(parts[1]).evalf())
        pairs.append((x, y))
    return pairs

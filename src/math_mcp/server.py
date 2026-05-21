"""
math_mcp.server
Math MCP 服务器，提供全面的数学计算功能。
符号计算、微积分、线性代数、数论、统计、单位换算。
"""
from __future__ import annotations

import math
import os
import re
from typing import Any

from sympy import (
    Derivative,
    Eq,
    Function,
    I,
    Integral,
    Limit,
    Matrix,
    Product,
    Sum,
    Symbol,
    apart,
    bernoulli,
    binomial,
    cancel,
    collect,
    diff,
    divisors,
    dsolve,
    expand,
    factor,
    factorint,
    fibonacci,
    gcd,
    integrate,
    isprime,
    lcm,
    limit,
    nextprime,
    npartitions,
    oo,
    pi,
    piecewise_fold,
    prevprime,
    prime,
    primepi,
    primitive_root,
    radsimp,
    series,
    sieve,
    simplify,
    solve,
    sstr,
    symbols,
    together,
    totient,
    trigsimp,
)
from sympy.calculus.util import continuous_domain
from sympy.parsing.sympy_parser import (
    convert_xor,
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)
from sympy.stats import (
    Beta,
    Binomial,
    ChiSquared,
    Exponential,
    FDistribution,
    Gamma,
    Normal,
    Poisson,
    StudentT,
    Uniform,
    P,
    E as EV,
    cdf,
    density,
    given,
    quantile,
    sample,
    variance,
    where,
)

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

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
    import re
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


# ── MCP 服务器 ──────────────────────────────────────────────────────────────────

_port = int(os.environ.get("PORT", 5109))
_host = os.environ.get("HOST", "127.0.0.1")
_transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)

mcp = FastMCP(
    "mcp-math",
    host=_host,
    port=_port,
    streamable_http_path="/mcp",
    transport_security=_transport_security,
)


# ── 工具 ────────────────────────────────────────────────────────────────────────

@mcp.tool()
def math_eval(expression: str, precision: int = 50, substitutions: str = "") -> str:
    """
    计算数学表达式。支持任意精度浮点、复数、符号运算。

    expression: 数学表达式，支持算术、三角函数、对数、指数、特殊函数（gamma/erf/zeta）、
               复数（I 为虚数单位）、无穷大（oo）、矩阵字面量等。
               示例: 'sqrt(2)+sqrt(3)', 'sin(pi/6)+cos(pi/3)', 'gamma(0.5)',
                     'integrate(x^2*sin(x), (x,0,pi))', 'Matrix([[1,2],[3,4]]).det()'
    precision: 数值计算精度（小数位数），默认 50。
    substitutions: 变量替换，格式 'x=5,y=10'。
    """
    try:
        expr = _parse(expression)
        if substitutions.strip():
            subs_dict = _parse_subs(substitutions)
            expr = expr.subs(subs_dict)
        return _maybe_eval(expr, precision)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def math_solve(
    equation: str,
    variables: str = "x",
    equation_type: str = "auto",
    function: str = "",
) -> str:
    """
    求解方程或方程组。

    equation: 方程，支持三种写法:
              (1) 'x^2 - 4 = 0'（显式等式）
              (2) 'x^2 - 4'（隐式 = 0）
              (3) 方程组: 'x + y = 10, 2*x - y = 5' 配合 variables='x,y'
              (4) 微分方程: 'Derivative(f(x),x) + f(x)' 配合 function='f'
    variables: 待求解变量，默认 'x'。方程组用逗号分隔: 'x,y,z'。
    equation_type: 'auto'（自动检测）、'algebraic'、'differential'、'system'。
    function: 微分方程中的未知函数名，默认自动从表达式中提取（如 f(x) → f）。
    """
    try:
        var_list = [Symbol(v.strip()) for v in variables.split(",") if v.strip()]
        eq_str = equation.strip()

        # 自动检测类型
        if equation_type == "auto":
            if "Derivative" in eq_str:
                equation_type = "differential"
            elif len(var_list) > 1 and ("," in eq_str or ";" in eq_str):
                equation_type = "system"
            else:
                equation_type = "algebraic"

        if equation_type == "differential":
            # 确定未知函数名
            if function.strip():
                func_name = function.strip()
            else:
                names = _extract_func_names(eq_str)
                func_name = names[0] if names else "f"

            # 创建 Function 对象并注入 local_dict，使 f(x) 被正确解析为函数应用
            func = Function(func_name)
            local_dict = {func_name: func}

            # 解析微分方程
            eqs = []
            for part in eq_str.split(";"):
                part = part.strip()
                if not part:
                    continue
                if "=" in part:
                    lhs_s, rhs_s = part.split("=", 1)
                    eqs.append(Eq(_parse(lhs_s, local_dict), _parse(rhs_s, local_dict)))
                else:
                    eqs.append(Eq(_parse(part, local_dict), 0))

            sol = dsolve(eqs[0], func(var_list[0]))
            # dsolve 可能返回单个 Eq 或列表
            if isinstance(sol, list):
                lines = []
                for s in sol:
                    lines.append(sstr(s))
                return "\n".join(lines)
            return sstr(sol)

        if equation_type == "system" or len(var_list) > 1:
            eqs = []
            for part in eq_str.split(","):
                part = part.strip()
                if not part:
                    continue
                if "=" in part:
                    lhs_s, rhs_s = part.split("=", 1)
                    eqs.append(Eq(_parse(lhs_s), _parse(rhs_s)))
                else:
                    eqs.append(Eq(_parse(part), 0))
            sol = solve(eqs, var_list, dict=True)
        else:
            if "=" in eq_str:
                lhs_s, rhs_s = eq_str.split("=", 1)
                eq = Eq(_parse(lhs_s), _parse(rhs_s))
            else:
                eq = Eq(_parse(eq_str), 0)
            sol = solve(eq, var_list[0], dict=True)

        if not sol:
            return "(无解)"
        if isinstance(sol, list):
            lines = []
            for i, s in enumerate(sol):
                if isinstance(s, dict):
                    items = [f"{k}={_maybe_eval(v)}" for k, v in s.items()]
                    lines.append(f"  解 {i+1}: {', '.join(items)}")
                else:
                    lines.append(f"  {_maybe_eval(s)}")
            return "\n".join(lines)
        return sstr(sol)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def math_calculus(
    expression: str,
    variable: str = "x",
    operation: str = "integrate",
    lower: str = "",
    upper: str = "",
    order: int = 1,
    point: str = "",
) -> str:
    """
    微积分运算：积分、求导、极限、级数展开、求和、求积。

    expression: 数学表达式，如 'x^2*sin(x)'、'sin(x)/x'、'1/n^2'。
    variable: 变量名，默认 'x'。
    operation: 'integrate'（积分）、'differentiate'（求导）、'limit'（极限）、
               'series'（级数展开）、'sum'（求和）、'product'（求积）。
    lower: 定积分下限 / 求和下限 / 级数点。
    upper: 定积分上限 / 求和上限。
    order: 求导阶数 / 级数展开阶数，默认 1。
    point: 极限趋近点 / 级数展开中心点。
    """
    try:
        expr = _parse(expression)
        var = Symbol(variable.strip())

        if operation == "integrate":
            if lower or upper:
                lo = _parse(lower) if lower else -oo
                hi = _parse(upper) if upper else oo
                return sstr(integrate(expr, (var, lo, hi)))
            return sstr(integrate(expr, var))

        elif operation == "differentiate":
            for _ in range(order):
                expr = diff(expr, var)
            return sstr(expr)

        elif operation == "limit":
            pt = _parse(point) if point else 0
            return sstr(limit(expr, var, pt))

        elif operation == "series":
            pt = _parse(point) if point else 0
            n = max(order, 1)
            return sstr(series(expr, var, pt, n))

        elif operation in ("sum", "summation"):
            lo = _parse(lower) if lower else 0
            hi = _parse(upper) if upper else oo
            return sstr(Sum(expr, (var, lo, hi)).doit())

        elif operation == "product":
            lo = _parse(lower) if lower else 1
            hi = _parse(upper) if upper else oo
            return sstr(Product(expr, (var, lo, hi)).doit())

        else:
            return f"不支持的操作: {operation}。支持: integrate, differentiate, limit, series, sum, product"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def math_matrix(
    matrix: str,
    operation: str = "eigenvalues",
    vector: str = "",
) -> str:
    """
    矩阵与线性代数运算。

    matrix: 矩阵，格式 '[[a,b],[c,d]]' 或 '[a,b;c,d]'。
    operation: 支持的运算:
        eigenvalues    — 特征值
        eigenvectors   — 特征向量
        determinant    — 行列式
        inverse        — 逆矩阵
        rref           — 简化行阶梯形
        rank           — 秩
        nullspace      — 零空间
        charpoly       — 特征多项式
        transpose      — 转置
        solve_linear   — 解线性方程组 Ax=b（需 vector 参数）
        svd            — 奇异值分解
        lu             — LU 分解
        qr             — QR 分解
        diagonalize    — 对角化
        jordan         — Jordan 标准形
    vector: 线性方程组右侧向量，格式 '[a,b,c]'，仅 solve_linear 需要。
    """
    try:
        M = _parse_matrix(matrix)

        if operation == "eigenvalues":
            evs = M.eigenvals()
            lines = []
            for val, mult in evs.items():
                lines.append(f"  {_maybe_eval(val)}  (重数: {mult})")
            return "特征值:\n" + "\n".join(lines)

        elif operation == "eigenvectors":
            evs = M.eigenvects()
            if not evs:
                return "(无特征向量)"
            lines = []
            for val, mult, vecs in evs:
                lines.append(f"  特征值 {_maybe_eval(val)} (重数 {mult}):")
                for v in vecs:
                    lines.append(f"    {sstr(v.T)}")
            return "特征向量:\n" + "\n".join(lines)

        elif operation == "determinant":
            return sstr(M.det())

        elif operation == "inverse":
            return sstr(M.inv())

        elif operation == "rref":
            rref_M, pivots = M.rref()
            return f"RREF:\n{sstr(rref_M)}\n主元列: {list(pivots)}"

        elif operation == "rank":
            return str(M.rank())

        elif operation == "nullspace":
            ns = M.nullspace()
            if not ns:
                return "(零空间仅含零向量)"
            lines = [f"零空间维度: {len(ns)}"]
            for v in ns:
                lines.append(f"  {sstr(v.T)}")
            return "\n".join(lines)

        elif operation == "charpoly":
            lam = Symbol("λ")
            return sstr(M.charpoly(lam).as_expr())

        elif operation == "transpose":
            return sstr(M.T)

        elif operation == "solve_linear":
            if not vector:
                return "Error: solve_linear 需要 vector 参数，格式 '[a,b,c]'"
            v = _parse_vector(vector)
            sol = M.LUsolve(v)
            return sstr(sol)

        elif operation == "svd":
            U, S_vals, V = M.singular_value_decomposition()
            lines = [
                f"U:\n{sstr(U)}",
                f"奇异值: {sstr(S_vals)}",
                f"V:\n{sstr(V)}",
            ]
            return "\n\n".join(lines)

        elif operation == "lu":
            L, U, perm = M.LUdecomposition()
            lines = [
                f"L:\n{sstr(L)}",
                f"U:\n{sstr(U)}",
                f"置换: {perm}",
            ]
            return "\n\n".join(lines)

        elif operation == "qr":
            Q, R = M.QRdecomposition()
            return f"Q:\n{sstr(Q)}\n\nR:\n{sstr(R)}"

        elif operation == "diagonalize":
            P, D = M.diagonalize()
            return f"P:\n{sstr(P)}\n\nD:\n{sstr(D)}"

        elif operation == "jordan":
            P, J = M.jordan_form()
            return f"P:\n{sstr(P)}\n\nJ:\n{sstr(J)}"

        else:
            ops = "eigenvalues, eigenvectors, determinant, inverse, rref, rank, nullspace, charpoly, transpose, solve_linear, svd, lu, qr, diagonalize, jordan"
            return f"不支持的操作: {operation}。支持: {ops}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def math_manipulate(expression: str, operation: str = "simplify",
                    variable: str = "") -> str:
    """
    表达式变换与化简。

    expression: 数学表达式。
    operation:
        simplify       — 通用化简
        expand         — 展开
        factor         — 因式分解
        cancel         — 约分有理函数
        apart          — 部分分式分解
        together       — 通分
        collect        — 按变量合并同类项（会用 variable 参数或自动选主变量）
        trigsimp       — 三角化简
        radsimp        — 根式化简
        piecewise_fold — 分段函数折叠
        domain         — 求定义域
    variable: 用于 collect 操作的变量名（可选，不填则自动选第一个自由变量）。
    """
    try:
        expr = _parse(expression)

        if operation == "simplify":
            return sstr(simplify(expr))
        elif operation == "expand":
            return sstr(expand(expr))
        elif operation == "factor":
            return sstr(factor(expr))
        elif operation == "cancel":
            return sstr(cancel(expr))
        elif operation == "apart":
            return sstr(apart(expr))
        elif operation == "together":
            return sstr(together(expr))
        elif operation == "collect":
            if variable.strip():
                return sstr(collect(expr, Symbol(variable.strip())))
            syms = list(expr.free_symbols)
            if syms:
                return sstr(collect(expr, syms[0]))
            return sstr(expr)
        elif operation == "trigsimp":
            return sstr(trigsimp(expr))
        elif operation == "radsimp":
            return sstr(radsimp(expr))
        elif operation == "piecewise_fold":
            return sstr(piecewise_fold(expr))
        elif operation == "domain":
            syms = list(expr.free_symbols)
            if not syms:
                return "(无自由变量)"
            try:
                from sympy import S
                dom = continuous_domain(expr, syms[0], S.Reals)
                return f"定义域: {sstr(dom)}"
            except Exception as e:
                return f"(无法求定义域: {e})"
        else:
            ops = "simplify, expand, factor, cancel, apart, together, collect, trigsimp, radsimp, piecewise_fold, domain"
            return f"不支持的操作: {operation}。支持: {ops}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def math_number_theory(value: str, operation: str = "factor") -> str:
    """
    数论运算。

    value: 整数值或参数，取决于 operation:
           因式分解/factor：'1234567890'
           GCD/LCM：'1234,5678'
           素数范围：'2,100'
           离散对数：'base,value,modulus'
           中国剩余定理：'r1,m1;r2,m2;...'
    operation:
        factor        — 质因数分解
        isprime       — 素数判定
        nextprime     — 下一个素数
        prevprime     — 前一个素数
        totient       — 欧拉函数 φ(n)
        divisors      — 所有因子
        primitiveroot — 最小原根
        gcd           — 最大公约数
        lcm           — 最小公倍数
        fibonacci     — 第 n 个斐波那契数
        bernoulli     — 第 n 个伯努利数
        npartitions   — 整数分拆数
        primorial     — 素数阶乘（前 n 个素数之积）
        primepi       — ≤ n 的素数个数
        prime         — 第 n 个素数
        primerange    — 范围内素数列表（格式 'a,b'）
        crt           — 中国剩余定理（格式 'r1,m1;r2,m2;...'）
        legendre      — Legendre 符号 (a|p)，格式 'a,p'
        jacobi        — Jacobi 符号 (a|n)，格式 'a,n'
    """
    try:
        v = value.strip()

        def _ints(count: int = 2):
            parts = [p.strip() for p in v.split(",")]
            if len(parts) < count:
                raise ValueError(f"需要 {count} 个逗号分隔的整数")
            return [int(_parse(p)) for p in parts]

        if operation == "factor":
            n = int(_parse(v))
            fac = factorint(n)
            if not fac:
                return f"{n} = 1"
            parts = [f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(fac.items())]
            return f"{n} = " + " × ".join(parts)

        elif operation == "isprime":
            n = int(_parse(v))
            return f"{n} 是素数" if isprime(n) else f"{n} 不是素数"

        elif operation == "nextprime":
            n = int(_parse(v))
            return str(nextprime(n))

        elif operation == "prevprime":
            n = int(_parse(v))
            try:
                return str(prevprime(n))
            except ValueError:
                return "(无更小的素数)"

        elif operation == "totient":
            n = int(_parse(v))
            return str(totient(n))

        elif operation == "divisors":
            n = int(_parse(v))
            divs = divisors(n)
            return f"共 {len(divs)} 个因子: {divs}"

        elif operation == "primitiveroot":
            n = int(_parse(v))
            try:
                return str(primitive_root(n))
            except ValueError as e:
                return str(e)

        elif operation == "gcd":
            a, b = _ints(2)
            return str(gcd(a, b))

        elif operation == "lcm":
            a, b = _ints(2)
            return str(lcm(a, b))

        elif operation == "fibonacci":
            n = int(_parse(v))
            return str(fibonacci(n))

        elif operation == "bernoulli":
            n = int(_parse(v))
            return str(bernoulli(n))

        elif operation == "npartitions":
            n = int(_parse(v))
            return str(npartitions(n))

        elif operation == "primorial":
            n = int(_parse(v))
            result = 1
            for p in sieve.primerange(2, prime(n) + 1):
                result *= p
            return str(result)

        elif operation == "primepi":
            n = int(_parse(v))
            return str(primepi(n))

        elif operation == "prime":
            n = int(_parse(v))
            return str(prime(n))

        elif operation == "primerange":
            a, b = _ints(2)
            primes = list(sieve.primerange(a, b + 1))
            if len(primes) <= 50:
                return f"共 {len(primes)} 个素数: {primes}"
            return f"共 {len(primes)} 个素数（前 50 个）: {primes[:50]}..."

        elif operation == "crt":
            remainders = []
            moduli = []
            for part in v.split(";"):
                part = part.strip()
                if not part:
                    continue
                r_s, m_s = part.split(",")
                remainders.append(int(_parse(r_s)))
                moduli.append(int(_parse(m_s)))
            from sympy.ntheory.modular import crt as _crt
            result = _crt(moduli, remainders)
            if result is None:
                return "(无解)"
            return f"x ≡ {result[0]} (mod {result[1]})"

        elif operation == "legendre":
            a_s, p_s = v.split(",")
            a = int(_parse(a_s))
            p = int(_parse(p_s))
            from sympy.ntheory.residue_ntheory import legendre_symbol
            return str(legendre_symbol(a, p))

        elif operation == "jacobi":
            a_s, n_s = v.split(",")
            a = int(_parse(a_s))
            n = int(_parse(n_s))
            from sympy.ntheory.residue_ntheory import jacobi_symbol
            return str(jacobi_symbol(a, n))

        else:
            ops = "factor, isprime, nextprime, prevprime, totient, divisors, primitiveroot, gcd, lcm, fibonacci, bernoulli, npartitions, primorial, primepi, prime, primerange, crt, legendre, jacobi"
            return f"不支持的操作: {operation}。支持: {ops}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def math_statistics(data: str, operation: str = "describe") -> str:
    """
    统计与概率计算。

    data: 数据集或分布描述。
          数据集格式: '[1,2,3,4,5]' 或 '1,2,3,4,5'。
          配对数据（回归/相关）: '[[1,2],[3,4],[5,6]]' 或 '[1,2;3,4;5,6]'。
    operation:
        describe           — 描述性统计（均值、中位数、标准差、极值等）
        mean / median       — 均值 / 中位数
        std / variance      — 标准差 / 方差
        min / max / range   — 最小值 / 最大值 / 极差
        skewness / kurtosis — 偏度 / 峰度
        quantile            — 分位数（需 quantile 参数，如 0.25）
        correlation         — Pearson 相关系数（需配对数据）
        linear_regression   — 简单线性回归 y=ax+b（需配对数据）
    distribution: 概率分布查询，格式 '分布名,参数1=值,参数2=值,x=点'。
                  支持的分布: normal, exponential, binomial, poisson, uniform,
                            gamma, beta, chi2, t, F。
                  示例: 'normal,mu=0,sigma=1,x=1.96'
                  操作: pdf, cdf, quantile, mean, variance, sample(需 n=数量)。
    """
    try:
        d = data.strip()

        # 概率分布模式
        if any(d.lower().startswith(p) for p in
               ("normal", "exponential", "binomial", "poisson", "uniform",
                "gamma", "beta", "chi2", "t", "f", "chisquared")):

            parts = {p.split("=")[0].strip(): p.split("=")[1].strip()
                     for p in d.split(",") if "=" in p}
            dist_name = d.split(",")[0].strip().lower()

            # 创建分布
            dist_map = {
                "normal": Normal, "exponential": Exponential,
                "binomial": Binomial, "poisson": Poisson,
                "uniform": Uniform, "gamma": Gamma,
                "beta": Beta, "chi2": ChiSquared, "chisquared": ChiSquared,
                "t": StudentT, "f": FDistribution,
            }
            if dist_name not in dist_map:
                return f"不支持的分布: {dist_name}。支持: {', '.join(sorted(dist_map))}"

            # 参数名别名映射：用户常用名 → SymPy 期望名
            _PARAM_ALIASES: dict[str, str] = {
                "mu": "mean", "sigma": "std",
                "lambda": "lamda", "lam": "lamda",
                "low": "left", "high": "right",
                "a": "left", "b": "right",
                "df": "nu", "dof": "nu",
                "d1": "d1", "d2": "d2",
            }
            # 按分布覆盖 — chi2 的参数名是 k 不是 nu
            _DIST_OVERRIDES: dict[str, dict[str, str]] = {
                "chi2": {"df": "k", "dof": "k", "nu": "k"},
                "chisquared": {"df": "k", "dof": "k", "nu": "k"},
            }

            # 先确定实际操作（用于区分分布参数和操作参数）
            sub_op = operation if operation in ("pdf", "cdf", "quantile", "mean", "variance", "sample") else "pdf"

            X = Symbol("X")
            dist_class = dist_map[dist_name]
            overrides = _DIST_OVERRIDES.get(dist_name, {})
            kwargs: dict[str, float] = {}
            for k, v in parts.items():
                # x 永远是求值点，不是分布参数
                if k == "x":
                    continue
                # size 在 sample 操作时是样本量，n 仅在无 size 且 sample 操作时视为样本量
                if k == "size" and sub_op == "sample":
                    continue
                if k == "n" and sub_op == "sample" and "size" not in parts:
                    continue
                # q 在 quantile 操作时是分位点，p 仅在无 q 且 quantile 操作时视为分位点
                if k == "q" and sub_op == "quantile":
                    continue
                if k == "p" and sub_op == "quantile" and "q" not in parts:
                    continue
                sympy_key = overrides.get(k) or _PARAM_ALIASES.get(k, k)
                f_val = float(_parse(v).evalf())
                kwargs[sympy_key] = int(f_val) if f_val == int(f_val) else f_val

            dist = dist_class("X", **kwargs)

            if sub_op == "pdf":
                x_val = float(_parse(parts.get("x", "0")).evalf())
                try:
                    d = density(dist)(x_val)
                    if hasattr(d, "doit"):
                        d = d.doit()
                    return str(float(d.evalf()))
                except Exception:
                    return str(float(P(Eq(dist, x_val)).doit().evalf()))
            elif sub_op == "cdf":
                x_val = float(_parse(parts.get("x", "0")).evalf())
                return str(float(cdf(dist)(x_val).evalf()))
            elif sub_op == "quantile":
                q_val = float(parts.get("q", parts.get("p", "0.5")))
                return str(float(quantile(dist)(q_val).evalf()))
            elif sub_op == "mean":
                return str(float(EV(dist).evalf()))
            elif sub_op == "variance":
                return str(float(variance(dist).evalf()))
            elif sub_op == "sample":
                n = int(parts.get("size", parts.get("n", "10")))
                return str([float(x.evalf()) for x in sample(dist, n)])
            else:
                return f"分布操作: pdf, cdf, quantile, mean, variance, sample"

        # 数值数据模式
        if operation in ("correlation", "linear_regression"):
            pairs = _parse_xy_data(d)
            n = len(pairs)
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            mx = sum(xs) / n
            my = sum(ys) / n
            ss_xy = sum((x - mx) * (y - my) for x, y in pairs)
            ss_xx = sum((x - mx) ** 2 for x in xs)
            ss_yy = sum((y - my) ** 2 for y in ys)

            if operation == "correlation":
                if ss_xx == 0 or ss_yy == 0:
                    return "r = 0"
                r = ss_xy / (ss_xx * ss_yy) ** 0.5
                return f"Pearson r = {r:.10f}"

            elif operation == "linear_regression":
                if ss_xx == 0:
                    return "(x 方差为 0，无法回归)"
                a = ss_xy / ss_xx
                b = my - a * mx
                # R²
                ss_res = sum((y - (a * x + b)) ** 2 for x, y in pairs)
                r2 = 1 - ss_res / ss_yy if ss_yy != 0 else 0
                return f"y = {a:.10f} * x + {b:.10f}\nR² = {r2:.10f}"

        # 单变量数据
        vals = _parse_data(d)
        n = len(vals)
        if n == 0:
            return "(空数据集)"

        sorted_vals = sorted(vals)
        mean_val = sum(vals) / n

        if n % 2 == 0:
            median_val = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2
        else:
            median_val = sorted_vals[n // 2]

        var_val = sum((x - mean_val) ** 2 for x in vals) / n
        std_val = var_val ** 0.5

        if operation == "describe":
            lines = [
                f"  样本量: {n}",
                f"  均值:   {mean_val:.10g}",
                f"  中位数: {median_val:.10g}",
                f"  标准差: {std_val:.10g}",
                f"  方差:   {var_val:.10g}",
                f"  最小值: {sorted_vals[0]:.10g}",
                f"  最大值: {sorted_vals[-1]:.10g}",
                f"  总和:   {sum(vals):.10g}",
            ]
            # 偏度、峰度
            if n >= 3:
                m3 = sum((x - mean_val) ** 3 for x in vals) / n
                m4 = sum((x - mean_val) ** 4 for x in vals) / n
                skew = m3 / (std_val ** 3) if std_val > 0 else 0
                kurt = m4 / (var_val ** 2) - 3 if var_val > 0 else 0
                lines.append(f"  偏度:   {skew:.6f}")
                lines.append(f"  峰度:   {kurt:.6f}")

            # 五数概括
            def _quantile(data_sorted, q):
                idx = q * (len(data_sorted) - 1)
                lo = int(idx)
                hi = min(lo + 1, len(data_sorted) - 1)
                frac = idx - lo
                return data_sorted[lo] + frac * (data_sorted[hi] - data_sorted[lo])

            q1 = _quantile(sorted_vals, 0.25)
            q3 = _quantile(sorted_vals, 0.75)
            lines.append(f"  Q1:     {q1:.10g}")
            lines.append(f"  Q3:     {q3:.10g}")
            lines.append(f"  IQR:    {q3 - q1:.10g}")

            return "描述性统计:\n" + "\n".join(lines)

        elif operation == "mean":
            return f"{mean_val:.10g}"
        elif operation == "median":
            return f"{median_val:.10g}"
        elif operation == "std":
            return f"{std_val:.10g}"
        elif operation == "variance":
            return f"{var_val:.10g}"
        elif operation == "min":
            return f"{sorted_vals[0]:.10g}"
        elif operation == "max":
            return f"{sorted_vals[-1]:.10g}"
        elif operation == "range":
            return f"{sorted_vals[-1] - sorted_vals[0]:.10g}"
        elif operation == "skewness":
            m3 = sum((x - mean_val) ** 3 for x in vals) / n
            return f"{m3 / (std_val ** 3) if std_val > 0 else 0:.6f}"
        elif operation == "kurtosis":
            m4 = sum((x - mean_val) ** 4 for x in vals) / n
            return f"{m4 / (var_val ** 2) - 3 if var_val > 0 else 0:.6f}"
        elif operation == "quantile":
            return "quantile 操作需要指定分位点参数，请使用分布查询格式"
        else:
            ops = "describe, mean, median, std, variance, min, max, range, skewness, kurtosis, correlation, linear_regression"
            return f"不支持的操作: {operation}。支持: {ops}"
    except Exception as e:
        return f"Error: {e}"


# ── 单位换算与常数 ──────────────────────────────────────────────────────────────

# 所有单位换算到 SI 基准，再换算到目标单位
_SI_FACTORS: dict[str, float] = {
    # 长度 (基准: m)
    "m": 1.0, "meter": 1.0, "meters": 1.0,
    "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0,
    "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
    "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
    "um": 1e-6, "micrometer": 1e-6, "micron": 1e-6,
    "nm": 1e-9, "nanometer": 1e-9, "nanometers": 1e-9,
    "angstrom": 1e-10, "ang": 1e-10,
    "mile": 1609.344, "miles": 1609.344, "mi": 1609.344,
    "yard": 0.9144, "yards": 0.9144, "yd": 0.9144,
    "foot": 0.3048, "feet": 0.3048, "ft": 0.3048,
    "inch": 0.0254, "inches": 0.0254, "in": 0.0254,
    "nautical_mile": 1852.0, "nmi": 1852.0,
    "light_year": 9.4607304725808e15, "ly": 9.4607304725808e15,
    "au": 1.495978707e11, "astronomical_unit": 1.495978707e11,
    "pc": 3.085677581e16, "parsec": 3.085677581e16,
    # 质量 (基准: kg)
    "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
    "g": 0.001, "gram": 0.001, "grams": 0.001,
    "mg": 1e-6, "milligram": 1e-6, "milligrams": 1e-6,
    "ug": 1e-9, "microgram": 1e-9, "micrograms": 1e-9,
    "ton": 1000.0, "tonne": 1000.0, "metric_ton": 1000.0,
    "ton_us": 907.18474, "us_ton": 907.18474, "short_ton": 907.18474,
    "lb": 0.45359237, "lbs": 0.45359237, "pound": 0.45359237, "pounds": 0.45359237,
    "oz": 0.028349523125, "ounce": 0.028349523125, "ounces": 0.028349523125,
    # 时间 (基准: s)
    "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0,
    "min": 60.0, "minute": 60.0, "minutes": 60.0,
    "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "hours": 3600.0,
    "day": 86400.0, "days": 86400.0,
    "week": 604800.0, "weeks": 604800.0,
    "year": 31557600.0, "years": 31557600.0,  # 365.25 days
    # 温度有特殊处理
    # 速度 (基准: m/s)
    "m/s": 1.0, "mps": 1.0,
    "km/h": 0.2777777777777778, "kmh": 0.2777777777777778, "kph": 0.2777777777777778,
    "mph": 0.44704, "mi/h": 0.44704,
    "knot": 0.5144444444444444, "kn": 0.5144444444444444,
    # 力 (基准: N)
    "N": 1.0, "newton": 1.0, "newtons": 1.0,
    "kN": 1000.0, "kilonewton": 1000.0,
    "lbf": 4.4482216152605, "pound_force": 4.4482216152605,
    "dyne": 1e-5,
    # 能量 (基准: J)
    "J": 1.0, "joule": 1.0, "joules": 1.0,
    "kJ": 1000.0, "kilojoule": 1000.0,
    "cal": 4.184, "calorie": 4.184, "calories": 4.184,
    "kcal": 4184.0, "Calorie": 4184.0, "Calories": 4184.0,
    "Wh": 3600.0, "watt_hour": 3600.0,
    "kWh": 3_600_000.0, "kilowatt_hour": 3_600_000.0,
    "eV": 1.602176634e-19, "electron_volt": 1.602176634e-19,
    "MeV": 1.602176634e-13,
    "GeV": 1.602176634e-10,
    "erg": 1e-7,
    # 功率 (基准: W)
    "W": 1.0, "watt": 1.0, "watts": 1.0,
    "kW": 1000.0, "kilowatt": 1000.0,
    "MW": 1e6, "megawatt": 1e6,
    "GW": 1e9, "gigawatt": 1e9,
    "hp": 745.6998715822702, "horsepower": 745.6998715822702,
    # 压强 (基准: Pa)
    "Pa": 1.0, "pascal": 1.0,
    "kPa": 1000.0, "kilopascal": 1000.0,
    "MPa": 1e6, "megapascal": 1e6,
    "atm": 101325.0, "atmosphere": 101325.0,
    "bar": 100000.0,
    "mbar": 100.0, "millibar": 100.0,
    "mmHg": 133.322368421, "torr": 133.322368421,
    "psi": 6894.757293168, "lb/in2": 6894.757293168,
    # 面积 (基准: m^2)
    "m2": 1.0, "sq_m": 1.0,
    "km2": 1e6, "sq_km": 1e6,
    "cm2": 1e-4, "sq_cm": 1e-4,
    "mm2": 1e-6, "sq_mm": 1e-6,
    "ha": 10000.0, "hectare": 10000.0,
    "acre": 4046.8564224, "acres": 4046.8564224,
    "sq_ft": 0.09290304, "ft2": 0.09290304, "square_foot": 0.09290304, "square_feet": 0.09290304,
    "sq_in": 0.00064516, "in2": 0.00064516, "square_inch": 0.00064516, "square_inches": 0.00064516,
    "sq_mi": 2.58998811e6, "mi2": 2.58998811e6, "square_mile": 2.58998811e6,
    # 体积 (基准: m^3)
    "m3": 1.0, "cubic_meter": 1.0,
    "L": 0.001, "liter": 0.001, "liters": 0.001, "litre": 0.001,
    "mL": 1e-6, "ml": 1e-6, "milliliter": 1e-6, "milliliters": 1e-6,
    "gal_us": 0.003785411784, "gallon": 0.003785411784, "gallons": 0.003785411784,
    "gal_uk": 0.00454609, "imperial_gallon": 0.00454609,
    "qt": 0.000946352946, "quart": 0.000946352946, "quarts": 0.000946352946,
    "pt": 0.000473176473, "pint": 0.000473176473, "pints": 0.000473176473,
    "cup": 0.0002365882365,
    "fl_oz": 2.95735295625e-5, "fluid_ounce": 2.95735295625e-5,
    # 角度 (基准: rad)
    "rad": 1.0, "radian": 1.0, "radians": 1.0,
    "deg": math.pi / 180, "degree": math.pi / 180, "degrees": math.pi / 180,
    "grad": math.pi / 200, "gon": math.pi / 200,
    "arcmin": math.pi / 10800, "arc_minute": math.pi / 10800,
    "arcsec": math.pi / 648000, "arc_second": math.pi / 648000,
    # 频率 (基准: Hz)
    "Hz": 1.0, "hertz": 1.0,
    "kHz": 1000.0, "kilohertz": 1000.0,
    "MHz": 1e6, "megahertz": 1e6,
    "GHz": 1e9, "gigahertz": 1e9,
    "rpm": 1.0 / 60,
    # 数据量 (基准: bit)
    "bit": 1.0,
    "byte": 8.0, "B": 8.0,
    "KB": 8_000.0, "kilobyte": 8_000.0,
    "MB": 8_000_000.0, "megabyte": 8_000_000.0,
    "GB": 8_000_000_000.0, "gigabyte": 8_000_000_000.0,
    "TB": 8_000_000_000_000.0, "terabyte": 8_000_000_000_000.0,
    "KiB": 8192.0, "kib": 8192.0, "kibibyte": 8192.0,
    "MiB": 8_388_608.0, "mib": 8_388_608.0, "mebibyte": 8_388_608.0,
    "GiB": 8_589_934_592.0, "gib": 8_589_934_592.0, "gibibyte": 8_589_934_592.0,
    "TiB": 8_796_093_022_208.0, "tib": 8_796_093_022_208.0, "tebibyte": 8_796_093_022_208.0,
    # 浓度 / 其他
    "mol": 1.0, "mole": 1.0, "moles": 1.0,
    "mmol": 0.001, "millimole": 0.001,
    "M": 1.0, "molar": 1.0, "mol/L": 1.0,
    "mM": 0.001, "millimolar": 0.001,
}

# 温度需要特殊处理
_TEMP_UNITS = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}


def _celsius_to_si(val: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("c", "celsius"):
        return val + 273.15
    if unit in ("f", "fahrenheit"):
        return (val - 32) * 5 / 9 + 273.15
    if unit in ("k", "kelvin"):
        return val
    raise ValueError(f"未知温度单位: {unit}")


def _si_to_celsius(val: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("c", "celsius"):
        return val - 273.15
    if unit in ("f", "fahrenheit"):
        return (val - 273.15) * 9 / 5 + 32
    if unit in ("k", "kelvin"):
        return val
    raise ValueError(f"未知温度单位: {unit}")


_PHYSICAL_CONSTANTS: dict[str, tuple[str, str]] = {
    # (名称, 值, 单位)
    "pi": ("圆周率 π", "3.1415926535897932384626433832795028841971693993751..."),
    "e": ("自然常数 e", "2.7182818284590452353602874713526624977572470936999..."),
    "golden_ratio": ("黄金比例 φ", "1.6180339887498948482045868343656381177203091798057..."),
    "euler_mascheroni": ("Euler-Mascheroni 常数 γ", "0.5772156649015328606065120900824024310421593359399..."),
    "speed_of_light": ("真空光速 c", "299792458 m/s"),
    "planck_constant": ("Planck 常数 h", "6.62607015e-34 J·s"),
    "reduced_planck": ("约化 Planck 常数 ħ", "1.054571817e-34 J·s"),
    "gravitational_constant": ("万有引力常数 G", "6.67430e-11 N·m²/kg²"),
    "acceleration_due_to_gravity": ("标准重力加速度 g", "9.80665 m/s²"),
    "avogadro_number": ("Avogadro 常数 N_A", "6.02214076e23 mol⁻¹"),
    "boltzmann_constant": ("Boltzmann 常数 k_B", "1.380649e-23 J/K"),
    "gas_constant": ("理想气体常数 R", "8.314462618 J/(mol·K)"),
    "elementary_charge": ("基本电荷 e", "1.602176634e-19 C"),
    "electron_mass": ("电子质量 m_e", "9.1093837015e-31 kg"),
    "proton_mass": ("质子质量 m_p", "1.67262192369e-27 kg"),
    "neutron_mass": ("中子质量 m_n", "1.67492749804e-27 kg"),
    "bohr_radius": ("Bohr 半径 a_0", "5.29177210903e-11 m"),
    "rydberg_constant": ("Rydberg 常数 R_∞", "10973731.568160 m⁻¹"),
    "fine_structure": ("精细结构常数 α", "1/137.035999084"),
    "stefan_boltzmann": ("Stefan-Boltzmann 常数 σ", "5.670374419e-8 W/(m²·K⁴)"),
    "vacuum_permittivity": ("真空介电常数 ε_0", "8.8541878128e-12 F/m"),
    "vacuum_permeability": ("真空磁导率 μ_0", "1.25663706212e-6 N/A²"),
    "wien_displacement": ("Wien 位移常数 b", "2.897771955e-3 m·K"),
    "hartree_energy": ("Hartree 能量 E_h", "4.3597447222071e-18 J"),
    "atomic_mass_unit": ("原子质量单位 u", "1.66053906660e-27 kg"),
    "faraday_constant": ("Faraday 常数 F", "96485.33212 C/mol"),
    "molar_volume": ("理想气体摩尔体积 V_m (STP)", "0.02241396954 m³/mol"),
    "solar_mass": ("太阳质量 M_☉", "1.98847e30 kg"),
    "earth_mass": ("地球质量 M_⊕", "5.9722e24 kg"),
    "solar_luminosity": ("太阳光度 L_☉", "3.828e26 W"),
    "astronomical_unit_value": ("天文单位 AU", "149597870700 m"),
    "parsec_value": ("秒差距 pc", "3.0856775814913673e16 m"),
    "light_year_value": ("光年 ly", "9460730472580800 m"),
    "hubble_constant": ("Hubble 常数 H_0", "≈ 70 km/s/Mpc"),
    "cosmic_microwave_bg": ("宇宙微波背景温度 T_CMB", "2.72548 K"),
}


@mcp.tool()
def math_convert(value: str = "", unit_from: str = "", unit_to: str = "",
                 constant: str = "") -> str:
    """
    单位换算或物理常数查询。

    value: 数值，如 '100'。
    unit_from: 源单位，如 'miles'。
    unit_to: 目标单位，如 'km'。
    constant: 查询物理/数学常数名称。留空则列出所有可用常数。

    示例:
        math_convert(value='100', unit_from='miles', unit_to='km')
        math_convert(value='32', unit_from='F', unit_to='C')
        math_convert(constant='speed_of_light')
        math_convert(constant='')  ← 列出所有常数

    支持的单位类别: 长度、质量、时间、温度、速度、力、能量、功率、压强、
                   面积、体积、角度、频率、数据量、浓度。
    """
    try:
        # 常数查询
        if constant is not None and constant.strip():
            name = constant.strip().lower().replace(" ", "_")
            if name in _PHYSICAL_CONSTANTS:
                desc, val = _PHYSICAL_CONSTANTS[name]
                return f"{val}"
            # 模糊搜索
            matches = [(k, v) for k, v in _PHYSICAL_CONSTANTS.items() if name in k]
            if len(matches) == 1:
                desc, val = matches[0][1]
                return f"{matches[0][0]}: {val}"
            if len(matches) > 1:
                lines = [f"找到 {len(matches)} 个匹配:"]
                for k, (desc, val) in matches[:10]:
                    lines.append(f"  {k}: {val}")
                return "\n".join(lines)
            # 列出所有
            lines = ["可用常数:"]
            for k, (desc, val) in sorted(_PHYSICAL_CONSTANTS.items()):
                lines.append(f"  {k} — {desc}: {val}")
            return "\n".join(lines)

        # 单位换算
        if value and unit_from and unit_to:
            val = float(_parse(value).evalf())
            uf = unit_from.strip().lower()
            ut = unit_to.strip().lower()

            # 温度特殊处理
            if uf in _TEMP_UNITS and ut in _TEMP_UNITS:
                si = _celsius_to_si(val, uf)
                result = _si_to_celsius(si, ut)
                return f"{val} {unit_from} = {result:.6g} {unit_to}"

            if uf not in _SI_FACTORS:
                return f"未知源单位: {unit_from}。可用 math_convert(constant='') 改为查看常数列表。"
            if ut not in _SI_FACTORS:
                return f"未知目标单位: {unit_to}。"

            si_val = val * _SI_FACTORS[uf]
            result = si_val / _SI_FACTORS[ut]
            # 选择合适的精度
            if abs(result) < 0.01 or abs(result) > 1e10:
                fmt = f"{result:.10g}"
            else:
                fmt = f"{result:.6g}"
            return f"{val} {unit_from} = {fmt} {unit_to}"

        # 列出单位
        lines = ["可用单位（按类别）:"]
        categories = {
            "长度": ["m", "km", "cm", "mm", "um", "nm", "angstrom", "mile", "yard", "foot", "inch", "nautical_mile", "light_year", "au", "parsec"],
            "质量": ["kg", "g", "mg", "ug", "ton", "ton_us", "lb", "oz"],
            "时间": ["s", "min", "h", "day", "week", "year"],
            "温度": ["C (celsius)", "F (fahrenheit)", "K (kelvin)"],
            "速度": ["m/s", "km/h", "mph", "knot"],
            "力": ["N", "kN", "lbf", "dyne"],
            "能量": ["J", "kJ", "cal", "kcal", "Wh", "kWh", "eV", "MeV", "GeV", "erg"],
            "功率": ["W", "kW", "MW", "GW", "hp"],
            "压强": ["Pa", "kPa", "MPa", "atm", "bar", "mbar", "mmHg", "torr", "psi"],
            "面积": ["m2", "km2", "ha", "acre", "sq_ft", "sq_in"],
            "体积": ["L", "mL", "gal_us", "gal_uk", "qt", "pt", "cup", "fl_oz"],
            "角度": ["rad", "deg", "grad", "arcmin", "arcsec"],
            "频率": ["Hz", "kHz", "MHz", "GHz", "rpm"],
            "数据量": ["bit", "B", "KB", "MB", "GB", "TB", "KiB", "MiB", "GiB", "TiB"],
        }
        for cat, units in categories.items():
            lines.append(f"  {cat}: {', '.join(units)}")
        lines.append("")
        lines.append("用法: math_convert(value='100', unit_from='miles', unit_to='km')")
        lines.append("温度: math_convert(value='32', unit_from='F', unit_to='C')")
        lines.append("常数: math_convert(constant='speed_of_light')")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"


# ── 入口 ────────────────────────────────────────────────────────────────────────

def main():
    """CLI 入口：支持 stdio 和 streamable-http 两种传输模式。"""
    import argparse

    parser = argparse.ArgumentParser(description="Math MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="传输模式 (默认: stdio)",
    )
    args = parser.parse_args()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

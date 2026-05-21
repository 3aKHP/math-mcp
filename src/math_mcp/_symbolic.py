"""
math_mcp._symbolic
符号计算工具：math_eval, math_solve, math_calculus, math_manipulate
"""
from __future__ import annotations

from sympy import (
    Derivative,
    Eq,
    Function,
    I,
    Integral,
    Limit,
    Product,
    Sum,
    Symbol,
    apart,
    cancel,
    collect,
    diff,
    dsolve,
    expand,
    factor,
    integrate,
    limit,
    oo,
    piecewise_fold,
    radsimp,
    series,
    simplify,
    solve,
    sstr,
    symbols,
    together,
    trigsimp,
)
from sympy.calculus.util import continuous_domain

from ._parse import _extract_func_names, _maybe_eval, _parse, _parse_subs

from .server import mcp


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

"""
math_mcp._statistics
统计与概率工具：math_statistics
"""
from __future__ import annotations

from sympy import Eq, Symbol
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
    quantile,
    sample,
    variance,
)

from ._parse import _parse, _parse_data, _parse_xy_data

from .server import mcp


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

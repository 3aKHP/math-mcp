"""
math_mcp._matrix
线性代数工具：math_matrix
"""
from __future__ import annotations

from sympy import Matrix, Symbol, sstr

from ._parse import _maybe_eval, _parse_matrix, _parse_vector

from .server import mcp


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

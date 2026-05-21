from math_mcp.server import math_solve


def test_quadratic():
    result = math_solve(equation="x^2 - 4 = 0")
    assert "2" in result
    assert "-2" in result


def test_implicit_zero():
    result = math_solve(equation="x^2 - 9")
    assert "3" in result
    assert "-3" in result


def test_system_of_equations():
    result = math_solve(equation="x + y = 10, 2*x - y = 5", variables="x,y")
    assert "x=5" in result
    assert "y=5" in result


def test_no_solution():
    result = math_solve(equation="x^2 + 1 = 0", variables="x")
    # Over reals, sympy returns -I and I
    assert "I" in result or "无解" in result


def test_differential_equation():
    result = math_solve(
        equation="Derivative(f(x),x) + f(x)",
        variables="x",
        equation_type="differential",
        function="f",
    )
    assert "exp" in result or "C1" in result

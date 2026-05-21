from math_mcp.server import math_manipulate


def test_simplify():
    result = math_manipulate(expression="x^2 + 2*x + x^2", operation="simplify")
    assert "2*x**2 + 2*x" in result or "2*x*(x + 1)" in result


def test_expand():
    result = math_manipulate(expression="(x + 1)^2", operation="expand")
    assert "x**2 + 2*x + 1" in result


def test_factor():
    result = math_manipulate(expression="x^2 - 1", operation="factor")
    assert "(x - 1)*(x + 1)" in result or "(x + 1)*(x - 1)" in result


def test_cancel():
    result = math_manipulate(expression="(x^2 - 1)/(x - 1)", operation="cancel")
    assert "x + 1" in result


def test_apart():
    result = math_manipulate(expression="1/(x^2 - 1)", operation="apart")
    assert "1/(2*(x - 1))" in result or "-1/(2*(x + 1))" in result


def test_trigsimp():
    result = math_manipulate(expression="sin(x)^2 + cos(x)^2", operation="trigsimp")
    assert "1" in result


def test_unsupported_operation():
    result = math_manipulate(expression="x", operation="foobar")
    assert "不支持" in result

from math_mcp.server import math_calculus


def test_indefinite_integral():
    result = math_calculus(expression="x^2", operation="integrate")
    assert "x**3/3" in result


def test_definite_integral():
    result = math_calculus(expression="x^2", operation="integrate", lower="0", upper="1")
    assert "1/3" in result


def test_derivative():
    result = math_calculus(expression="x^3", operation="differentiate")
    assert "3*x**2" in result


def test_higher_order_derivative():
    result = math_calculus(expression="x^4", operation="differentiate", order=2)
    assert "12*x**2" in result


def test_limit():
    result = math_calculus(expression="sin(x)/x", operation="limit", point="0")
    assert "1" in result


def test_series_expansion():
    result = math_calculus(expression="exp(x)", operation="series", order=4)
    assert "x**2/2" in result

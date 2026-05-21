from math_mcp.server import math_eval


def test_basic_arithmetic():
    result = math_eval(expression="2 + 3 * 4")
    assert "14" in result


def test_sqrt_precision():
    result = math_eval(expression="sqrt(2)", precision=10)
    assert "1.414213562" in result


def test_trig_identity():
    result = math_eval(expression="sin(pi/6) + cos(pi/3)")
    assert "1" in result


def test_substitutions():
    result = math_eval(expression="x^2 + 1", substitutions="x=3")
    assert "10" in result


def test_complex_number():
    result = math_eval(expression="(1 + I) * (1 - I)")
    assert "2" in result


def test_empty_expression_error():
    result = math_eval(expression="")
    assert "Error" in result

from math_mcp.server import math_number_theory


def test_factor():
    result = math_number_theory(value="1234567890", operation="factor")
    assert "2" in result and "3" in result and "5" in result


def test_isprime_true():
    result = math_number_theory(value="17", operation="isprime")
    assert "是素数" in result


def test_isprime_false():
    result = math_number_theory(value="15", operation="isprime")
    assert "不是素数" in result


def test_nextprime():
    result = math_number_theory(value="10", operation="nextprime")
    assert "11" in result


def test_totient():
    result = math_number_theory(value="12", operation="totient")
    assert "4" in result


def test_gcd():
    result = math_number_theory(value="12,18", operation="gcd")
    assert "6" in result


def test_lcm():
    result = math_number_theory(value="4,6", operation="lcm")
    assert "12" in result


def test_fibonacci():
    result = math_number_theory(value="10", operation="fibonacci")
    assert "55" in result


def test_divisors():
    result = math_number_theory(value="12", operation="divisors")
    assert "6" in result  # 12 has 6 divisors: 1,2,3,4,6,12

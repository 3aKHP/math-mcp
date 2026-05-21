from math_mcp.server import math_statistics


def test_describe():
    result = math_statistics(data="[1,2,3,4,5]", operation="describe")
    assert "样本量: 5" in result
    assert "均值" in result
    assert "3" in result


def test_mean():
    result = math_statistics(data="[10,20,30]", operation="mean")
    assert "20" in result


def test_median():
    result = math_statistics(data="[1,3,5,7,9]", operation="median")
    assert "5" in result


def test_std():
    result = math_statistics(data="[2,4,4,4,5,5,7,9]", operation="std")
    assert "2" in result  # std = 2.0


def test_correlation():
    result = math_statistics(data="[[1,2],[2,4],[3,6]]", operation="correlation")
    assert "1" in result  # perfect correlation


def test_linear_regression():
    result = math_statistics(data="[[1,2],[2,4],[3,6]]", operation="linear_regression")
    assert "y =" in result
    assert "2" in result  # slope = 2


def test_empty_data():
    result = math_statistics(data="[]", operation="describe")
    assert "空" in result


def test_normal_distribution_pdf():
    result = math_statistics(data="normal,mu=0,sigma=1,x=0", operation="pdf")
    # pdf of N(0,1) at x=0 is 1/sqrt(2*pi) ≈ 0.3989
    assert "0.3989" in result

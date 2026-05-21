from math_mcp.server import math_matrix


def test_eigenvalues():
    result = math_matrix(matrix="[[1,2],[3,4]]", operation="eigenvalues")
    assert "特征值" in result


def test_determinant():
    result = math_matrix(matrix="[[1,2],[3,4]]", operation="determinant")
    assert "-2" in result


def test_inverse():
    result = math_matrix(matrix="[[1,2],[3,4]]", operation="inverse")
    assert "Matrix" in result or "-2" in result or "1/2" in result


def test_rank():
    result = math_matrix(matrix="[[1,2],[2,4]]", operation="rank")
    assert "1" in result


def test_solve_linear():
    result = math_matrix(matrix="[[1,0],[0,1]]", operation="solve_linear", vector="[3,5]")
    assert "3" in result
    assert "5" in result


def test_transpose():
    result = math_matrix(matrix="[[1,2],[3,4]]", operation="transpose")
    assert "Matrix" in result


def test_unsupported_operation():
    result = math_matrix(matrix="[[1,2],[3,4]]", operation="foobar")
    assert "不支持" in result

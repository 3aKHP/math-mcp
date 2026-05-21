from math_mcp.server import math_convert


def test_miles_to_km():
    result = math_convert(value="100", unit_from="miles", unit_to="km")
    assert "160.934" in result or "160.9" in result


def test_fahrenheit_to_celsius():
    result = math_convert(value="32", unit_from="F", unit_to="C")
    assert "0" in result


def test_celsius_to_fahrenheit():
    result = math_convert(value="100", unit_from="C", unit_to="F")
    assert "212" in result


def test_kg_to_lb():
    result = math_convert(value="1", unit_from="kg", unit_to="lb")
    assert "2.204" in result


def test_constant_speed_of_light():
    result = math_convert(constant="speed_of_light")
    assert "299792458" in result


def test_constant_fuzzy_search():
    result = math_convert(constant="planck")
    assert "Planck" in result or "planck" in result


def test_unknown_unit():
    result = math_convert(value="1", unit_from="foo", unit_to="bar")
    assert "未知" in result or "Error" in result


def test_list_units():
    result = math_convert()
    assert "长度" in result
    assert "质量" in result

"""
math_mcp._convert
单位换算与物理常数：math_convert
"""
from __future__ import annotations

import math

from ._parse import _parse

from .server import mcp

# ── 单位换算与常数 ──────────────────────────────────────────────────────────────

# 所有单位换算到 SI 基准，再换算到目标单位
_SI_FACTORS: dict[str, float] = {
    # 长度 (基准: m)
    "m": 1.0, "meter": 1.0, "meters": 1.0,
    "km": 1000.0, "kilometer": 1000.0, "kilometers": 1000.0,
    "cm": 0.01, "centimeter": 0.01, "centimeters": 0.01,
    "mm": 0.001, "millimeter": 0.001, "millimeters": 0.001,
    "um": 1e-6, "micrometer": 1e-6, "micron": 1e-6,
    "nm": 1e-9, "nanometer": 1e-9, "nanometers": 1e-9,
    "angstrom": 1e-10, "ang": 1e-10,
    "mile": 1609.344, "miles": 1609.344, "mi": 1609.344,
    "yard": 0.9144, "yards": 0.9144, "yd": 0.9144,
    "foot": 0.3048, "feet": 0.3048, "ft": 0.3048,
    "inch": 0.0254, "inches": 0.0254, "in": 0.0254,
    "nautical_mile": 1852.0, "nmi": 1852.0,
    "light_year": 9.4607304725808e15, "ly": 9.4607304725808e15,
    "au": 1.495978707e11, "astronomical_unit": 1.495978707e11,
    "pc": 3.085677581e16, "parsec": 3.085677581e16,
    # 质量 (基准: kg)
    "kg": 1.0, "kilogram": 1.0, "kilograms": 1.0,
    "g": 0.001, "gram": 0.001, "grams": 0.001,
    "mg": 1e-6, "milligram": 1e-6, "milligrams": 1e-6,
    "ug": 1e-9, "microgram": 1e-9, "micrograms": 1e-9,
    "ton": 1000.0, "tonne": 1000.0, "metric_ton": 1000.0,
    "ton_us": 907.18474, "us_ton": 907.18474, "short_ton": 907.18474,
    "lb": 0.45359237, "lbs": 0.45359237, "pound": 0.45359237, "pounds": 0.45359237,
    "oz": 0.028349523125, "ounce": 0.028349523125, "ounces": 0.028349523125,
    # 时间 (基准: s)
    "s": 1.0, "sec": 1.0, "second": 1.0, "seconds": 1.0,
    "min": 60.0, "minute": 60.0, "minutes": 60.0,
    "h": 3600.0, "hr": 3600.0, "hour": 3600.0, "hours": 3600.0,
    "day": 86400.0, "days": 86400.0,
    "week": 604800.0, "weeks": 604800.0,
    "year": 31557600.0, "years": 31557600.0,  # 365.25 days
    # 温度有特殊处理
    # 速度 (基准: m/s)
    "m/s": 1.0, "mps": 1.0,
    "km/h": 0.2777777777777778, "kmh": 0.2777777777777778, "kph": 0.2777777777777778,
    "mph": 0.44704, "mi/h": 0.44704,
    "knot": 0.5144444444444444, "kn": 0.5144444444444444,
    # 力 (基准: N)
    "N": 1.0, "newton": 1.0, "newtons": 1.0,
    "kN": 1000.0, "kilonewton": 1000.0,
    "lbf": 4.4482216152605, "pound_force": 4.4482216152605,
    "dyne": 1e-5,
    # 能量 (基准: J)
    "J": 1.0, "joule": 1.0, "joules": 1.0,
    "kJ": 1000.0, "kilojoule": 1000.0,
    "cal": 4.184, "calorie": 4.184, "calories": 4.184,
    "kcal": 4184.0, "Calorie": 4184.0, "Calories": 4184.0,
    "Wh": 3600.0, "watt_hour": 3600.0,
    "kWh": 3_600_000.0, "kilowatt_hour": 3_600_000.0,
    "eV": 1.602176634e-19, "electron_volt": 1.602176634e-19,
    "MeV": 1.602176634e-13,
    "GeV": 1.602176634e-10,
    "erg": 1e-7,
    # 功率 (基准: W)
    "W": 1.0, "watt": 1.0, "watts": 1.0,
    "kW": 1000.0, "kilowatt": 1000.0,
    "MW": 1e6, "megawatt": 1e6,
    "GW": 1e9, "gigawatt": 1e9,
    "hp": 745.6998715822702, "horsepower": 745.6998715822702,
    # 压强 (基准: Pa)
    "Pa": 1.0, "pascal": 1.0,
    "kPa": 1000.0, "kilopascal": 1000.0,
    "MPa": 1e6, "megapascal": 1e6,
    "atm": 101325.0, "atmosphere": 101325.0,
    "bar": 100000.0,
    "mbar": 100.0, "millibar": 100.0,
    "mmHg": 133.322368421, "torr": 133.322368421,
    "psi": 6894.757293168, "lb/in2": 6894.757293168,
    # 面积 (基准: m^2)
    "m2": 1.0, "sq_m": 1.0,
    "km2": 1e6, "sq_km": 1e6,
    "cm2": 1e-4, "sq_cm": 1e-4,
    "mm2": 1e-6, "sq_mm": 1e-6,
    "ha": 10000.0, "hectare": 10000.0,
    "acre": 4046.8564224, "acres": 4046.8564224,
    "sq_ft": 0.09290304, "ft2": 0.09290304, "square_foot": 0.09290304, "square_feet": 0.09290304,
    "sq_in": 0.00064516, "in2": 0.00064516, "square_inch": 0.00064516, "square_inches": 0.00064516,
    "sq_mi": 2.58998811e6, "mi2": 2.58998811e6, "square_mile": 2.58998811e6,
    # 体积 (基准: m^3)
    "m3": 1.0, "cubic_meter": 1.0,
    "L": 0.001, "liter": 0.001, "liters": 0.001, "litre": 0.001,
    "mL": 1e-6, "ml": 1e-6, "milliliter": 1e-6, "milliliters": 1e-6,
    "gal_us": 0.003785411784, "gallon": 0.003785411784, "gallons": 0.003785411784,
    "gal_uk": 0.00454609, "imperial_gallon": 0.00454609,
    "qt": 0.000946352946, "quart": 0.000946352946, "quarts": 0.000946352946,
    "pt": 0.000473176473, "pint": 0.000473176473, "pints": 0.000473176473,
    "cup": 0.0002365882365,
    "fl_oz": 2.95735295625e-5, "fluid_ounce": 2.95735295625e-5,
    # 角度 (基准: rad)
    "rad": 1.0, "radian": 1.0, "radians": 1.0,
    "deg": math.pi / 180, "degree": math.pi / 180, "degrees": math.pi / 180,
    "grad": math.pi / 200, "gon": math.pi / 200,
    "arcmin": math.pi / 10800, "arc_minute": math.pi / 10800,
    "arcsec": math.pi / 648000, "arc_second": math.pi / 648000,
    # 频率 (基准: Hz)
    "Hz": 1.0, "hertz": 1.0,
    "kHz": 1000.0, "kilohertz": 1000.0,
    "MHz": 1e6, "megahertz": 1e6,
    "GHz": 1e9, "gigahertz": 1e9,
    "rpm": 1.0 / 60,
    # 数据量 (基准: bit)
    "bit": 1.0,
    "byte": 8.0, "B": 8.0,
    "KB": 8_000.0, "kilobyte": 8_000.0,
    "MB": 8_000_000.0, "megabyte": 8_000_000.0,
    "GB": 8_000_000_000.0, "gigabyte": 8_000_000_000.0,
    "TB": 8_000_000_000_000.0, "terabyte": 8_000_000_000_000.0,
    "KiB": 8192.0, "kib": 8192.0, "kibibyte": 8192.0,
    "MiB": 8_388_608.0, "mib": 8_388_608.0, "mebibyte": 8_388_608.0,
    "GiB": 8_589_934_592.0, "gib": 8_589_934_592.0, "gibibyte": 8_589_934_592.0,
    "TiB": 8_796_093_022_208.0, "tib": 8_796_093_022_208.0, "tebibyte": 8_796_093_022_208.0,
    # 浓度 / 其他
    "mol": 1.0, "mole": 1.0, "moles": 1.0,
    "mmol": 0.001, "millimole": 0.001,
    "M": 1.0, "molar": 1.0, "mol/L": 1.0,
    "mM": 0.001, "millimolar": 0.001,
}

# 温度需要特殊处理
_TEMP_UNITS = {"c", "celsius", "f", "fahrenheit", "k", "kelvin"}


def _celsius_to_si(val: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("c", "celsius"):
        return val + 273.15
    if unit in ("f", "fahrenheit"):
        return (val - 32) * 5 / 9 + 273.15
    if unit in ("k", "kelvin"):
        return val
    raise ValueError(f"未知温度单位: {unit}")


def _si_to_celsius(val: float, unit: str) -> float:
    unit = unit.lower()
    if unit in ("c", "celsius"):
        return val - 273.15
    if unit in ("f", "fahrenheit"):
        return (val - 273.15) * 9 / 5 + 32
    if unit in ("k", "kelvin"):
        return val
    raise ValueError(f"未知温度单位: {unit}")


_PHYSICAL_CONSTANTS: dict[str, tuple[str, str]] = {
    # (名称, 值, 单位)
    "pi": ("圆周率 π", "3.1415926535897932384626433832795028841971693993751..."),
    "e": ("自然常数 e", "2.7182818284590452353602874713526624977572470936999..."),
    "golden_ratio": ("黄金比例 φ", "1.6180339887498948482045868343656381177203091798057..."),
    "euler_mascheroni": ("Euler-Mascheroni 常数 γ", "0.5772156649015328606065120900824024310421593359399..."),
    "speed_of_light": ("真空光速 c", "299792458 m/s"),
    "planck_constant": ("Planck 常数 h", "6.62607015e-34 J·s"),
    "reduced_planck": ("约化 Planck 常数 ħ", "1.054571817e-34 J·s"),
    "gravitational_constant": ("万有引力常数 G", "6.67430e-11 N·m²/kg²"),
    "acceleration_due_to_gravity": ("标准重力加速度 g", "9.80665 m/s²"),
    "avogadro_number": ("Avogadro 常数 N_A", "6.02214076e23 mol⁻¹"),
    "boltzmann_constant": ("Boltzmann 常数 k_B", "1.380649e-23 J/K"),
    "gas_constant": ("理想气体常数 R", "8.314462618 J/(mol·K)"),
    "elementary_charge": ("基本电荷 e", "1.602176634e-19 C"),
    "electron_mass": ("电子质量 m_e", "9.1093837015e-31 kg"),
    "proton_mass": ("质子质量 m_p", "1.67262192369e-27 kg"),
    "neutron_mass": ("中子质量 m_n", "1.67492749804e-27 kg"),
    "bohr_radius": ("Bohr 半径 a_0", "5.29177210903e-11 m"),
    "rydberg_constant": ("Rydberg 常数 R_∞", "10973731.568160 m⁻¹"),
    "fine_structure": ("精细结构常数 α", "1/137.035999084"),
    "stefan_boltzmann": ("Stefan-Boltzmann 常数 σ", "5.670374419e-8 W/(m²·K⁴)"),
    "vacuum_permittivity": ("真空介电常数 ε_0", "8.8541878128e-12 F/m"),
    "vacuum_permeability": ("真空磁导率 μ_0", "1.25663706212e-6 N/A²"),
    "wien_displacement": ("Wien 位移常数 b", "2.897771955e-3 m·K"),
    "hartree_energy": ("Hartree 能量 E_h", "4.3597447222071e-18 J"),
    "atomic_mass_unit": ("原子质量单位 u", "1.66053906660e-27 kg"),
    "faraday_constant": ("Faraday 常数 F", "96485.33212 C/mol"),
    "molar_volume": ("理想气体摩尔体积 V_m (STP)", "0.02241396954 m³/mol"),
    "solar_mass": ("太阳质量 M_☉", "1.98847e30 kg"),
    "earth_mass": ("地球质量 M_⊕", "5.9722e24 kg"),
    "solar_luminosity": ("太阳光度 L_☉", "3.828e26 W"),
    "astronomical_unit_value": ("天文单位 AU", "149597870700 m"),
    "parsec_value": ("秒差距 pc", "3.0856775814913673e16 m"),
    "light_year_value": ("光年 ly", "9460730472580800 m"),
    "hubble_constant": ("Hubble 常数 H_0", "≈ 70 km/s/Mpc"),
    "cosmic_microwave_bg": ("宇宙微波背景温度 T_CMB", "2.72548 K"),
}


@mcp.tool()
def math_convert(value: str = "", unit_from: str = "", unit_to: str = "",
                 constant: str = "") -> str:
    """
    单位换算或物理常数查询。

    value: 数值，如 '100'。
    unit_from: 源单位，如 'miles'。
    unit_to: 目标单位，如 'km'。
    constant: 查询物理/数学常数名称。留空则列出所有可用常数。

    示例:
        math_convert(value='100', unit_from='miles', unit_to='km')
        math_convert(value='32', unit_from='F', unit_to='C')
        math_convert(constant='speed_of_light')
        math_convert(constant='')  ← 列出所有常数

    支持的单位类别: 长度、质量、时间、温度、速度、力、能量、功率、压强、
                   面积、体积、角度、频率、数据量、浓度。
    """
    try:
        # 常数查询
        if constant is not None and constant.strip():
            name = constant.strip().lower().replace(" ", "_")
            if name in _PHYSICAL_CONSTANTS:
                desc, val = _PHYSICAL_CONSTANTS[name]
                return f"{val}"
            # 模糊搜索
            matches = [(k, v) for k, v in _PHYSICAL_CONSTANTS.items() if name in k]
            if len(matches) == 1:
                desc, val = matches[0][1]
                return f"{matches[0][0]}: {val}"
            if len(matches) > 1:
                lines = [f"找到 {len(matches)} 个匹配:"]
                for k, (desc, val) in matches[:10]:
                    lines.append(f"  {k}: {val}")
                return "\n".join(lines)
            # 列出所有
            lines = ["可用常数:"]
            for k, (desc, val) in sorted(_PHYSICAL_CONSTANTS.items()):
                lines.append(f"  {k} — {desc}: {val}")
            return "\n".join(lines)

        # 单位换算
        if value and unit_from and unit_to:
            val = float(_parse(value).evalf())
            uf = unit_from.strip().lower()
            ut = unit_to.strip().lower()

            # 温度特殊处理
            if uf in _TEMP_UNITS and ut in _TEMP_UNITS:
                si = _celsius_to_si(val, uf)
                result = _si_to_celsius(si, ut)
                return f"{val} {unit_from} = {result:.6g} {unit_to}"

            if uf not in _SI_FACTORS:
                return f"未知源单位: {unit_from}。可用 math_convert(constant='') 改为查看常数列表。"
            if ut not in _SI_FACTORS:
                return f"未知目标单位: {unit_to}。"

            si_val = val * _SI_FACTORS[uf]
            result = si_val / _SI_FACTORS[ut]
            # 选择合适的精度
            if abs(result) < 0.01 or abs(result) > 1e10:
                fmt = f"{result:.10g}"
            else:
                fmt = f"{result:.6g}"
            return f"{val} {unit_from} = {fmt} {unit_to}"

        # 列出单位
        lines = ["可用单位（按类别）:"]
        categories = {
            "长度": ["m", "km", "cm", "mm", "um", "nm", "angstrom", "mile", "yard", "foot", "inch", "nautical_mile", "light_year", "au", "parsec"],
            "质量": ["kg", "g", "mg", "ug", "ton", "ton_us", "lb", "oz"],
            "时间": ["s", "min", "h", "day", "week", "year"],
            "温度": ["C (celsius)", "F (fahrenheit)", "K (kelvin)"],
            "速度": ["m/s", "km/h", "mph", "knot"],
            "力": ["N", "kN", "lbf", "dyne"],
            "能量": ["J", "kJ", "cal", "kcal", "Wh", "kWh", "eV", "MeV", "GeV", "erg"],
            "功率": ["W", "kW", "MW", "GW", "hp"],
            "压强": ["Pa", "kPa", "MPa", "atm", "bar", "mbar", "mmHg", "torr", "psi"],
            "面积": ["m2", "km2", "ha", "acre", "sq_ft", "sq_in"],
            "体积": ["L", "mL", "gal_us", "gal_uk", "qt", "pt", "cup", "fl_oz"],
            "角度": ["rad", "deg", "grad", "arcmin", "arcsec"],
            "频率": ["Hz", "kHz", "MHz", "GHz", "rpm"],
            "数据量": ["bit", "B", "KB", "MB", "GB", "TB", "KiB", "MiB", "GiB", "TiB"],
        }
        for cat, units in categories.items():
            lines.append(f"  {cat}: {', '.join(units)}")
        lines.append("")
        lines.append("用法: math_convert(value='100', unit_from='miles', unit_to='km')")
        lines.append("温度: math_convert(value='32', unit_from='F', unit_to='C')")
        lines.append("常数: math_convert(constant='speed_of_light')")
        return "\n".join(lines)
    except Exception as e:
        return f"Error: {e}"

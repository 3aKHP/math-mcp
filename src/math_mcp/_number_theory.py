"""
math_mcp._number_theory
数论工具：math_number_theory
"""
from __future__ import annotations

from sympy import (
    bernoulli,
    divisors,
    factorint,
    fibonacci,
    gcd,
    isprime,
    lcm,
    nextprime,
    npartitions,
    prime,
    primepi,
    prevprime,
    primitive_root,
    sieve,
    totient,
)

from ._parse import _parse

from .server import mcp


@mcp.tool()
def math_number_theory(value: str, operation: str = "factor") -> str:
    """
    数论运算。

    value: 整数值或参数，取决于 operation:
           因式分解/factor：'1234567890'
           GCD/LCM：'1234,5678'
           素数范围：'2,100'
           离散对数：'base,value,modulus'
           中国剩余定理：'r1,m1;r2,m2;...'
    operation:
        factor        — 质因数分解
        isprime       — 素数判定
        nextprime     — 下一个素数
        prevprime     — 前一个素数
        totient       — 欧拉函数 φ(n)
        divisors      — 所有因子
        primitiveroot — 最小原根
        gcd           — 最大公约数
        lcm           — 最小公倍数
        fibonacci     — 第 n 个斐波那契数
        bernoulli     — 第 n 个伯努利数
        npartitions   — 整数分拆数
        primorial     — 素数阶乘（前 n 个素数之积）
        primepi       — ≤ n 的素数个数
        prime         — 第 n 个素数
        primerange    — 范围内素数列表（格式 'a,b'）
        crt           — 中国剩余定理（格式 'r1,m1;r2,m2;...'）
        legendre      — Legendre 符号 (a|p)，格式 'a,p'
        jacobi        — Jacobi 符号 (a|n)，格式 'a,n'
    """
    try:
        v = value.strip()

        def _ints(count: int = 2):
            parts = [p.strip() for p in v.split(",")]
            if len(parts) < count:
                raise ValueError(f"需要 {count} 个逗号分隔的整数")
            return [int(_parse(p)) for p in parts]

        if operation == "factor":
            n = int(_parse(v))
            fac = factorint(n)
            if not fac:
                return f"{n} = 1"
            parts = [f"{p}^{e}" if e > 1 else str(p) for p, e in sorted(fac.items())]
            return f"{n} = " + " × ".join(parts)

        elif operation == "isprime":
            n = int(_parse(v))
            return f"{n} 是素数" if isprime(n) else f"{n} 不是素数"

        elif operation == "nextprime":
            n = int(_parse(v))
            return str(nextprime(n))

        elif operation == "prevprime":
            n = int(_parse(v))
            try:
                return str(prevprime(n))
            except ValueError:
                return "(无更小的素数)"

        elif operation == "totient":
            n = int(_parse(v))
            return str(totient(n))

        elif operation == "divisors":
            n = int(_parse(v))
            divs = divisors(n)
            return f"共 {len(divs)} 个因子: {divs}"

        elif operation == "primitiveroot":
            n = int(_parse(v))
            try:
                return str(primitive_root(n))
            except ValueError as e:
                return str(e)

        elif operation == "gcd":
            a, b = _ints(2)
            return str(gcd(a, b))

        elif operation == "lcm":
            a, b = _ints(2)
            return str(lcm(a, b))

        elif operation == "fibonacci":
            n = int(_parse(v))
            return str(fibonacci(n))

        elif operation == "bernoulli":
            n = int(_parse(v))
            return str(bernoulli(n))

        elif operation == "npartitions":
            n = int(_parse(v))
            return str(npartitions(n))

        elif operation == "primorial":
            n = int(_parse(v))
            result = 1
            for p in sieve.primerange(2, prime(n) + 1):
                result *= p
            return str(result)

        elif operation == "primepi":
            n = int(_parse(v))
            return str(primepi(n))

        elif operation == "prime":
            n = int(_parse(v))
            return str(prime(n))

        elif operation == "primerange":
            a, b = _ints(2)
            primes = list(sieve.primerange(a, b + 1))
            if len(primes) <= 50:
                return f"共 {len(primes)} 个素数: {primes}"
            return f"共 {len(primes)} 个素数（前 50 个）: {primes[:50]}..."

        elif operation == "crt":
            remainders = []
            moduli = []
            for part in v.split(";"):
                part = part.strip()
                if not part:
                    continue
                r_s, m_s = part.split(",")
                remainders.append(int(_parse(r_s)))
                moduli.append(int(_parse(m_s)))
            from sympy.ntheory.modular import crt as _crt
            result = _crt(moduli, remainders)
            if result is None:
                return "(无解)"
            return f"x ≡ {result[0]} (mod {result[1]})"

        elif operation == "legendre":
            a_s, p_s = v.split(",")
            a = int(_parse(a_s))
            p = int(_parse(p_s))
            from sympy.ntheory.residue_ntheory import legendre_symbol
            return str(legendre_symbol(a, p))

        elif operation == "jacobi":
            a_s, n_s = v.split(",")
            a = int(_parse(a_s))
            n = int(_parse(n_s))
            from sympy.ntheory.residue_ntheory import jacobi_symbol
            return str(jacobi_symbol(a, n))

        else:
            ops = "factor, isprime, nextprime, prevprime, totient, divisors, primitiveroot, gcd, lcm, fibonacci, bernoulli, npartitions, primorial, primepi, prime, primerange, crt, legendre, jacobi"
            return f"不支持的操作: {operation}。支持: {ops}"
    except Exception as e:
        return f"Error: {e}"

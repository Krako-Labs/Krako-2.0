from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, getcontext

getcontext().prec = 28

_SCALE_6 = Decimal("0.000001")


def dec(x: str | int) -> Decimal:
    return Decimal(str(x))


def quant6(d: Decimal) -> Decimal:
    return d.quantize(_SCALE_6, rounding=ROUND_HALF_EVEN)


def serialize_decimal(d: Decimal) -> str:
    q = quant6(d)
    return format(q, ".6f")

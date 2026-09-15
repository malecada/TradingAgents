# SPDX-License-Identifier: GPL-2.0-or-later
"""Exact v3 tick-to-Q64.96 translation for research range configuration.

Derived from Uniswap v3-core TickMath.sol (Uniswap, GPL-2.0-or-later):
https://github.com/Uniswap/v3-core/blob/main/contracts/libraries/TickMath.sol
Retains the contract's Q128 integer multipliers, intermediate truncation,
positive-tick reciprocal and final upward rounding. No market/source access.
"""

MIN_TICK, MAX_TICK = -887272, 887272
MIN_SQRT = 4295128739
MAX_SQRT = 1461446703485210103287273052203988822378723970342
MULTIPLIERS = (
    0xfffcb933bd6fad37aa2d162d1a594001,
    0xfff97272373d413259a46990580e213a,
    0xfff2e50f5f656932ef12357cf3c7fdcc,
    0xffe5caca7e10e4e61c3624eaa0941cd0,
    0xffcb9843d60f6159c9db58835c926644,
    0xff973b41fa98c081472e6896dfb254c0,
    0xff2ea16466c96a3843ec78b326b52861,
    0xfe5dee046a99a2a811c461f1969c3053,
    0xfcbe86c7900a88aedcffc83b479aa3a4,
    0xf987a7253ac413176f2b074cf7815e54,
    0xf3392b0822b70005940c7a398e4b70f3,
    0xe7159475a2c29b7443b29c7fa6e889d9,
    0xd097f3bdfd2022b8845ad8f792aa5825,
    0xa9f746462d870fdf8a65dc1f90e061e5,
    0x70d869a156d2a1b890bb3df62baf32f7,
    0x31be135f97d08fd981231505542fcfa6,
    0x9aa508b5b7a84e1c677de54f3e99bc9,
    0x5d6af8dedb81196699c329225ee604,
    0x2216e584f5fa1ea926041bedfe98,
    0x48a170391f7dc42444e8fa2,
)


def sqrt_at_tick(tick):
    if type(tick) is not int or not MIN_TICK <= tick <= MAX_TICK:
        raise ValueError('v3 tick outside the exact domain')
    magnitude, ratio = abs(tick), 1 << 128
    for bit, multiplier in enumerate(MULTIPLIERS):
        if magnitude & (1 << bit):
            ratio = ratio * multiplier >> 128
    if tick > 0:
        ratio = ((1 << 256) - 1) // ratio
    return (ratio + (1 << 32) - 1) >> 32


def position_bounds(lower_tick, upper_tick, spacing):
    """Validate an explicitly supplied spacing and return exact sqrt bounds.

    The caller must prove the pool's actual spacing and version. This does not
    establish initialization, position capacity or price-path eligibility.
    """
    if type(spacing) is not int or not 0 < spacing < 1 << 23:
        raise ValueError('positive int24 tick spacing required')
    low, high = sqrt_at_tick(lower_tick), sqrt_at_tick(upper_tick)
    if lower_tick >= upper_tick or lower_tick % spacing or upper_tick % spacing:
        raise ValueError('ordered ticks must be exact multiples of pool spacing')
    return low, high

"""Color conversion helpers used across the simulation."""
from __future__ import annotations

import math
from typing import Tuple


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value between minimum and maximum."""
    return max(minimum, min(maximum, value))


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """Convert HSL values to RGB (0-255)."""
    h = (h % 360.0) / 360.0
    s = clamp(s / 100.0, 0.0, 1.0)
    l = clamp(l / 100.0, 0.0, 1.0)

    if s == 0:
        r = g = b = int(round(l * 255))
        return r, g, b

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q

    r = hue_to_rgb(p, q, h + 1 / 3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1 / 3)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def hex_to_rgb(value: str) -> Tuple[int, int, int]:
    """Convert a #RRGGBB or #RGB hex string to RGB tuple."""
    value = value.strip()
    if value.startswith("#"):
        value = value[1:]
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise ValueError("Invalid HEX color format")
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return r, g, b


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB tuple (0-255) to #RRGGBB string."""
    return f"#{r:02X}{g:02X}{b:02X}"


def hue_similarity(h1: float, h2: float) -> float:
    """Return similarity score between hues."""
    d = abs(h1 - h2) % 360.0
    d = min(d, 360.0 - d)
    return 1.0 - (d / 180.0)

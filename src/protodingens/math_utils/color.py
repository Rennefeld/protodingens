"""Color conversion helpers mirroring the JavaScript utilities."""
from __future__ import annotations

from math import cos, pi, sin
from typing import Tuple


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def hsl_to_rgb(hue: float, saturation: float, lightness: float) -> Tuple[int, int, int]:
    """Convert HSL (with hue in degrees, saturation/lightness in percent) to RGB."""
    h = (hue % 360) / 360.0
    s = clamp(saturation, 0.0, 100.0) / 100.0
    l = clamp(lightness, 0.0, 100.0) / 100.0

    if s == 0.0:
        value = int(round(l * 255))
        return value, value, value

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


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    color = hex_color.lstrip('#')
    if len(color) == 3:
        color = ''.join(ch * 2 for ch in color)
    if len(color) != 6:
        raise ValueError(f"Invalid hex color: {hex_color}")
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return r, g, b


def get_hue_similarity(h1: float, h2: float) -> float:
    delta = abs((h1 % 360) - (h2 % 360))
    delta = min(delta, 360 - delta)
    return 1.0 - delta / 180.0


__all__ = ["clamp", "hsl_to_rgb", "hex_to_rgb", "get_hue_similarity"]

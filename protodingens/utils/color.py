"""Colour conversion helpers."""
from __future__ import annotations

import colorsys
from typing import Tuple


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[int, int, int]:
    """Convert HSL (in degrees/percent) to RGB 0-255."""
    h_norm = (h % 360) / 360.0
    s_norm = max(0.0, min(1.0, s / 100.0))
    l_norm = max(0.0, min(1.0, l / 100.0))
    r, g, b = colorsys.hls_to_rgb(h_norm, l_norm, s_norm)
    return int(round(r * 255)), int(round(g * 255)), int(round(b * 255))


def hex_to_rgb(hex_code: str) -> Tuple[int, int, int]:
    """Convert hex colour to RGB tuple."""
    value = hex_code.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6:
        raise ValueError(f"Unsupported hex colour: {hex_code}")
    r = int(value[0:2], 16)
    g = int(value[2:4], 16)
    b = int(value[4:6], 16)
    return r, g, b


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp value into range."""
    return max(min_value, min(max_value, value))


def get_hue_similarity(h1: float, h2: float) -> float:
    """Return similarity of hues (0-1)."""
    diff = abs((h1 % 360) - (h2 % 360))
    diff = min(diff, 360 - diff)
    return 1.0 - (diff / 180.0)

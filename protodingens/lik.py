"""Particle implementation for Localised Information Nodes (LIK)."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from .colors import hsl_to_rgb
from .config import Config


@dataclass
class Lik:
    """Represents a single particle in the Protochaos field."""

    config: Config
    frame_created: int
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    initial_lifespan: float = field(init=False)
    initial_hue: float = field(init=False)
    hue: float = field(init=False)
    rgb: tuple[int, int, int] = field(init=False)

    def __post_init__(self) -> None:
        fg = self.config.field_geometry
        self.x += (random.random() - 0.5) * 50.0
        self.y += (random.random() - 0.5) * 50.0
        self.z += (random.random() - 0.5) * 50.0
        self.initial_lifespan = fg.max_lik_lifespan * (0.5 + random.random() * 0.5)
        self.initial_hue = random.random() * 360.0
        self.hue = self.initial_hue
        self.rgb = hsl_to_rgb(self.hue, self.config.palette.palette_saturation, self.config.palette.palette_lightness)

    def update_color(self, frame: int) -> None:
        age = (frame - self.frame_created) / max(self.initial_lifespan, 1.0)
        self.hue = (self.initial_hue + age * 36.0) % 360.0
        self.rgb = hsl_to_rgb(self.hue, self.config.palette.palette_saturation, self.config.palette.palette_lightness)

    def prepare_step(self, frame: int) -> None:
        if frame % 15 == 0:
            self.update_color(frame)

    def age(self, frame: int) -> float:
        return frame - self.frame_created

    def expired(self, frame: int) -> bool:
        return self.age(frame) > self.initial_lifespan

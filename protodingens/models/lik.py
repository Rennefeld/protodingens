"""LIK particle implementation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from ..config import Config
from ..utils.color import clamp, get_hue_similarity, hsl_to_rgb


@dataclass
class LIK:
    """Localized information node in the Protochaos field."""

    x: float
    y: float
    z: float
    config: Config
    frame_created: int
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    initial_lifespan: float = field(init=False)
    initial_hue: float = field(init=False)
    hue: float = field(init=False)
    rgb: tuple[int, int, int] = field(init=False)

    def __post_init__(self) -> None:
        import random

        jitter = 50.0
        self.x += (random.random() - 0.5) * jitter
        self.y += (random.random() - 0.5) * jitter
        self.z += (random.random() - 0.5) * jitter
        self.initial_lifespan = self.config.max_lik_lifespan * (0.5 + random.random() * 0.5)
        self.initial_hue = random.random() * 360.0
        self.hue = self.initial_hue
        self.rgb = hsl_to_rgb(self.hue, self.config.palette_saturation, self.config.palette_lightness)

    def update_color(self, frame_count: int) -> None:
        age = (frame_count - self.frame_created) / max(1.0, self.initial_lifespan)
        self.hue = (self.initial_hue + age * 36.0) % 360.0
        self.rgb = hsl_to_rgb(self.hue, self.config.palette_saturation, self.config.palette_lightness)

    def update(self, liks: List["LIK"], frame_count: int, global_drift: tuple[float, float, float]) -> None:
        import math
        import random

        if frame_count % 15 == 0:
            self.update_color(frame_count)

        fx = fy = fz = 0.0
        ps_radius = self.config.personal_space_radius
        ps_repulsion = self.config.personal_space_repulsion
        attraction_strength = self.config.attraction_strength
        similarity_threshold = self.config.attraction_similarity_threshold
        repulsion_strength = self.config.repulsion_strength

        for other in liks:
            if other is self:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            dz = other.z - self.z
            dist_sq = dx * dx + dy * dy + dz * dz
            if dist_sq < 1.0:
                continue
            dist = math.sqrt(dist_sq)
            if dist < ps_radius:
                r = ps_repulsion * (ps_radius - dist) / dist
                fx -= dx * r
                fy -= dy * r
                fz -= dz * r

            similarity = get_hue_similarity(self.hue, other.hue)
            if similarity > similarity_threshold:
                strength = attraction_strength * similarity / dist_sq
                fx += dx * strength
                fy += dy * strength
                fz += dz * strength
            else:
                strength = repulsion_strength * (1.0 - similarity) / dist_sq
                fx -= dx * strength
                fy -= dy * strength
                fz -= dz * strength

        mig = self.config.base_migration_speed
        fx += (random.random() - 0.5) * mig
        fy += (random.random() - 0.5) * mig
        fz += (random.random() - 0.5) * mig

        gx, gy, gz = global_drift
        fx += gx
        fy += gy
        fz += gz

        self.vx += fx
        self.vy += fy
        self.vz += fz

        damping = self.config.global_drift_momentum
        self.vx *= damping
        self.vy *= damping
        self.vz *= damping

        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        dist_to_center = math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
        radius = self.config.universe_radius
        if dist_to_center > radius:
            factor = radius / dist_to_center
            self.x *= factor
            self.y *= factor
            self.z *= factor

    def is_alive(self, frame_count: int) -> bool:
        return (frame_count - self.frame_created) < self.initial_lifespan

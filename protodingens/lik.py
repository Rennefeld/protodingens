"""Particle implementation for Localised Information Nodes (LIK)."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List

from .colors import clamp, hsl_to_rgb, hue_similarity
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

    def update(self, frame: int, liks: List["Lik"], global_drift: tuple[float, float, float]) -> None:
        if frame % 15 == 0:
            self.update_color(frame)

        fx = fy = fz = 0.0
        swarm = self.config.swarm

        for other in liks:
            if other is self:
                continue
            dx = other.x - self.x
            dy = other.y - self.y
            dz = other.z - self.z
            dist_sq = dx * dx + dy * dy + dz * dz
            if dist_sq < 1e-6:
                continue
            dist = math.sqrt(dist_sq)

            if dist < swarm.personal_space_radius:
                repulsion = swarm.personal_space_repulsion * (swarm.personal_space_radius - dist) / dist
                fx -= dx * repulsion
                fy -= dy * repulsion
                fz -= dz * repulsion

            similarity = hue_similarity(self.hue, other.hue)
            if similarity > swarm.attraction_similarity_threshold:
                strength = swarm.attraction_strength * similarity / dist_sq
                fx += dx * strength
                fy += dy * strength
                fz += dz * strength
            else:
                strength = swarm.repulsion_strength * (1.0 - similarity) / dist_sq
                fx -= dx * strength
                fy -= dy * strength
                fz -= dz * strength

        mig = swarm.base_migration_speed
        fx += (random.random() - 0.5) * mig
        fy += (random.random() - 0.5) * mig
        fz += (random.random() - 0.5) * mig

        fx += global_drift[0]
        fy += global_drift[1]
        fz += global_drift[2]

        self.vx += fx
        self.vy += fy
        self.vz += fz

        damping = self.config.interaction.global_drift_momentum
        self.vx *= damping
        self.vy *= damping
        self.vz *= damping

        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        radius = self.config.field_geometry.universe_radius
        dist_to_center = math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)
        if dist_to_center > radius:
            factor = radius / dist_to_center
            self.x *= factor
            self.y *= factor
            self.z *= factor

    def age(self, frame: int) -> float:
        return frame - self.frame_created

    def expired(self, frame: int) -> bool:
        return self.age(frame) > self.initial_lifespan

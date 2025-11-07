"""Particle model for ProtoDingens."""
from __future__ import annotations

from dataclasses import dataclass, field
from math import sqrt
from random import random
from typing import Iterable, Tuple

from ..config import Config
from ..math_utils.color import get_hue_similarity, hsl_to_rgb


@dataclass(slots=True)
class LIK:
    x: float
    y: float
    z: float
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    birth_frame: int = 0
    initial_lifespan: float = 0.0
    initial_hue: float = 0.0
    hue: float = 0.0
    rgb: Tuple[int, int, int] = field(default_factory=lambda: (0, 0, 0))

    def initialize(self, frame_count: int, config: Config, origin: Tuple[float, float, float]) -> None:
        ox, oy, oz = origin
        jitter = 50.0
        self.x = ox + (random() - 0.5) * jitter
        self.y = oy + (random() - 0.5) * jitter
        self.z = oz + (random() - 0.5) * jitter
        self.vx = 0.0
        self.vy = 0.0
        self.vz = 0.0
        self.birth_frame = frame_count
        self.initial_lifespan = config["maxLikLifespan"] * (0.5 + random() * 0.5)
        self.initial_hue = random() * 360.0
        self.hue = self.initial_hue
        self.update_color(frame_count, config)

    def age(self, frame_count: int) -> float:
        return (frame_count - self.birth_frame) / self.initial_lifespan if self.initial_lifespan else 0.0

    def update_color(self, frame_count: int, config: Config) -> None:
        age_factor = self.age(frame_count)
        self.hue = (self.initial_hue + age_factor * 36.0) % 360.0
        saturation = config["paletteSaturation"]
        lightness = config["paletteLightness"]
        self.rgb = hsl_to_rgb(self.hue, saturation, lightness)

    def update(self, frame_count: int, config: Config, liks: Iterable["LIK"], global_drift: Tuple[float, float, float]) -> None:
        if frame_count % 15 == 0:
            self.update_color(frame_count, config)

        fx = fy = fz = 0.0
        px = self.x
        py = self.y
        pz = self.z

        for other in liks:
            if other is self:
                continue
            dx = other.x - px
            dy = other.y - py
            dz = other.z - pz
            dist_sq = dx * dx + dy * dy + dz * dz
            if dist_sq < 1.0:
                continue
            dist = sqrt(dist_sq)

            if dist < config["personalSpaceRadius"]:
                repulsion = config["personalSpaceRepulsion"] * (config["personalSpaceRadius"] - dist) / dist
                fx -= dx * repulsion
                fy -= dy * repulsion
                fz -= dz * repulsion

            similarity = get_hue_similarity(self.hue, other.hue)
            if similarity > config["attractionSimilarityThreshold"]:
                strength = config["attractionStrength"] * similarity / dist_sq
                fx += dx * strength
                fy += dy * strength
                fz += dz * strength
            else:
                strength = config["repulsionStrength"] * (1.0 - similarity) / dist_sq
                fx -= dx * strength
                fy -= dy * strength
                fz -= dz * strength

        mig = config["baseMigrationSpeed"]
        fx += (random() - 0.5) * mig
        fy += (random() - 0.5) * mig
        fz += (random() - 0.5) * mig

        drift_x, drift_y, drift_z = global_drift
        fx += drift_x
        fy += drift_y
        fz += drift_z

        self.vx = (self.vx + fx) * 0.98
        self.vy = (self.vy + fy) * 0.98
        self.vz = (self.vz + fz) * 0.98

        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        radius = config["universeRadius"]
        dist_center_sq = self.x * self.x + self.y * self.y + self.z * self.z
        if dist_center_sq > radius * radius:
            dist_center = sqrt(dist_center_sq)
            factor = radius / dist_center
            self.x *= factor
            self.y *= factor
            self.z *= factor

    def is_dead(self, frame_count: int) -> bool:
        return frame_count - self.birth_frame > self.initial_lifespan


__all__ = ["LIK"]

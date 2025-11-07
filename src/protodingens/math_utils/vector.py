"""Minimal vector helpers for 3D calculations."""
from __future__ import annotations

from dataclasses import dataclass
from math import sqrt


@dataclass(slots=True)
class Vec3:
    x: float
    y: float
    z: float

    def copy(self) -> "Vec3":
        return Vec3(self.x, self.y, self.z)

    def add(self, other: "Vec3") -> "Vec3":
        self.x += other.x
        self.y += other.y
        self.z += other.z
        return self

    def scale(self, factor: float) -> "Vec3":
        self.x *= factor
        self.y *= factor
        self.z *= factor
        return self

    def magnitude(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalized(self) -> "Vec3":
        length = self.magnitude() or 1.0
        return Vec3(self.x / length, self.y / length, self.z / length)


__all__ = ["Vec3"]

"""Core simulation loop independent from UI."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .config import Config
from .models.lik import LIK
from .utils.color import clamp, get_hue_similarity, hsl_to_rgb, hex_to_rgb


@dataclass
class Camera:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    yaw: float = 0.0
    pitch: float = 0.0


@dataclass
class GlobalDrift:
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0


@dataclass
class Simulation:
    config: Config
    liks: List[LIK] = field(default_factory=list)
    frame_count: int = 0
    camera: Camera = field(default_factory=Camera)
    global_drift: GlobalDrift = field(default_factory=GlobalDrift)
    lik_pairs_cache: List[Tuple[LIK, LIK]] = field(default_factory=list)

    keys: dict[str, bool] = field(default_factory=dict)
    paused: bool = False

    def ensure_liks(self) -> None:
        import random

        self.liks = [lik for lik in self.liks if lik.is_alive(self.frame_count)]
        if len(self.liks) < self.config.min_lik_count:
            self.liks.append(LIK(self.camera.x, self.camera.y, self.camera.z, self.config, self.frame_count))
        elif len(self.liks) < self.config.max_lik_count and random.random() < 0.05:
            self.liks.append(LIK(self.camera.x, self.camera.y, self.camera.z, self.config, self.frame_count))

        if self.frame_count % 10 == 0:
            self.update_lik_pairs()

    def update_lik_pairs(self) -> None:
        pairs: List[Tuple[LIK, LIK]] = []
        visible = [lik for lik in self.liks if self.project(lik.x, lik.y, lik.z)[2] > -900]
        for i in range(len(visible)):
            for j in range(i + 1, len(visible)):
                pairs.append((visible[i], visible[j]))
        self.lik_pairs_cache = pairs

    def project(self, x: float, y: float, z: float) -> Tuple[float, float, float, float]:
        import math

        dx = x - self.camera.x
        dy = y - self.camera.y
        dz = z - self.camera.z

        cz = math.cos(self.camera.yaw)
        sz = math.sin(self.camera.yaw)
        x1 = cz * dx - sz * dz
        z1 = sz * dx + cz * dz

        cp = math.cos(self.camera.pitch)
        sp = math.sin(self.camera.pitch)
        y2 = cp * dy - sp * z1
        z2 = sp * dy + cp * z1

        fov = 1.0
        scale = fov / (z2 + 1000.0)
        return x1 * scale, y2 * scale, z2, scale

    def project_to_canvas(self, x: float, y: float, z: float, width: int, height: int) -> Tuple[float, float, float, float]:
        px, py, pz, scale = self.project(x, y, z)
        screen_x = width / 2 + px * width / 2
        screen_y = height / 2 + py * width / 2
        return screen_x, screen_y, pz, scale * width / 2

    def update_camera(self, dt: float) -> None:
        import math

        rotation_speed = 0.01
        move_speed = self.config.camera_movement_speed
        if self.keys.get("shift", False):
            move_speed *= 3.0

        if self.keys.get("arrowleft", False):
            self.camera.yaw += rotation_speed
        if self.keys.get("arrowright", False):
            self.camera.yaw -= rotation_speed
        if self.keys.get("arrowup", False):
            self.camera.pitch += rotation_speed
        if self.keys.get("arrowdown", False):
            self.camera.pitch -= rotation_speed

        self.camera.pitch = clamp(self.camera.pitch, -math.pi / 2, math.pi / 2)

        dx = dy = dz = 0.0
        yaw = self.camera.yaw
        if self.keys.get("w", False) or self.keys.get("s", False):
            speed = move_speed * (1 if self.keys.get("w", False) else -1)
            dx += math.sin(yaw) * speed
            dz += math.cos(yaw) * speed
        if self.keys.get("a", False) or self.keys.get("d", False):
            speed = move_speed * (-1 if self.keys.get("a", False) else 1)
            dx += math.sin(yaw + math.pi / 2) * speed
            dz += math.cos(yaw + math.pi / 2) * speed
        if self.keys.get(" ", False):
            dy -= move_speed
        if self.keys.get("control", False):
            dy += move_speed

        self.camera.x += dx * dt
        self.camera.y += dy * dt
        self.camera.z += dz * dt

    def update_global_drift(self) -> None:
        import random

        strength = self.config.global_drift_strength
        momentum = self.config.global_drift_momentum
        self.global_drift.vx *= momentum
        self.global_drift.vy *= momentum
        self.global_drift.vz *= momentum
        if random.random() < 0.01:
            self.global_drift.vx += (random.random() - 0.5) * strength
            self.global_drift.vy += (random.random() - 0.5) * strength
            self.global_drift.vz += (random.random() - 0.5) * strength

    def step(self, dt: float) -> None:
        if self.paused:
            return
        self.update_camera(dt)
        self.update_global_drift()
        self.ensure_liks()
        for lik in list(self.liks):
            lik.update(self.liks, self.frame_count, (self.global_drift.vx, self.global_drift.vy, self.global_drift.vz))
        self.frame_count += 1

    def background_rgba(self) -> Tuple[int, int, int, float]:
        r, g, b = hex_to_rgb(self.config.background_color)
        return r, g, b, self.config.trail_alpha

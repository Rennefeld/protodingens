"""Tkinter based renderer for the Protochaos simulation."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Iterable, List, Tuple

import tkinter as tk

from .colors import clamp, rgb_to_hex
from .config import Config
from .simulation import SimulationState


@dataclass
class ProjectedLik:
    x: float
    y: float
    depth: float
    radius: float
    rgb: Tuple[int, int, int]


class Renderer:
    """Handle drawing of LIKs and resonance lines on a Tk canvas."""

    def __init__(self, canvas: tk.Canvas, config: Config) -> None:
        self.canvas = canvas
        self.config = config
        self.width = 1280
        self.height = 720
        self.last_background = ""

    def update_dimensions(self) -> None:
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1:
            self.width = w
        if h > 1:
            self.height = h

    def clear(self) -> None:
        cfg = self.config
        bg = cfg.canvas.background_color
        if bg != self.last_background:
            self.canvas.configure(background=bg)
            self.last_background = bg
        self.canvas.delete("frame")

    def render(self, state: SimulationState) -> None:
        self.update_dimensions()
        self.clear()
        projected = [self.project_lik(lik) for lik in state.liks]
        if self.config.resonance.resonance_alpha > 0:
            self.draw_resonance_lines(projected)
        if self.config.rendering.render_liks:
            self.draw_liks(projected)

    def project_lik(self, lik) -> ProjectedLik:
        radius = self.config.field_geometry.universe_radius
        z = (lik.z + radius) / (2 * radius)
        depth = clamp(z, 0.02, 0.98)
        scale = 1.0 / (0.2 + depth)
        px = self.width / 2 + lik.x * scale
        py = self.height / 2 + lik.y * scale
        base_size = self.config.rendering.lik_base_size
        min_size = self.config.rendering.min_lik_render_size
        size = max(min_size, base_size * scale)
        return ProjectedLik(px, py, depth, size, lik.rgb)

    def draw_liks(self, liks: Iterable[ProjectedLik]) -> None:
        cfg = self.config
        amount = cfg.rgb_shift.rgb_shift_amount
        if amount <= 0 or not cfg.rgb_shift.rgb_shift_liks:
            for lik in liks:
                color = rgb_to_hex(*lik.rgb)
                radius = lik.radius
                self.canvas.create_oval(
                    lik.x - radius,
                    lik.y - radius,
                    lik.x + radius,
                    lik.y + radius,
                    fill=color,
                    outline="",
                    tags="frame",
                )
            return

        angle = math.radians(cfg.rgb_shift.rgb_shift_angle_deg)
        jitter = cfg.rgb_shift.rgb_shift_jitter
        offsets = self._compute_rgb_offsets(amount, angle, jitter)

        for lik in liks:
            radius = lik.radius
            for (dx, dy), color in offsets:
                self.canvas.create_oval(
                    lik.x - radius + dx,
                    lik.y - radius + dy,
                    lik.x + radius + dx,
                    lik.y + radius + dy,
                    fill=color,
                    outline="",
                    tags="frame",
                )

    def draw_resonance_lines(self, liks: List[ProjectedLik]) -> None:
        cfg = self.config.resonance
        shift_cfg = self.config.rgb_shift
        alpha = clamp(cfg.resonance_alpha, 0.0, 1.0)
        if alpha <= 0.0:
            return

        if len(liks) < 2:
            return

        max_distance = cfg.max_resonance_dist
        max_pairs = max(10, cfg.line_draw_sample_count * 3)
        candidates = random.sample(liks, min(len(liks), cfg.line_draw_sample_count * 4))
        pairs: List[Tuple[ProjectedLik, ProjectedLik]] = []
        for i, a in enumerate(candidates):
            for b in candidates[i + 1 :]:
                dx = a.x - b.x
                dy = a.y - b.y
                dist = math.hypot(dx, dy)
                if dist > max_distance:
                    continue
                pairs.append((a, b))
                if len(pairs) > max_pairs:
                    break
            if len(pairs) > max_pairs:
                break

        if not pairs:
            return

        amount = shift_cfg.rgb_shift_amount if shift_cfg.rgb_shift_lines else 0.0
        angle = math.radians(self.config.rgb_shift.rgb_shift_angle_deg)
        jitter = self.config.rgb_shift.rgb_shift_jitter
        offsets = self._compute_rgb_offsets(amount, angle, jitter) if amount > 0 else [((0.0, 0.0), "#00FFFF")]

        base_color = self._line_color(alpha)

        for (start, end) in pairs:
            wiggle = self.config.distortion.curve_wiggle_factor
            pull = self.config.distortion.line_target_pull
            mid_x = (start.x + end.x) / 2
            mid_y = (start.y + end.y) / 2
            noise_x = (random.random() - 0.5) * wiggle * 100.0
            noise_y = (random.random() - 0.5) * wiggle * 100.0
            ctrl_x = mid_x + noise_x + pull * (start.x - end.x)
            ctrl_y = mid_y + noise_y + pull * (start.y - end.y)

            for (dx, dy), color in offsets:
                line_color = color if amount > 0 else base_color
                self.canvas.create_line(
                    start.x + dx,
                    start.y + dy,
                    ctrl_x + dx,
                    ctrl_y + dy,
                    end.x + dx,
                    end.y + dy,
                    fill=line_color,
                    width=self.config.resonance.resonance_thickness,
                    smooth=True,
                    splinesteps=20,
                    tags="frame",
                )

    def _compute_rgb_offsets(
        self, amount: float, angle: float, jitter: float
    ) -> List[Tuple[Tuple[float, float], str]]:
        ax = math.cos(angle) * amount
        ay = math.sin(angle) * amount
        jitter_scale = amount * jitter
        offsets = []
        for color, mult in zip(((255, 0, 0), (0, 255, 0), (0, 0, 255)), (-1, 0, 1)):
            dx = ax * mult + (random.random() - 0.5) * jitter_scale
            dy = ay * mult + (random.random() - 0.5) * jitter_scale
            offsets.append(((dx, dy), rgb_to_hex(*color)))
        return offsets

    def _line_color(self, alpha: float) -> str:
        intensity = int(clamp(255 * alpha, 0, 255))
        return rgb_to_hex(0, intensity, intensity)

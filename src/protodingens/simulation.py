"""Core simulation loop for ProtoDingens."""
from __future__ import annotations

from dataclasses import dataclass, field
from random import random
from typing import List, Tuple

from .auto_loop import AutoLoopController
from .config import Config
from .math_utils.color import get_hue_similarity, hex_to_rgb
from .models.lik import LIK


@dataclass(slots=True)
class ResonancePair:
    a_index: int
    b_index: int
    distance: float
    similarity: float


@dataclass(slots=True)
class SimulationState:
    config: Config
    auto_loop: AutoLoopController
    liks: List[LIK] = field(default_factory=list)
    resonance_pairs: List[ResonancePair] = field(default_factory=list)
    frame_count: int = 0
    is_paused: bool = False
    global_drift: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def step(self, dt: float) -> None:
        if self.is_paused:
            return
        self.auto_loop.update(dt, self.frame_count)
        self._update_global_drift()
        self._manage_liks()
        drift = self.global_drift
        config = self.config
        for lik in list(self.liks):
            lik.update(self.frame_count, config, self.liks, drift)
        self._update_resonance_pairs()
        self.frame_count += 1

    def _manage_liks(self) -> None:
        config = self.config
        frame = self.frame_count
        self.liks = [lik for lik in self.liks if not lik.is_dead(frame)]
        origin = (0.0, 0.0, 0.0)
        while len(self.liks) < config["minLikCount"]:
            lik = LIK(0.0, 0.0, 0.0)
            lik.initialize(frame, config, origin)
            self.liks.append(lik)
        if len(self.liks) > config["maxLikCount"]:
            self.liks = self.liks[: config["maxLikCount"]]
        elif len(self.liks) < config["maxLikCount"] and random() < 0.05:
            lik = LIK(0.0, 0.0, 0.0)
            lik.initialize(frame, config, origin)
            self.liks.append(lik)

    def _update_resonance_pairs(self) -> None:
        max_dist = self.config["maxResonanceDist"]
        threshold = self.config["resonanceThreshold"]
        max_dist_sq = max_dist * max_dist
        liks = self.liks
        pairs: List[ResonancePair] = []
        for idx_a, lik_a in enumerate(liks):
            for idx_b in range(idx_a + 1, len(liks)):
                lik_b = liks[idx_b]
                dx = lik_b.x - lik_a.x
                dy = lik_b.y - lik_a.y
                dz = lik_b.z - lik_a.z
                dist_sq = dx * dx + dy * dy + dz * dz
                if dist_sq > max_dist_sq:
                    continue
                similarity = get_hue_similarity(lik_a.hue, lik_b.hue)
                if similarity < threshold:
                    continue
                pairs.append(ResonancePair(idx_a, idx_b, dist_sq ** 0.5, similarity))
        self.resonance_pairs = pairs

    def _update_global_drift(self) -> None:
        strength = self.config["globalDriftStrength"]
        momentum = self.config["globalDriftMomentum"]
        vx, vy, vz = self.global_drift
        vx = vx * momentum + (random() - 0.5) * strength
        vy = vy * momentum + (random() - 0.5) * strength
        vz = vz * momentum + (random() - 0.5) * strength
        self.global_drift = (vx, vy, vz)

    def toggle_pause(self) -> None:
        self.is_paused = not self.is_paused

    def randomize_all(self) -> None:
        config = self.config
        config.update(
            {
                "maxLikCount": int(200 + random() * 800),
                "minLikCount": int(50 + random() * 200),
                "maxLikLifespan": int(1000 + random() * 4000),
                "universeRadius": int(500 + random() * 1500),
                "attractionStrength": 0.0001 + random() * 0.0099,
                "attractionSimilarityThreshold": 0.5 + random() * 0.5,
                "repulsionStrength": 0.0001 + random() * 0.0199,
                "baseMigrationSpeed": 0.0001 + random() * 0.0099,
                "personalSpaceRadius": int(20 + random() * 200),
                "personalSpaceRepulsion": 0.1 + random() * 0.9,
                "paletteSaturation": int(20 + random() * 80),
                "paletteLightness": int(20 + random() * 60),
                "rgbShiftAmount": random() * 10.0,
                "rgbShiftAngleDeg": int(random() * 360),
                "rgbShiftJitter": random() * 0.5,
                "rgbShiftMode": "add" if random() < 0.5 else "subtract",
                "lineDrawSampleCount": int(5 + random() * 95),
                "resonanceThickness": 0.5 + random() * 4.5,
                "maxLineThicknessChaos": random() * 1.0,
                "resonanceAlpha": 0.05 + random() * 0.5,
                "maxResonanceDist": int(100 + random() * 700),
                "globalDriftStrength": random() * 0.2,
                "globalDriftMomentum": 0.9 + random() * 0.099,
                "animationSpeed": 0.5 + random() * 3.0,
            }
        )

    def background_rgba(self) -> Tuple[int, int, int, float]:
        r, g, b = hex_to_rgb(self.config["backgroundColor"])
        return r, g, b, self.config["trailAlpha"]


__all__ = ["SimulationState", "ResonancePair"]

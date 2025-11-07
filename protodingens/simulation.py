"""Simulation coordinator for the Protochaos field."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import Callable, List, Tuple

from .config import Config
from .lik import Lik
from .physics import SwarmIntegrator


@dataclass
class SimulationState:
    config: Config
    frame: int = 0
    liks: List[Lik] = field(default_factory=list)
    global_drift: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    def ensure_population(self) -> None:
        target = self.config.field_geometry.max_lik_count
        if len(self.liks) > target:
            self.liks = self.liks[:target]
        while len(self.liks) < target:
            self.liks.append(Lik(self.config, self.frame))

    def update_global_drift(self) -> None:
        strength = self.config.interaction.global_drift_strength
        momentum = self.config.interaction.global_drift_momentum
        gx, gy, gz = self.global_drift
        gx = gx * momentum + (random.random() - 0.5) * strength
        gy = gy * momentum + (random.random() - 0.5) * strength
        gz = gz * momentum + (random.random() - 0.5) * strength
        self.global_drift = (gx, gy, gz)

    def cull_dead_liks(self) -> None:
        frame = self.frame
        fg = self.config.field_geometry
        min_count = fg.min_lik_count
        self.liks = [lik for lik in self.liks if not lik.expired(frame)]
        while len(self.liks) < min_count:
            self.liks.append(Lik(self.config, frame))


class Simulation:
    """High-level interface combining update and rendering hooks."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.state = SimulationState(config)
        self.state.ensure_population()
        self._on_state_updated: List[Callable[[SimulationState], None]] = []
        self._integrator = SwarmIntegrator(config)

    def on_state_updated(self, callback: Callable[[SimulationState], None]) -> None:
        self._on_state_updated.append(callback)

    def step(self) -> SimulationState:
        cfg = self.config
        state = self.state
        state.update_global_drift()

        liks = state.liks
        for lik in liks:
            lik.prepare_step(state.frame)

        self._integrator.update(state.frame, liks, state.global_drift)

        state.cull_dead_liks()
        state.ensure_population()
        state.frame += 1

        for callback in self._on_state_updated:
            callback(state)
        return state

    def rebuild_population(self) -> None:
        self.state.liks.clear()
        self.state.ensure_population()

    def reset(self) -> None:
        self.state = SimulationState(self.config)
        self.state.ensure_population()

"""Auto-loop modulation for Protochaos parameters."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from .config import Config


@dataclass
class AutoLoopEntry:
    key: str
    getter: Callable[[], float]
    setter: Callable[[float], None]
    ui_min: float
    ui_max: float
    speed_mul: float = field(default_factory=lambda: 0.5 + random.random() * 1.5)
    t: float = 0.0
    direction: int = 1
    is_select: bool = False
    options: Optional[List[str]] = None
    last_change_frame: int = 0
    active: bool = False
    min: float = 0.0
    max: float = 0.0

    def reset_range(self, config: Config) -> None:
        span = self.ui_max - self.ui_min
        lim = config.auto_loop.auto_loop_limes
        self.min = self.ui_min + span * lim
        self.max = self.ui_max - span * lim
        if self.max <= self.min:
            self.min = self.ui_min
            self.max = self.ui_max
        self.t = random.random() * (self.max - self.min)
        self.direction = 1 if random.random() > 0.5 else -1


class AutoLoopController:
    """Animate parameter changes in the background."""

    LOOPABLE_KEYS: List[str] = [
        "maxLikCount",
        "minLikCount",
        "maxLikLifespan",
        "attractionStrength",
        "attractionSimilarityThreshold",
        "repulsionStrength",
        "baseMigrationSpeed",
        "cameraMovementSpeed",
        "universeRadius",
        "personalSpaceRadius",
        "personalSpaceRepulsion",
        "globalDriftStrength",
        "globalDriftMomentum",
        "lineDrawSampleCount",
        "resonanceThickness",
        "maxLineThicknessChaos",
        "resonanceAlpha",
        "maxResonanceDist",
        "curveWiggleFactor",
        "pulsationSpeed",
        "lineTargetPull",
        "likBaseSize",
        "minLikRenderSize",
        "trailAlpha",
        "rgbShiftAmount",
        "rgbShiftAngle",
        "rgbShiftJitter",
        "animationSpeed",
        "paletteSaturation",
        "paletteLightness",
        "compositeOperation",
    ]

    def __init__(self, config: Config) -> None:
        self.config = config
        self.entries: Dict[str, AutoLoopEntry] = {}
        self.enabled = False

    def register_slider(
        self,
        key: str,
        getter: Callable[[], float],
        setter: Callable[[float], None],
        minimum: float,
        maximum: float,
    ) -> None:
        entry = AutoLoopEntry(key, getter, setter, minimum, maximum)
        entry.reset_range(self.config)
        self.entries[key] = entry

    def register_select(
        self,
        key: str,
        getter: Callable[[], str],
        setter: Callable[[str], None],
        options: Iterable[str],
    ) -> None:
        entry = AutoLoopEntry(key, getter, setter, 0.0, 1.0)
        entry.is_select = True
        entry.options = list(options)
        self.entries[key] = entry

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def toggle_parameter(self, key: str, active: bool) -> None:
        if key not in self.entries:
            return
        entry = self.entries[key]
        entry.active = active

    def active_entries(self) -> Iterable[AutoLoopEntry]:
        for entry in self.entries.values():
            if getattr(entry, "active", False):
                yield entry

    def update(self, frame_delta: float, frame_number: int) -> None:
        if not self.enabled:
            return
        for entry in self.active_entries():
            if entry.is_select:
                assert entry.options is not None
                change_interval = max(10, int(120 / max(frame_delta * entry.speed_mul, 0.001)))
                if frame_number - entry.last_change_frame > change_interval:
                    entry.last_change_frame = frame_number
                    current = entry.getter()
                    next_option = random.choice(entry.options)
                    while next_option == current and len(entry.options) > 1:
                        next_option = random.choice(entry.options)
                    entry.setter(next_option)
            else:
                span = entry.max - entry.min
                speed = self.config.auto_loop.auto_loop_speed * entry.speed_mul
                entry.t += entry.direction * speed * frame_delta
                if entry.t > span:
                    entry.t = span
                    entry.direction = -1
                elif entry.t < 0:
                    entry.t = 0
                    entry.direction = 1
                value = entry.min + entry.t
                jitter = self.config.auto_loop.auto_loop_jitter
                if jitter > 0:
                    value += (random.random() - 0.5) * span * jitter * 0.02
                value = max(entry.ui_min, min(entry.ui_max, value))
                entry.setter(value)

    def randomize_targets(self) -> None:
        for entry in self.active_entries():
            if entry.is_select:
                continue
            entry.reset_range(self.config)

    def available_keys(self) -> List[str]:
        return list(self.entries.keys())

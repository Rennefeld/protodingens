"""Auto loop parameter modulation."""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, Iterable, Optional

from .config import Config
from .utils.color import clamp


@dataclass
class AutoLoopEntry:
    is_select: bool
    min_value: float = 0.0
    max_value: float = 1.0
    t: float = 0.0
    direction: int = 1
    speed_mul: float = 1.0
    options: Optional[list[str]] = None
    last_change_frame: int = 0


class AutoLoopController:
    """Replicates the JavaScript auto-loop engine."""

    def __init__(self, config: Config, loopable_keys: Iterable[str]):
        self.config = config
        self.loopable_keys = list(loopable_keys)
        self.entries: Dict[str, AutoLoopEntry] = {}

    def add_entry_for_range(self, key: str, ui_min: float, ui_max: float) -> None:
        span = ui_max - ui_min
        lim = self.config.auto_loop_limes
        min_value = ui_min + span * lim
        max_value = ui_max - span * lim
        entry_span = max_value - min_value
        entry = AutoLoopEntry(
            is_select=False,
            min_value=min_value,
            max_value=max_value,
            t=random.random() * entry_span,
            direction=1 if random.random() < 0.5 else -1,
            speed_mul=0.5 + random.random() * 1.5,
        )
        self.entries[key] = entry

    def add_entry_for_select(self, key: str, options: Iterable[str], frame_count: int) -> None:
        self.entries[key] = AutoLoopEntry(
            is_select=True,
            options=list(options),
            last_change_frame=frame_count,
            speed_mul=0.5 + random.random() * 1.5,
        )

    def remove_entry(self, key: str) -> None:
        self.entries.pop(key, None)

    def toggle_entry(self, key: str, *, enable: bool, **kwargs) -> None:
        if not enable:
            self.remove_entry(key)
            return
        if kwargs.get("is_select"):
            self.add_entry_for_select(key, kwargs["options"], kwargs.get("frame_count", 0))
        else:
            self.add_entry_for_range(key, kwargs["ui_min"], kwargs["ui_max"])

    def randomize_targets(self) -> None:
        for entry in self.entries.values():
            if entry.is_select:
                continue
            entry.t = random.random() * (entry.max_value - entry.min_value)
            entry.direction = 1 if random.random() < 0.5 else -1
            entry.speed_mul = 0.5 + random.random() * 1.5

    def step(self, dt: float, frame_count: int) -> None:
        if not self.config.auto_loop_enabled:
            return
        base_speed = self.config.auto_loop_speed
        jitter = self.config.auto_loop_jitter
        for key, entry in self.entries.items():
            if entry.is_select:
                interval = max(10, int(120 / (base_speed * entry.speed_mul)))
                if frame_count - entry.last_change_frame > interval and entry.options:
                    new_value = random.choice(entry.options)
                    setattr(self.config, key, new_value)
                    entry.last_change_frame = frame_count
            else:
                span = entry.max_value - entry.min_value
                entry.t += entry.direction * base_speed * entry.speed_mul * dt
                if entry.t > span:
                    entry.t = span
                    entry.direction = -1
                if entry.t < 0:
                    entry.t = 0
                    entry.direction = 1
                value = entry.min_value + entry.t
                value += (random.random() - 0.5) * span * jitter * 0.02
                value = clamp(value, entry.min_value, entry.max_value)
                setattr(self.config, key, value)

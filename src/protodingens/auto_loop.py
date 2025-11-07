"""Auto loop controller that mirrors the blueprint behaviour."""
from __future__ import annotations

from dataclasses import dataclass
from random import choice, random
from typing import Dict, List, MutableMapping, Optional

from .config import Config, PARAMETER_INDEX, ParameterDefinition


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
    "rgbShiftAngleDeg",
    "rgbShiftJitter",
    "animationSpeed",
    "paletteSaturation",
    "paletteLightness",
    "compositeOperation",
]


@dataclass(slots=True)
class AutoLoopEntry:
    key: str
    speed_multiplier: float
    is_select: bool
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    direction: float = 1.0
    position: float = 0.0
    options: Optional[List[str]] = None
    last_switch_frame: int = 0

    def clamp_position(self) -> None:
        if self.minimum is None or self.maximum is None:
            return
        if self.position < self.minimum:
            self.position = self.minimum
            self.direction *= -1.0
        elif self.position > self.maximum:
            self.position = self.maximum
            self.direction *= -1.0


class AutoLoopController:
    """Animate configuration values over time."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.entries: Dict[str, AutoLoopEntry] = {}
        self.enabled_keys: set[str] = set()

    def build_default_entries(self) -> None:
        for key in LOOPABLE_KEYS:
            self.enable_parameter(key, False)

    def enable_parameter(self, key: str, enabled: bool) -> None:
        if enabled:
            if key not in self.entries:
                definition = PARAMETER_INDEX[key]
                entry = self._create_entry(definition)
                self.entries[key] = entry
            entry = self.entries[key]
            self._apply_entry_value(entry)
            self.enabled_keys.add(key)
        else:
            self.enabled_keys.discard(key)

    def toggle(self, key: str) -> bool:
        enabled = key not in self.enabled_keys
        self.enable_parameter(key, enabled)
        return enabled

    def _create_entry(self, definition: ParameterDefinition) -> AutoLoopEntry:
        speed_multiplier = 0.5 + random() * 1.5
        if definition.control_type == "select":
            options = [value for value, _ in (definition.options or [])]
            return AutoLoopEntry(
                key=definition.key,
                speed_multiplier=speed_multiplier,
                is_select=True,
                options=options,
            )
        assert definition.minimum is not None and definition.maximum is not None
        span = definition.maximum - definition.minimum
        lim = self.config["autoLoopLimes"]
        minimum = definition.minimum + span * lim
        maximum = definition.maximum - span * lim
        start = minimum + random() * (maximum - minimum)
        direction = 1.0 if random() < 0.5 else -1.0
        return AutoLoopEntry(
            key=definition.key,
            speed_multiplier=speed_multiplier,
            is_select=False,
            minimum=minimum,
            maximum=maximum,
            direction=direction,
            position=start,
        )

    def _apply_entry_value(self, entry: AutoLoopEntry) -> None:
        if entry.is_select:
            options = entry.options or []
            if options:
                self.config[entry.key] = choice(options)
        else:
            self.config[entry.key] = entry.position

    def randomize_targets(self) -> None:
        for key in list(self.enabled_keys):
            definition = PARAMETER_INDEX[key]
            self.entries[key] = self._create_entry(definition)

    def update(self, dt: float, frame_count: int) -> None:
        if not self.config["autoLoopEnabled"]:
            return
        speed = self.config["autoLoopSpeed"]
        jitter = self.config["autoLoopJitter"]
        for key in list(self.enabled_keys):
            entry = self.entries.get(key)
            if not entry:
                continue
            definition = PARAMETER_INDEX[key]
            if entry.is_select:
                cooldown = int(120 / max(0.1, speed * entry.speed_multiplier))
                if frame_count - entry.last_switch_frame >= cooldown:
                    entry.last_switch_frame = frame_count
                    if entry.options:
                        self.config[key] = choice(entry.options)
                continue

            position = entry.position
            velocity = entry.direction * speed * entry.speed_multiplier * dt
            velocity += (random() - 0.5) * jitter
            position += velocity
            entry.position = position
            entry.clamp_position()
            self.config[key] = entry.position

    def state_snapshot(self) -> MutableMapping[str, bool]:
        return {key: key in self.enabled_keys for key in LOOPABLE_KEYS}


__all__ = ["AutoLoopController", "LOOPABLE_KEYS", "AutoLoopEntry"]

"""Configuration models for the Protochaos simulation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple, Any


@dataclass
class CanvasConfig:
    background_color: str = "#000000"
    composite_operation: str = "lighter"


@dataclass
class FieldGeometryConfig:
    max_lik_count: int = 300
    min_lik_count: int = 100
    max_lik_lifespan: int = 1800
    universe_radius: float = 1000.0


@dataclass
class SwarmBehaviorConfig:
    attraction_strength: float = 0.005
    attraction_similarity_threshold: float = 0.7
    repulsion_strength: float = 0.005
    base_migration_speed: float = 0.002
    personal_space_radius: float = 50.0
    personal_space_repulsion: float = 0.5


@dataclass
class InteractionConfig:
    global_drift_strength: float = 0.1
    global_drift_momentum: float = 0.99
    animation_speed: float = 1.0
    camera_movement_speed: float = 5.0


@dataclass
class ResonanceConfig:
    line_draw_sample_count: int = 10
    resonance_thickness: float = 1.5
    max_line_thickness_chaos: float = 0.5
    resonance_alpha: float = 0.15
    max_resonance_dist: float = 200.0
    resonance_threshold: float = 0.0


@dataclass
class DistortionConfig:
    curve_wiggle_factor: float = 0.5
    pulsation_speed: float = 0.1
    line_target_pull: float = 0.5


@dataclass
class PaletteConfig:
    palette_saturation: float = 50.0
    palette_lightness: float = 50.0


@dataclass
class LikRenderConfig:
    render_liks: bool = True
    lik_base_size: float = 5.0
    min_lik_render_size: float = 1.0
    trail_alpha: float = 0.9


@dataclass
class RgbShiftConfig:
    rgb_shift_liks: bool = True
    rgb_shift_lines: bool = True
    rgb_shift_amount: float = 6.0
    rgb_shift_angle_deg: float = 45.0
    rgb_shift_jitter: float = 0.15
    rgb_shift_mode: str = "add"


@dataclass
class AutoLoopConfig:
    auto_loop_enabled: bool = False
    auto_loop_speed: float = 2.0
    auto_loop_limes: float = 0.2
    auto_loop_jitter: float = 0.15


@dataclass
class Config:
    """Aggregate configuration for the Protochaos field."""

    canvas: CanvasConfig = field(default_factory=CanvasConfig)
    field_geometry: FieldGeometryConfig = field(default_factory=FieldGeometryConfig)
    swarm: SwarmBehaviorConfig = field(default_factory=SwarmBehaviorConfig)
    interaction: InteractionConfig = field(default_factory=InteractionConfig)
    resonance: ResonanceConfig = field(default_factory=ResonanceConfig)
    distortion: DistortionConfig = field(default_factory=DistortionConfig)
    palette: PaletteConfig = field(default_factory=PaletteConfig)
    rendering: LikRenderConfig = field(default_factory=LikRenderConfig)
    rgb_shift: RgbShiftConfig = field(default_factory=RgbShiftConfig)
    auto_loop: AutoLoopConfig = field(default_factory=AutoLoopConfig)


CONFIG_KEY_PATHS: Dict[str, Tuple[str, str]] = {
    "backgroundColor": ("canvas", "background_color"),
    "compositeOperation": ("canvas", "composite_operation"),
    "maxLikCount": ("field_geometry", "max_lik_count"),
    "minLikCount": ("field_geometry", "min_lik_count"),
    "maxLikLifespan": ("field_geometry", "max_lik_lifespan"),
    "universeRadius": ("field_geometry", "universe_radius"),
    "attractionStrength": ("swarm", "attraction_strength"),
    "attractionSimilarityThreshold": ("swarm", "attraction_similarity_threshold"),
    "repulsionStrength": ("swarm", "repulsion_strength"),
    "baseMigrationSpeed": ("swarm", "base_migration_speed"),
    "personalSpaceRadius": ("swarm", "personal_space_radius"),
    "personalSpaceRepulsion": ("swarm", "personal_space_repulsion"),
    "globalDriftStrength": ("interaction", "global_drift_strength"),
    "globalDriftMomentum": ("interaction", "global_drift_momentum"),
    "animationSpeed": ("interaction", "animation_speed"),
    "cameraMovementSpeed": ("interaction", "camera_movement_speed"),
    "lineDrawSampleCount": ("resonance", "line_draw_sample_count"),
    "resonanceThickness": ("resonance", "resonance_thickness"),
    "maxLineThicknessChaos": ("resonance", "max_line_thickness_chaos"),
    "resonanceAlpha": ("resonance", "resonance_alpha"),
    "maxResonanceDist": ("resonance", "max_resonance_dist"),
    "resonanceThreshold": ("resonance", "resonance_threshold"),
    "curveWiggleFactor": ("distortion", "curve_wiggle_factor"),
    "pulsationSpeed": ("distortion", "pulsation_speed"),
    "lineTargetPull": ("distortion", "line_target_pull"),
    "paletteSaturation": ("palette", "palette_saturation"),
    "paletteLightness": ("palette", "palette_lightness"),
    "renderLiks": ("rendering", "render_liks"),
    "likBaseSize": ("rendering", "lik_base_size"),
    "minLikRenderSize": ("rendering", "min_lik_render_size"),
    "trailAlpha": ("rendering", "trail_alpha"),
    "rgbShiftLiks": ("rgb_shift", "rgb_shift_liks"),
    "rgbShiftLines": ("rgb_shift", "rgb_shift_lines"),
    "rgbShiftAmount": ("rgb_shift", "rgb_shift_amount"),
    "rgbShiftAngle": ("rgb_shift", "rgb_shift_angle_deg"),
    "rgbShiftJitter": ("rgb_shift", "rgb_shift_jitter"),
    "rgbShiftMode": ("rgb_shift", "rgb_shift_mode"),
    "autoLoopEnabled": ("auto_loop", "auto_loop_enabled"),
    "autoLoopSpeed": ("auto_loop", "auto_loop_speed"),
    "autoLoopLimes": ("auto_loop", "auto_loop_limes"),
    "autoLoopJitter": ("auto_loop", "auto_loop_jitter"),
}


def get_config_value(config: Config, key: str) -> Any:
    path = CONFIG_KEY_PATHS[key]
    return getattr(getattr(config, path[0]), path[1])


def set_config_value(config: Config, key: str, value: Any) -> None:
    path = CONFIG_KEY_PATHS[key]
    setattr(getattr(config, path[0]), path[1], value)

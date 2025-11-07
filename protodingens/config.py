"""Simulation configuration data structures."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Config:
    """Mutable runtime configuration for the Protochaos field."""

    max_lik_count: int = 300
    min_lik_count: int = 100
    max_lik_lifespan: int = 1800
    universe_radius: float = 1000.0

    background_color: str = "#000000"
    composite_operation: str = "lighter"

    attraction_strength: float = 0.005
    attraction_similarity_threshold: float = 0.7
    repulsion_strength: float = 0.005
    base_migration_speed: float = 0.002
    personal_space_radius: float = 50.0
    personal_space_repulsion: float = 0.5

    global_drift_strength: float = 0.1
    global_drift_momentum: float = 0.99

    camera_movement_speed: float = 5.0
    animation_speed: float = 1.0

    line_draw_sample_count: int = 10
    resonance_thickness: float = 1.5
    max_line_thickness_chaos: float = 0.5
    resonance_alpha: float = 0.15
    max_resonance_dist: float = 200.0
    resonance_threshold: float = 0.0
    curve_wiggle_factor: float = 0.5
    pulsation_speed: float = 0.1
    line_target_pull: float = 0.5

    render_liks: bool = True
    lik_base_size: float = 5.0
    min_lik_render_size: float = 1.0
    trail_alpha: float = 0.9

    palette_saturation: float = 50.0
    palette_lightness: float = 50.0

    rgb_shift_liks: bool = True
    rgb_shift_lines: bool = True
    rgb_shift_amount: float = 6.0
    rgb_shift_angle_deg: float = 45.0
    rgb_shift_jitter: float = 0.15
    rgb_shift_mode: str = "add"

    auto_loop_enabled: bool = False
    auto_loop_speed: float = 2.0
    auto_loop_limes: float = 0.2
    auto_loop_jitter: float = 0.15


CONFIG_KEYS = {
    "maxLikCount": "max_lik_count",
    "minLikCount": "min_lik_count",
    "maxLikLifespan": "max_lik_lifespan",
    "universeRadius": "universe_radius",
    "backgroundColor": "background_color",
    "compositeOperation": "composite_operation",
    "attractionStrength": "attraction_strength",
    "attractionSimilarityThreshold": "attraction_similarity_threshold",
    "repulsionStrength": "repulsion_strength",
    "baseMigrationSpeed": "base_migration_speed",
    "personalSpaceRadius": "personal_space_radius",
    "personalSpaceRepulsion": "personal_space_repulsion",
    "globalDriftStrength": "global_drift_strength",
    "globalDriftMomentum": "global_drift_momentum",
    "cameraMovementSpeed": "camera_movement_speed",
    "animationSpeed": "animation_speed",
    "lineDrawSampleCount": "line_draw_sample_count",
    "resonanceThickness": "resonance_thickness",
    "maxLineThicknessChaos": "max_line_thickness_chaos",
    "resonanceAlpha": "resonance_alpha",
    "maxResonanceDist": "max_resonance_dist",
    "resonanceThreshold": "resonance_threshold",
    "curveWiggleFactor": "curve_wiggle_factor",
    "pulsationSpeed": "pulsation_speed",
    "lineTargetPull": "line_target_pull",
    "renderLiks": "render_liks",
    "likBaseSize": "lik_base_size",
    "minLikRenderSize": "min_lik_render_size",
    "trailAlpha": "trail_alpha",
    "paletteSaturation": "palette_saturation",
    "paletteLightness": "palette_lightness",
    "rgbShiftLiks": "rgb_shift_liks",
    "rgbShiftLines": "rgb_shift_lines",
    "rgbShiftAmount": "rgb_shift_amount",
    "rgbShiftAngleDeg": "rgb_shift_angle_deg",
    "rgbShiftJitter": "rgb_shift_jitter",
    "rgbShiftMode": "rgb_shift_mode",
    "autoLoopEnabled": "auto_loop_enabled",
    "autoLoopSpeed": "auto_loop_speed",
    "autoLoopLimes": "auto_loop_limes",
    "autoLoopJitter": "auto_loop_jitter",
}

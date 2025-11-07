"""Configuration models and schema for ProtoDingens Python port."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional


@dataclass(slots=True, frozen=True)
class ParameterDefinition:
    """Metadata that describes one configurable parameter in the control panel."""

    key: str
    label: str
    control_type: str
    section: str
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[tuple[str, str]]] = None
    precision: int = 2
    default: Any = None

    def normalized(self, value: Any) -> Any:
        """Clamp and convert a value to the parameter domain."""
        if self.control_type == "checkbox":
            return bool(value)
        if self.control_type == "select":
            text = str(value)
            if self.options and text not in {opt for opt, _ in self.options}:
                return self.options[0][0]
            return text
        if self.control_type == "color":
            return str(value)
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = float(self.default or 0.0)
        if self.minimum is not None:
            numeric = max(self.minimum, numeric)
        if self.maximum is not None:
            numeric = min(self.maximum, numeric)
        if self.step:
            # Round to the closest discrete value defined by the slider step.
            steps = round((numeric - (self.minimum or 0.0)) / self.step)
            numeric = (self.minimum or 0.0) + steps * self.step
        if isinstance(self.default, int) and self.step and float(self.step).is_integer():
            return int(round(numeric))
        return numeric


def _option(value: str, label: str) -> tuple[str, str]:
    return value, label


SECTION_DEFINITIONS: List[ParameterDefinition] = [
    ParameterDefinition(
        key="backgroundColor",
        label="Hintergrundfarbe",
        control_type="color",
        section="Canvas",
        default="#000000",
    ),
    ParameterDefinition(
        key="compositeOperation",
        label="Render Modus",
        control_type="select",
        section="Canvas",
        options=[
            _option("source-over", "Normal"),
            _option("lighter", "Lighter (Additiv)"),
            _option("difference", "Difference (Invert)"),
            _option("multiply", "Multiply (Dunkler)"),
            _option("screen", "Screen (Heller)"),
            _option("overlay", "Overlay"),
            _option("hard-light", "Hard Light"),
        ],
        default="lighter",
    ),
    # Feld-Geometrie
    ParameterDefinition(
        key="maxLikCount",
        label="Max. LIKs",
        control_type="slider",
        section="Feld-Geometrie",
        minimum=50,
        maximum=1000,
        step=50,
        precision=0,
        default=300,
    ),
    ParameterDefinition(
        key="minLikCount",
        label="Min. LIKs",
        control_type="slider",
        section="Feld-Geometrie",
        minimum=10,
        maximum=500,
        step=10,
        precision=0,
        default=100,
    ),
    ParameterDefinition(
        key="maxLikLifespan",
        label="Max. Lebensdauer (Frames)",
        control_type="slider",
        section="Feld-Geometrie",
        minimum=100,
        maximum=5000,
        step=100,
        precision=0,
        default=1800,
    ),
    ParameterDefinition(
        key="universeRadius",
        label="Universum-Radius",
        control_type="slider",
        section="Feld-Geometrie",
        minimum=100,
        maximum=2000,
        step=50,
        precision=0,
        default=1000,
    ),
    # Schwarm-Verhalten
    ParameterDefinition(
        key="attractionStrength",
        label="Anziehungs-Stärke",
        control_type="slider",
        section="Schwarm-Verhalten",
        minimum=0.0001,
        maximum=0.01,
        step=0.0001,
        precision=4,
        default=0.005,
    ),
    ParameterDefinition(
        key="attractionSimilarityThreshold",
        label="Farb-Ähnlichkeits-Schwelle",
        control_type="slider",
        section="Schwarm-Verhalten",
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.7,
    ),
    ParameterDefinition(
        key="repulsionStrength",
        label="Abstoßungs-Stärke",
        control_type="slider",
        section="Schwarm-Verhalten",
        minimum=0.0001,
        maximum=0.02,
        step=0.0001,
        precision=4,
        default=0.005,
    ),
    ParameterDefinition(
        key="baseMigrationSpeed",
        label="Basis-Wander-Geschw.",
        control_type="slider",
        section="Schwarm-Verhalten",
        minimum=0.0001,
        maximum=0.01,
        step=0.0001,
        precision=4,
        default=0.002,
    ),
    ParameterDefinition(
        key="personalSpaceRadius",
        label="Pers. Bereich Radius",
        control_type="slider",
        section="Schwarm-Verhalten",
        minimum=10,
        maximum=500,
        step=10,
        precision=0,
        default=50,
    ),
    ParameterDefinition(
        key="personalSpaceRepulsion",
        label="Pers. Bereich Abstoßung",
        control_type="slider",
        section="Schwarm-Verhalten",
        minimum=0.01,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.5,
    ),
    # Interaktion
    ParameterDefinition(
        key="globalDriftStrength",
        label="Globale Drift Stärke",
        control_type="slider",
        section="Interaktion",
        minimum=0.0,
        maximum=0.5,
        step=0.01,
        precision=2,
        default=0.1,
    ),
    ParameterDefinition(
        key="globalDriftMomentum",
        label="Globale Drift Impuls",
        control_type="slider",
        section="Interaktion",
        minimum=0.8,
        maximum=0.999,
        step=0.001,
        precision=3,
        default=0.99,
    ),
    ParameterDefinition(
        key="animationSpeed",
        label="Animations-Geschw.",
        control_type="slider",
        section="Interaktion",
        minimum=0.1,
        maximum=5.0,
        step=0.1,
        precision=1,
        default=1.0,
    ),
    ParameterDefinition(
        key="cameraMovementSpeed",
        label="Kamera-Geschw.",
        control_type="slider",
        section="Interaktion",
        minimum=1.0,
        maximum=20.0,
        step=1.0,
        precision=1,
        default=5.0,
    ),
    # Resonanzlinien
    ParameterDefinition(
        key="lineDrawSampleCount",
        label="Linien Zeichnung Sample",
        control_type="slider",
        section="Resonanzlinien",
        minimum=1,
        maximum=100,
        step=1,
        precision=0,
        default=10,
    ),
    ParameterDefinition(
        key="resonanceThickness",
        label="Resonanz Dicke",
        control_type="slider",
        section="Resonanzlinien",
        minimum=0.1,
        maximum=5.0,
        step=0.1,
        precision=1,
        default=1.5,
    ),
    ParameterDefinition(
        key="maxLineThicknessChaos",
        label="Max. Dicke Chaos",
        control_type="slider",
        section="Resonanzlinien",
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.5,
    ),
    ParameterDefinition(
        key="resonanceAlpha",
        label="Resonanz Alpha",
        control_type="slider",
        section="Resonanzlinien",
        minimum=0.01,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.15,
    ),
    ParameterDefinition(
        key="maxResonanceDist",
        label="Max. Resonanz Dist.",
        control_type="slider",
        section="Resonanzlinien",
        minimum=50,
        maximum=1000,
        step=10,
        precision=0,
        default=200,
    ),
    ParameterDefinition(
        key="resonanceThreshold",
        label="Resonanz Schwelle",
        control_type="hidden",
        section="Resonanzlinien",
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.0,
    ),
    # Linien-Verzerrung
    ParameterDefinition(
        key="curveWiggleFactor",
        label="Kurven-Wiggle-Faktor",
        control_type="slider",
        section="Linien-Verzerrung",
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.5,
    ),
    ParameterDefinition(
        key="pulsationSpeed",
        label="Pulsations-Geschw.",
        control_type="slider",
        section="Linien-Verzerrung",
        minimum=0.01,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.1,
    ),
    ParameterDefinition(
        key="lineTargetPull",
        label="Linien-Ziel-Zug",
        control_type="slider",
        section="Linien-Verzerrung",
        minimum=0.01,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.5,
    ),
    # Feld-Farbe
    ParameterDefinition(
        key="paletteSaturation",
        label="LIK Sättigung",
        control_type="slider",
        section="Feld-Farbe (LIKs)",
        minimum=0,
        maximum=100,
        step=1,
        precision=0,
        default=50,
    ),
    ParameterDefinition(
        key="paletteLightness",
        label="LIK Helligkeit",
        control_type="slider",
        section="Feld-Farbe (LIKs)",
        minimum=0,
        maximum=100,
        step=1,
        precision=0,
        default=50,
    ),
    # LIK Rendering
    ParameterDefinition(
        key="renderLiks",
        label="LIKs rendern",
        control_type="checkbox",
        section="LIK Rendering",
        default=True,
    ),
    ParameterDefinition(
        key="likBaseSize",
        label="Basisgröße LIK",
        control_type="slider",
        section="LIK Rendering",
        minimum=1.0,
        maximum=15.0,
        step=0.1,
        precision=1,
        default=5.0,
    ),
    ParameterDefinition(
        key="minLikRenderSize",
        label="Min. Rendergröße",
        control_type="slider",
        section="LIK Rendering",
        minimum=0.1,
        maximum=5.0,
        step=0.1,
        precision=1,
        default=1.0,
    ),
    ParameterDefinition(
        key="trailAlpha",
        label="Spur Alpha",
        control_type="slider",
        section="LIK Rendering",
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.9,
    ),
    # RGB Shift
    ParameterDefinition(
        key="rgbShiftLiks",
        label="RGB Shift auf LIKs",
        control_type="checkbox",
        section="RGB Farbverschiebung",
        default=True,
    ),
    ParameterDefinition(
        key="rgbShiftLines",
        label="RGB Shift auf Linien",
        control_type="checkbox",
        section="RGB Farbverschiebung",
        default=True,
    ),
    ParameterDefinition(
        key="rgbShiftAmount",
        label="Shift Stärke (px)",
        control_type="slider",
        section="RGB Farbverschiebung",
        minimum=0.0,
        maximum=15.0,
        step=0.1,
        precision=1,
        default=6.0,
    ),
    ParameterDefinition(
        key="rgbShiftAngleDeg",
        label="Shift Winkel (Grad)",
        control_type="slider",
        section="RGB Farbverschiebung",
        minimum=0,
        maximum=360,
        step=1,
        precision=0,
        default=45,
    ),
    ParameterDefinition(
        key="rgbShiftJitter",
        label="Shift Jitter",
        control_type="slider",
        section="RGB Farbverschiebung",
        minimum=0.0,
        maximum=1.0,
        step=0.01,
        precision=2,
        default=0.15,
    ),
    ParameterDefinition(
        key="rgbShiftMode",
        label="Shift Modus",
        control_type="select",
        section="RGB Farbverschiebung",
        options=[_option("add", "Additiv"), _option("subtract", "Subtraktiv")],
        default="add",
    ),
    # Auto Loop
    ParameterDefinition(
        key="autoLoopEnabled",
        label="Auto Loop Aktiviert",
        control_type="checkbox",
        section="Auto Loop (Protochaos)",
        default=False,
    ),
    ParameterDefinition(
        key="autoLoopSpeed",
        label="Loop Geschwindigkeit",
        control_type="slider",
        section="Auto Loop (Protochaos)",
        minimum=0.1,
        maximum=5.0,
        step=0.1,
        precision=1,
        default=2.0,
    ),
    ParameterDefinition(
        key="autoLoopLimes",
        label="Loop Bereich (Limes)",
        control_type="slider",
        section="Auto Loop (Protochaos)",
        minimum=0.0,
        maximum=0.5,
        step=0.01,
        precision=2,
        default=0.2,
    ),
    ParameterDefinition(
        key="autoLoopJitter",
        label="Loop Jitter",
        control_type="slider",
        section="Auto Loop (Protochaos)",
        minimum=0.0,
        maximum=0.5,
        step=0.01,
        precision=2,
        default=0.15,
    ),
]


SECTION_ORDER = [definition.section for definition in dict.fromkeys((d.section for d in SECTION_DEFINITIONS))]


@dataclass(slots=True)
class Config:
    """Mutable configuration matching the JavaScript blueprint."""

    values: MutableMapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for definition in SECTION_DEFINITIONS:
            self.values.setdefault(definition.key, definition.default)

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        definition = PARAMETER_INDEX[key]
        self.values[key] = definition.normalized(value)

    def items(self) -> Iterable[tuple[str, Any]]:
        return self.values.items()

    def update(self, mapping: Mapping[str, Any]) -> None:
        for key, value in mapping.items():
            self[key] = value

    def copy(self) -> "Config":
        return Config(dict(self.values))


PARAMETER_INDEX: Dict[str, ParameterDefinition] = {d.key: d for d in SECTION_DEFINITIONS}


def parameter_definitions_by_section() -> Dict[str, List[ParameterDefinition]]:
    by_section: Dict[str, List[ParameterDefinition]] = {section: [] for section in SECTION_ORDER}
    for definition in SECTION_DEFINITIONS:
        by_section[definition.section].append(definition)
    return by_section


__all__ = [
    "Config",
    "ParameterDefinition",
    "SECTION_DEFINITIONS",
    "SECTION_ORDER",
    "parameter_definitions_by_section",
    "PARAMETER_INDEX",
]

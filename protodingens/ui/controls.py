"""Qt control panel replicating the HTML blueprint layout."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Tuple

from PySide6 import QtCore, QtGui, QtWidgets

from ..auto_loop import AutoLoopController
from ..config import Config
from ..utils.color import hex_to_rgb


@dataclass
class SliderSpec:
    label: str
    attr: str
    minimum: float
    maximum: float
    step: float
    decimals: int


class ControlPanel(QtWidgets.QFrame):
    pause_toggled = QtCore.Signal()
    randomize_all = QtCore.Signal()
    auto_loop_randomize = QtCore.Signal()

    def __init__(self, config: Config, auto_loop: AutoLoopController, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("controls")
        self.config = config
        self.auto_loop = auto_loop
        self.slider_widgets: Dict[str, QtWidgets.QSlider] = {}
        self.value_labels: Dict[str, QtWidgets.QLabel] = {}
        self.checkbox_widgets: Dict[str, QtWidgets.QCheckBox] = {}
        self.select_widgets: Dict[str, QtWidgets.QComboBox] = {}

        self.setStyleSheet(self._stylesheet())

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        button_row = QtWidgets.QHBoxLayout()
        self.pause_button = self._make_button("Pausieren (P)")
        self.pause_button.clicked.connect(self.pause_toggled.emit)
        self.random_button = self._make_button("Zufall (Alle)")
        self.random_button.clicked.connect(self.randomize_all.emit)
        button_row.addWidget(self.pause_button)
        button_row.addWidget(self.random_button)
        layout.addLayout(button_row)

        self._add_canvas_section(layout)
        self._add_field_geometry(layout)
        self._add_swarm_section(layout)
        self._add_interaction_section(layout)
        self._add_resonance_section(layout)
        self._add_distortion_section(layout)
        self._add_palette_section(layout)
        self._add_lik_render_section(layout)
        self._add_rgb_shift_section(layout)
        self._add_auto_loop_section(layout)

        layout.addStretch(1)

    def _make_button(self, text: str) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(text)
        button.setProperty("class", "toggle-btn")
        return button

    def _add_section_title(self, layout: QtWidgets.QVBoxLayout, title: str) -> None:
        label = QtWidgets.QLabel(title)
        label.setProperty("class", "section-title")
        layout.addWidget(label)

    def _add_slider(self, layout: QtWidgets.QVBoxLayout, spec: SliderSpec) -> None:
        container = QtWidgets.QWidget()
        vbox = QtWidgets.QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(4)

        label = QtWidgets.QLabel()
        label.setProperty("class", "control-label")
        value_label = QtWidgets.QLabel()
        value_label.setProperty("class", "display-value")

        hbox = QtWidgets.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(QtWidgets.QLabel(spec.label))
        hbox.addStretch(1)
        hbox.addWidget(value_label)
        label.setLayout(hbox)
        vbox.addWidget(label)

        slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        slider.setRange(0, int(round((spec.maximum - spec.minimum) / spec.step)))
        slider.valueChanged.connect(lambda value, sp=spec, vl=value_label: self._on_slider(sp, value, vl))
        vbox.addWidget(slider)

        layout.addWidget(container)
        self.slider_widgets[spec.attr] = slider
        self.value_labels[spec.attr] = value_label
        self._update_slider(spec)

    def _update_slider(self, spec: SliderSpec) -> None:
        slider = self.slider_widgets[spec.attr]
        current_value = getattr(self.config, spec.attr)
        slider.blockSignals(True)
        slider.setValue(int(round((current_value - spec.minimum) / spec.step)))
        slider.blockSignals(False)
        self.value_labels[spec.attr].setText(f"{current_value:.{spec.decimals}f}")

    def _on_slider(self, spec: SliderSpec, slider_value: int, value_label: QtWidgets.QLabel) -> None:
        actual_value = spec.minimum + slider_value * spec.step
        setattr(self.config, spec.attr, actual_value)
        value_label.setText(f"{actual_value:.{spec.decimals}f}")

    def _add_checkbox(self, layout: QtWidgets.QVBoxLayout, label: str, attr: str) -> None:
        checkbox = QtWidgets.QCheckBox(label)
        checkbox.setChecked(bool(getattr(self.config, attr)))
        checkbox.stateChanged.connect(lambda state, key=attr: setattr(self.config, key, bool(state)))
        layout.addWidget(checkbox)
        self.checkbox_widgets[attr] = checkbox

    def _add_combo(self, layout: QtWidgets.QVBoxLayout, label_text: str, attr: str, options: Iterable[Tuple[str, str]]) -> None:
        layout.addWidget(QtWidgets.QLabel(label_text))
        combo = QtWidgets.QComboBox()
        for key, display in options:
            combo.addItem(display, key)
        combo.setCurrentText(next(display for key, display in options if key == getattr(self.config, attr)))
        combo.currentIndexChanged.connect(lambda _index, key=attr, widget=combo: setattr(self.config, key, widget.currentData()))
        layout.addWidget(combo)
        self.select_widgets[attr] = combo

    def _add_canvas_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Canvas")
        canvas_box = QtWidgets.QVBoxLayout()
        color_row = QtWidgets.QHBoxLayout()
        color_row.addWidget(QtWidgets.QLabel("Hintergrundfarbe"))
        self.color_button = QtWidgets.QPushButton()
        self.color_button.setFixedSize(40, 20)
        self.color_button.clicked.connect(self._choose_color)
        canvas_box.addLayout(color_row)
        canvas_box.addWidget(self.color_button)
        self._set_color_button(self.config.background_color)

        composite_options = [
            ("source-over", "Normal"),
            ("lighter", "Lighter (Additiv)"),
            ("difference", "Difference (Invert)"),
            ("multiply", "Multiply (Dunkler)"),
            ("screen", "Screen (Heller)"),
            ("overlay", "Overlay"),
            ("hard-light", "Hard Light"),
        ]
        self._add_combo(canvas_box, "Render Modus", "composite_operation", composite_options)
        layout.addLayout(canvas_box)

    def _choose_color(self) -> None:
        current = QtGui.QColor(self.config.background_color)
        color = QtWidgets.QColorDialog.getColor(current, self, "Hintergrundfarbe")
        if color.isValid():
            self.config.background_color = color.name()
            self._set_color_button(color.name())

    def _set_color_button(self, color_hex: str) -> None:
        r, g, b = hex_to_rgb(color_hex)
        self.color_button.setStyleSheet(f"background-color: rgb({r},{g},{b}); border: 1px solid #00FFFF;")

    def _add_field_geometry(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Feld-Geometrie")
        specs = [
            SliderSpec("Max. LIKs", "max_lik_count", 50, 1000, 50, 0),
            SliderSpec("Min. LIKs", "min_lik_count", 10, 500, 10, 0),
            SliderSpec("Max. Lebensdauer (Frames)", "max_lik_lifespan", 100, 5000, 100, 0),
            SliderSpec("Universum-Radius", "universe_radius", 100, 2000, 50, 0),
        ]
        for spec in specs:
            self._add_slider(layout, spec)

    def _add_swarm_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Schwarm-Verhalten")
        specs = [
            SliderSpec("Anziehungs-Stärke", "attraction_strength", 0.0001, 0.01, 0.0001, 4),
            SliderSpec("Farb-Ähnlichkeits-Schwelle", "attraction_similarity_threshold", 0.0, 1.0, 0.01, 2),
            SliderSpec("Abstoßungs-Stärke", "repulsion_strength", 0.0001, 0.02, 0.0001, 4),
            SliderSpec("Basis-Wander-Geschw.", "base_migration_speed", 0.0001, 0.01, 0.0001, 4),
            SliderSpec("Pers. Bereich Radius", "personal_space_radius", 10, 500, 10, 0),
            SliderSpec("Pers. Bereich Abstoßung", "personal_space_repulsion", 0.01, 1.0, 0.01, 2),
        ]
        for spec in specs:
            self._add_slider(layout, spec)

    def _add_interaction_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Interaktion")
        specs = [
            SliderSpec("Globale Drift Stärke", "global_drift_strength", 0.0, 0.5, 0.01, 2),
            SliderSpec("Globale Drift Impuls", "global_drift_momentum", 0.8, 0.999, 0.001, 3),
            SliderSpec("Animations-Geschw.", "animation_speed", 0.1, 5.0, 0.1, 1),
            SliderSpec("Kamera-Geschw.", "camera_movement_speed", 1.0, 20.0, 1.0, 1),
        ]
        for spec in specs:
            self._add_slider(layout, spec)

    def _add_resonance_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Resonanzlinien")
        specs = [
            SliderSpec("Linien Zeichnung Sample", "line_draw_sample_count", 1, 100, 1, 0),
            SliderSpec("Resonanz Dicke", "resonance_thickness", 0.1, 5.0, 0.1, 1),
            SliderSpec("Max. Dicke Chaos", "max_line_thickness_chaos", 0.0, 1.0, 0.01, 2),
            SliderSpec("Resonanz Alpha", "resonance_alpha", 0.01, 1.0, 0.01, 2),
            SliderSpec("Max. Resonanz Dist.", "max_resonance_dist", 50, 1000, 10, 0),
        ]
        for spec in specs:
            self._add_slider(layout, spec)

    def _add_distortion_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Linien-Verzerrung")
        specs = [
            SliderSpec("Kurven-Wiggle-Faktor", "curve_wiggle_factor", 0.0, 1.0, 0.01, 2),
            SliderSpec("Pulsations-Geschw.", "pulsation_speed", 0.01, 1.0, 0.01, 2),
            SliderSpec("Linien-Ziel-Zug", "line_target_pull", 0.01, 1.0, 0.01, 2),
        ]
        for spec in specs:
            self._add_slider(layout, spec)

    def _add_palette_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Feld-Farbe (LIKs)")
        specs = [
            SliderSpec("LIK Sättigung", "palette_saturation", 0, 100, 1, 0),
            SliderSpec("LIK Helligkeit", "palette_lightness", 0, 100, 1, 0),
        ]
        for spec in specs:
            self._add_slider(layout, spec)

    def _add_lik_render_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "LIK Rendering")
        self._add_checkbox(layout, "LIKs rendern", "render_liks")
        specs = [
            SliderSpec("Basisgröße LIK", "lik_base_size", 1.0, 15.0, 0.1, 1),
            SliderSpec("Min. Rendergröße", "min_lik_render_size", 0.1, 5.0, 0.1, 1),
            SliderSpec("Spur Alpha", "trail_alpha", 0.0, 1.0, 0.01, 2),
        ]
        for spec in specs:
            self._add_slider(layout, spec)

    def _add_rgb_shift_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "RGB Farbverschiebung")
        self._add_checkbox(layout, "RGB Shift auf LIKs", "rgb_shift_liks")
        self._add_checkbox(layout, "RGB Shift auf Linien", "rgb_shift_lines")
        specs = [
            SliderSpec("Shift Stärke (px)", "rgb_shift_amount", 0.0, 15.0, 0.1, 1),
            SliderSpec("Shift Winkel (Grad)", "rgb_shift_angle_deg", 0.0, 360.0, 1.0, 0),
            SliderSpec("Shift Jitter", "rgb_shift_jitter", 0.0, 1.0, 0.01, 2),
        ]
        for spec in specs:
            self._add_slider(layout, spec)
        self._add_combo(
            layout,
            "Shift Modus",
            "rgb_shift_mode",
            [("add", "Additiv"), ("subtract", "Subtraktiv")],
        )

    def _add_auto_loop_section(self, layout: QtWidgets.QVBoxLayout) -> None:
        self._add_section_title(layout, "Auto Loop (Protochaos)")
        self._add_checkbox(layout, "Auto Loop Aktiviert", "auto_loop_enabled")
        specs = [
            SliderSpec("Loop Geschwindigkeit", "auto_loop_speed", 0.1, 5.0, 0.1, 1),
            SliderSpec("Loop Bereich (Limes)", "auto_loop_limes", 0.0, 0.5, 0.01, 2),
            SliderSpec("Loop Jitter", "auto_loop_jitter", 0.0, 0.5, 0.01, 2),
        ]
        for spec in specs:
            self._add_slider(layout, spec)
        random_loop_button = self._make_button("Zufällige Loop Parameter")
        random_loop_button.clicked.connect(self.auto_loop_randomize.emit)
        layout.addWidget(random_loop_button)
        self._add_section_title(layout, "Loop-Parameter Auswahl")
        self.loop_param_container = QtWidgets.QVBoxLayout()
        layout.addLayout(self.loop_param_container)

    def set_loop_parameter_options(self, entries: Iterable[Tuple[str, str, bool]], callback: Callable[[str, bool], None]) -> None:
        # Clear existing widgets
        while self.loop_param_container.count():
            item = self.loop_param_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        for key, label, checked in entries:
            checkbox = QtWidgets.QCheckBox(label)
            checkbox.setChecked(checked)
            checkbox.stateChanged.connect(lambda state, k=key: callback(k, bool(state)))
            self.loop_param_container.addWidget(checkbox)

    @staticmethod
    def _stylesheet() -> str:
        return (
            "#controls {"
            "background: rgba(0, 0, 0, 0.95);"
            "border: 1px solid rgba(0,255,255,0.5);"
            "border-radius: 12px;"
            "box-shadow: 0 0 35px rgba(0,255,255,0.8), 0 0 10px rgba(0,255,255,0.9);"
            "color: #E0F7FA;"
            "}"
            "QLabel { color: #E0F7FA; font-size: 12px; }"
            ".section-title { color: #84FFFF; font-weight: 700; border-top: 1px dashed rgba(132,255,255,0.3); padding-top: 6px; }"
            ".control-label { font-weight: 500; }"
            ".display-value { color: #00FFFF; font-family: 'Fira Code', monospace; }"
            "QSlider::groove:horizontal { height: 4px; background: #00FFFF; border-radius: 2px; }"
            "QSlider::handle:horizontal { background: #84FFFF; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; box-shadow: 0 0 5px #00FFFF; }"
            "QComboBox { background: #000; color: #84FFFF; border: 1px solid #00FFFF; border-radius: 4px; padding: 4px; }"
            "QCheckBox { color: #E0F7FA; }"
            "QPushButton[class='toggle-btn'] { background: #00FFFF; color: #000; border-radius: 6px; font-weight: bold; padding: 6px 12px; box-shadow: 0 0 10px rgba(0,255,255,0.5); }"
            "QPushButton[class='toggle-btn']:hover { background: #84FFFF; }"
        )

    def refresh(self) -> None:
        for spec_attr, slider in self.slider_widgets.items():
            current_value = getattr(self.config, spec_attr)
            decimals = 2
            for spec in self._all_specs():
                if spec.attr == spec_attr:
                    decimals = spec.decimals
                    step = spec.step
                    slider_range_value = int(round((current_value - spec.minimum) / spec.step))
                    slider.blockSignals(True)
                    slider.setValue(slider_range_value)
                    slider.blockSignals(False)
                    self.value_labels[spec_attr].setText(f"{current_value:.{decimals}f}")
                    break
        for attr, checkbox in self.checkbox_widgets.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(bool(getattr(self.config, attr)))
            checkbox.blockSignals(False)
        for attr, combo in self.select_widgets.items():
            combo.blockSignals(True)
            current_value = getattr(self.config, attr)
            idx = combo.findData(current_value)
            combo.setCurrentIndex(idx)
            combo.blockSignals(False)
        self._set_color_button(self.config.background_color)

    def _all_specs(self) -> Iterable[SliderSpec]:
        sections = [
            self._field_specs(),
            self._swarm_specs(),
            self._interaction_specs(),
            self._resonance_specs(),
            self._distortion_specs(),
            self._palette_specs(),
            self._lik_specs(),
            self._rgb_specs(),
            self._auto_loop_specs(),
        ]
        for section in sections:
            for spec in section:
                yield spec

    def get_slider_spec(self, attr: str) -> SliderSpec | None:
        for spec in self._all_specs():
            if spec.attr == attr:
                return spec
        return None

    def _field_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Max. LIKs", "max_lik_count", 50, 1000, 50, 0),
            SliderSpec("Min. LIKs", "min_lik_count", 10, 500, 10, 0),
            SliderSpec("Max. Lebensdauer (Frames)", "max_lik_lifespan", 100, 5000, 100, 0),
            SliderSpec("Universum-Radius", "universe_radius", 100, 2000, 50, 0),
        )

    def _swarm_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Anziehungs-Stärke", "attraction_strength", 0.0001, 0.01, 0.0001, 4),
            SliderSpec("Farb-Ähnlichkeits-Schwelle", "attraction_similarity_threshold", 0.0, 1.0, 0.01, 2),
            SliderSpec("Abstoßungs-Stärke", "repulsion_strength", 0.0001, 0.02, 0.0001, 4),
            SliderSpec("Basis-Wander-Geschw.", "base_migration_speed", 0.0001, 0.01, 0.0001, 4),
            SliderSpec("Pers. Bereich Radius", "personal_space_radius", 10, 500, 10, 0),
            SliderSpec("Pers. Bereich Abstoßung", "personal_space_repulsion", 0.01, 1.0, 0.01, 2),
        )

    def _interaction_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Globale Drift Stärke", "global_drift_strength", 0.0, 0.5, 0.01, 2),
            SliderSpec("Globale Drift Impuls", "global_drift_momentum", 0.8, 0.999, 0.001, 3),
            SliderSpec("Animations-Geschw.", "animation_speed", 0.1, 5.0, 0.1, 1),
            SliderSpec("Kamera-Geschw.", "camera_movement_speed", 1.0, 20.0, 1.0, 1),
        )

    def _resonance_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Linien Zeichnung Sample", "line_draw_sample_count", 1, 100, 1, 0),
            SliderSpec("Resonanz Dicke", "resonance_thickness", 0.1, 5.0, 0.1, 1),
            SliderSpec("Max. Dicke Chaos", "max_line_thickness_chaos", 0.0, 1.0, 0.01, 2),
            SliderSpec("Resonanz Alpha", "resonance_alpha", 0.01, 1.0, 0.01, 2),
            SliderSpec("Max. Resonanz Dist.", "max_resonance_dist", 50, 1000, 10, 0),
        )

    def _distortion_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Kurven-Wiggle-Faktor", "curve_wiggle_factor", 0.0, 1.0, 0.01, 2),
            SliderSpec("Pulsations-Geschw.", "pulsation_speed", 0.01, 1.0, 0.01, 2),
            SliderSpec("Linien-Ziel-Zug", "line_target_pull", 0.01, 1.0, 0.01, 2),
        )

    def _palette_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("LIK Sättigung", "palette_saturation", 0, 100, 1, 0),
            SliderSpec("LIK Helligkeit", "palette_lightness", 0, 100, 1, 0),
        )

    def _lik_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Basisgröße LIK", "lik_base_size", 1.0, 15.0, 0.1, 1),
            SliderSpec("Min. Rendergröße", "min_lik_render_size", 0.1, 5.0, 0.1, 1),
            SliderSpec("Spur Alpha", "trail_alpha", 0.0, 1.0, 0.01, 2),
        )

    def _rgb_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Shift Stärke (px)", "rgb_shift_amount", 0.0, 15.0, 0.1, 1),
            SliderSpec("Shift Winkel (Grad)", "rgb_shift_angle_deg", 0.0, 360.0, 1.0, 0),
            SliderSpec("Shift Jitter", "rgb_shift_jitter", 0.0, 1.0, 0.01, 2),
        )

    def _auto_loop_specs(self) -> Tuple[SliderSpec, ...]:
        return (
            SliderSpec("Loop Geschwindigkeit", "auto_loop_speed", 0.1, 5.0, 0.1, 1),
            SliderSpec("Loop Bereich (Limes)", "auto_loop_limes", 0.0, 0.5, 0.01, 2),
            SliderSpec("Loop Jitter", "auto_loop_jitter", 0.0, 0.5, 0.01, 2),
        )

"""Qt control panel replicating the HTML blueprint."""
from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QColorDialog,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from ..auto_loop import AutoLoopController, LOOPABLE_KEYS
from ..config import Config, PARAMETER_INDEX, ParameterDefinition, parameter_definitions_by_section


@dataclass(slots=True)
class BoundWidget:
    definition: ParameterDefinition
    widget: QWidget
    display_label: Optional[QLabel] = None
    updating: bool = False

    def set_value(self, value: object) -> None:
        self.updating = True
        try:
            if isinstance(self.widget, QSlider):
                slider_value = self._to_slider_value(float(value))
                slider_value = max(self.widget.minimum(), min(self.widget.maximum(), slider_value))
                self.widget.setValue(slider_value)
            elif isinstance(self.widget, QCheckBox):
                self.widget.setChecked(bool(value))
            elif isinstance(self.widget, QComboBox):
                index = self.widget.findData(value)
                if index >= 0:
                    self.widget.setCurrentIndex(index)
            elif isinstance(self.widget, QPushButton) and self.definition.control_type == "color":
                color = QColor(str(value))
                self._update_color_button(color)
        finally:
            self.updating = False
        self._update_display(value)

    def _update_display(self, value: object) -> None:
        if self.display_label is None:
            return
        if self.definition.control_type == "select" and self.definition.options:
            for option_value, text in self.definition.options:
                if str(option_value) == str(value):
                    self.display_label.setText(text)
                    return
        if isinstance(value, float):
            fmt = f"{{:.{self.definition.precision}f}}"
            self.display_label.setText(fmt.format(value))
        else:
            self.display_label.setText(str(value))

    def _to_slider_value(self, actual: float) -> int:
        definition = self.definition
        assert definition.step
        assert definition.minimum is not None
        return int(round((actual - definition.minimum) / definition.step))

    def _update_color_button(self, color: QColor) -> None:
        palette = self.widget.palette()
        palette.setColor(QPalette.Button, color)
        self.widget.setPalette(palette)
        self.widget.setAutoFillBackground(True)
        self.widget.setText(color.name())


class ControlPanel(QWidget):
    config_changed = Signal(str, object)
    toggle_pause = Signal()
    randomize_all = Signal()
    toggle_controls_panel = Signal()
    randomize_auto_loop = Signal()
    auto_loop_toggled = Signal(str, bool)

    def __init__(self, config: Config, auto_loop: AutoLoopController, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.config = config
        self.auto_loop = auto_loop
        self.bound_widgets: Dict[str, BoundWidget] = {}
        self.loop_checkboxes: Dict[str, QCheckBox] = {}
        self.toggle_button: Optional[QPushButton] = None
        self.setFixedWidth(320)
        self._build_ui()
        self.sync_from_config()

    def _build_ui(self) -> None:
        self.setObjectName("controlsPanel")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self.setStyleSheet(
            """
            #controlsPanel {
                background-color: rgba(8, 12, 20, 0.92);
                border-right: 2px solid #00ffff;
                color: #e0faff;
            }
            #sectionFrame {
                background-color: rgba(20, 30, 45, 0.65);
                border: 1px solid rgba(0, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px;
            }
            #sectionTitle {
                font-size: 14px;
                font-weight: bold;
                color: #53d7ff;
                letter-spacing: 0.5px;
            }
            #controlLabel {
                font-size: 12px;
                color: #c8efff;
            }
            #displayValue {
                min-width: 60px;
                text-align: right;
                color: #a0f0ff;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: rgba(0, 255, 255, 0.2);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #00ffff;
                border: 1px solid #0ff;
                width: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QPushButton {
                background-color: rgba(0, 180, 220, 0.4);
                border: 1px solid rgba(0, 255, 255, 0.7);
                padding: 6px 12px;
                border-radius: 6px;
                color: #e0faff;
            }
            QPushButton:hover {
                background-color: rgba(0, 200, 255, 0.6);
            }
            QCheckBox {
                spacing: 8px;
            }
            QComboBox {
                background-color: rgba(10, 30, 40, 0.9);
                border: 1px solid rgba(0, 255, 255, 0.4);
                color: #e0faff;
            }
            """
        )

        button_row = QHBoxLayout()
        pause_btn = QPushButton("Pausieren (P)")
        pause_btn.clicked.connect(self.toggle_pause.emit)
        button_row.addWidget(pause_btn)
        random_btn = QPushButton("Zufall (Alle)")
        random_btn.clicked.connect(self.randomize_all.emit)
        button_row.addWidget(random_btn)
        layout.addLayout(button_row)

        sections = parameter_definitions_by_section()
        for section_name, definitions in sections.items():
            section_frame = QFrame()
            section_frame.setObjectName("sectionFrame")
            section_layout = QVBoxLayout(section_frame)
            title = QLabel(section_name)
            title.setObjectName("sectionTitle")
            section_layout.addWidget(title)

            for definition in definitions:
                if definition.control_type == "hidden":
                    continue
                section_layout.addLayout(self._create_control(definition))

            if section_name == "Auto Loop (Protochaos)":
                random_button = QPushButton("Zufällige Loop Parameter")
                random_button.clicked.connect(self.randomize_auto_loop.emit)
                section_layout.addWidget(random_button)

            layout.addWidget(section_frame)

        loop_frame = QFrame()
        loop_layout = QVBoxLayout(loop_frame)
        loop_title = QLabel("Loop-Parameter Auswahl")
        loop_title.setObjectName("sectionTitle")
        loop_layout.addWidget(loop_title)
        for key in LOOPABLE_KEYS:
            definition = PARAMETER_INDEX.get(key)
            label_text = definition.label if definition else key
            cb = QCheckBox(label_text)
            cb.stateChanged.connect(partial(self._on_loop_toggle, key))
            loop_layout.addWidget(cb)
            self.loop_checkboxes[key] = cb
        layout.addWidget(loop_frame)

        toggle_btn = QPushButton("Steuerung Ausblenden")
        toggle_btn.clicked.connect(self.toggle_controls_panel.emit)
        layout.addWidget(toggle_btn)
        self.toggle_button = toggle_btn
        layout.addSpacerItem(QSpacerItem(10, 20))

    def _create_control(self, definition: ParameterDefinition) -> QVBoxLayout:
        layout = QVBoxLayout()
        layout.setSpacing(4)
        display_label = QLabel()
        display_label.setObjectName("displayValue")

        if definition.control_type == "slider":
            label = QLabel(definition.label)
            label.setObjectName("controlLabel")
            layout.addWidget(label)
            slider = QSlider(Qt.Horizontal)
            assert definition.step
            assert definition.minimum is not None and definition.maximum is not None
            slider.setMinimum(0)
            total_steps = int(round((definition.maximum - definition.minimum) / definition.step))
            slider.setMaximum(total_steps)
            slider.setSingleStep(1)
            slider.valueChanged.connect(partial(self._on_slider_changed, definition))
            display_container = QHBoxLayout()
            display_container.addWidget(slider)
            display_container.addWidget(display_label)
            layout.addLayout(display_container)
            bound = BoundWidget(definition, slider, display_label)
        elif definition.control_type == "checkbox":
            checkbox = QCheckBox(definition.label)
            checkbox.stateChanged.connect(partial(self._on_checkbox_changed, definition))
            layout.addWidget(checkbox)
            bound = BoundWidget(definition, checkbox)
        elif definition.control_type == "select":
            label = QLabel(definition.label)
            label.setObjectName("controlLabel")
            layout.addWidget(label)
            combo = QComboBox()
            for value, text in definition.options or []:
                combo.addItem(text, value)
            combo.currentIndexChanged.connect(partial(self._on_select_changed, definition, combo))
            display_container = QHBoxLayout()
            display_container.addWidget(combo)
            display_container.addWidget(display_label)
            layout.addLayout(display_container)
            bound = BoundWidget(definition, combo, display_label)
        elif definition.control_type == "color":
            label = QLabel(definition.label)
            label.setObjectName("controlLabel")
            layout.addWidget(label)
            button = QPushButton("Farbe wählen")
            button.clicked.connect(partial(self._on_color_clicked, definition, button))
            layout.addWidget(button)
            bound = BoundWidget(definition, button)
        else:
            bound = BoundWidget(definition, QLabel(""))

        self.bound_widgets[definition.key] = bound
        return layout

    def sync_from_config(self) -> None:
        for key, bound in self.bound_widgets.items():
            value = self.config[key]
            bound.set_value(value)

        state = self.auto_loop.state_snapshot()
        for key, checkbox in self.loop_checkboxes.items():
            checkbox.blockSignals(True)
            checkbox.setChecked(state.get(key, False))
            checkbox.blockSignals(False)

    def _on_slider_changed(self, definition: ParameterDefinition, value: int) -> None:
        bound = self.bound_widgets[definition.key]
        if bound.updating:
            return
        actual = definition.minimum + value * definition.step  # type: ignore
        self.config_changed.emit(definition.key, actual)
        bound._update_display(actual)

    def _on_checkbox_changed(self, definition: ParameterDefinition, state: int) -> None:
        bound = self.bound_widgets[definition.key]
        if bound.updating:
            return
        value = state == Qt.Checked
        self.config_changed.emit(definition.key, value)

    def _on_select_changed(self, definition: ParameterDefinition, combo: QComboBox, index: int) -> None:
        bound = self.bound_widgets[definition.key]
        if bound.updating:
            return
        self.config_changed.emit(definition.key, combo.itemData(index))
        bound._update_display(combo.itemData(index))

    def _on_color_clicked(self, definition: ParameterDefinition, button: QPushButton) -> None:
        color = QColorDialog.getColor(QColor(self.config[definition.key]), self)
        if color.isValid():
            self.config_changed.emit(definition.key, color.name())
            bound = self.bound_widgets[definition.key]
            bound.set_value(color.name())

    def _on_loop_toggle(self, key: str, state: int) -> None:
        enabled = state == Qt.Checked
        self.auto_loop_toggled.emit(key, enabled)

    def set_collapsed(self, collapsed: bool) -> None:
        if self.toggle_button:
            self.toggle_button.setText("Steuerung Einblenden" if collapsed else "Steuerung Ausblenden")


__all__ = ["ControlPanel"]

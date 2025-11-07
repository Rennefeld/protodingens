"""Qt application entry point."""
from __future__ import annotations

import math
import random
from typing import Iterable, List

from PySide6 import QtCore, QtGui, QtWidgets

from .auto_loop import AutoLoopController
from .config import Config
from .models.lik import LIK
from .rendering.canvas import ChaosCanvas
from .simulation import Simulation
from .ui.controls import ControlPanel


LOOPABLE_ATTRIBUTES: List[str] = [
    "max_lik_count",
    "min_lik_count",
    "max_lik_lifespan",
    "attraction_strength",
    "attraction_similarity_threshold",
    "repulsion_strength",
    "base_migration_speed",
    "camera_movement_speed",
    "universe_radius",
    "personal_space_radius",
    "personal_space_repulsion",
    "global_drift_strength",
    "global_drift_momentum",
    "line_draw_sample_count",
    "resonance_thickness",
    "max_line_thickness_chaos",
    "resonance_alpha",
    "max_resonance_dist",
    "curve_wiggle_factor",
    "pulsation_speed",
    "line_target_pull",
    "lik_base_size",
    "min_lik_render_size",
    "trail_alpha",
    "rgb_shift_amount",
    "rgb_shift_angle_deg",
    "rgb_shift_jitter",
    "animation_speed",
    "palette_saturation",
    "palette_lightness",
    "composite_operation",
]

SELECT_ATTRIBUTES = {"composite_operation"}


def bootstrap_liks(simulation: Simulation) -> None:
    simulation.liks = [LIK(simulation.camera.x, simulation.camera.y, simulation.camera.z, simulation.config, simulation.frame_count) for _ in range(simulation.config.max_lik_count)]
    simulation.update_lik_pairs()


def humanize_attr(attr: str) -> str:
    words = attr.replace("_", " ").title()
    words = words.replace("Lik", "LIK").replace("Rgb", "RGB").replace("Deg", "Grad")
    words = words.replace("Id", "ID")
    return words


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Protochaos Feld V18")
        self.config = Config()
        self.simulation = Simulation(self.config)
        self.auto_loop = AutoLoopController(self.config, LOOPABLE_ATTRIBUTES)

        bootstrap_liks(self.simulation)

        central = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(central)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.control_panel = ControlPanel(self.config, self.auto_loop)
        self.control_panel.setFixedWidth(320)
        self.control_panel.pause_toggled.connect(self.toggle_pause)
        self.control_panel.randomize_all.connect(self.randomize_all)
        self.control_panel.auto_loop_randomize.connect(self.auto_loop.randomize_targets)

        layout.addWidget(self.control_panel)

        self.canvas = ChaosCanvas(self.simulation, self.auto_loop)
        layout.addWidget(self.canvas, 1)
        self.setCentralWidget(central)

        self.toggle_button = QtWidgets.QPushButton("Steuerung Ausblenden", self)
        self.toggle_button.setProperty("class", "toggle-btn")
        self.toggle_button.clicked.connect(self.toggle_controls)
        self.toggle_button.resize(180, 32)

        self._setup_toggle_style()
        self._bootstrap_auto_loop_defaults()
        self._reposition_toggle_button()

        self.ui_sync_timer = QtCore.QTimer(self)
        self.ui_sync_timer.timeout.connect(self.control_panel.refresh)
        self.ui_sync_timer.start(200)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._reposition_toggle_button()

    def _reposition_toggle_button(self) -> None:
        x_offset = 20 if not self.control_panel.isVisible() else self.control_panel.width() + 20
        self.toggle_button.move(x_offset, 10)

    def _setup_toggle_style(self) -> None:
        self.toggle_button.setStyleSheet(
            "QPushButton { background: #00FFFF; color: #000; border-radius: 6px; font-weight: bold; box-shadow: 0 0 10px rgba(0,255,255,0.5); }"
            "QPushButton:hover { background: #84FFFF; }"
        )

    def toggle_controls(self) -> None:
        visible = self.control_panel.isVisible()
        self.control_panel.setVisible(not visible)
        self.toggle_button.setText("Steuerung Einblenden" if visible else "Steuerung Ausblenden")
        self._reposition_toggle_button()

    def toggle_pause(self) -> None:
        self.simulation.paused = not self.simulation.paused
        self.control_panel.pause_button.setText("Fortsetzen" if self.simulation.paused else "Pausieren (P)")
        self.control_panel.pause_button.setProperty("class", "toggle-btn paused" if self.simulation.paused else "toggle-btn")

    def randomize_all(self) -> None:
        cfg = self.config
        cfg.max_lik_count = random.randint(200, 1000)
        cfg.min_lik_count = random.randint(50, 250)
        cfg.max_lik_lifespan = random.randint(1000, 5000)
        cfg.universe_radius = random.randint(500, 2000)

        cfg.attraction_strength = 0.0001 + random.random() * 0.0099
        cfg.attraction_similarity_threshold = 0.5 + random.random() * 0.5
        cfg.repulsion_strength = 0.0001 + random.random() * 0.0199
        cfg.base_migration_speed = 0.0001 + random.random() * 0.0099
        cfg.personal_space_radius = random.randint(20, 220)
        cfg.personal_space_repulsion = 0.1 + random.random() * 0.9

        cfg.palette_saturation = random.randint(20, 99)
        cfg.palette_lightness = random.randint(20, 80)

        cfg.rgb_shift_amount = random.random() * 10.0
        cfg.rgb_shift_angle_deg = random.randint(0, 359)
        cfg.rgb_shift_jitter = random.random() * 0.5
        cfg.rgb_shift_mode = random.choice(["add", "subtract"])

        cfg.line_draw_sample_count = random.randint(5, 100)
        cfg.resonance_thickness = 0.5 + random.random() * 4.5
        cfg.max_line_thickness_chaos = random.random()
        cfg.resonance_alpha = 0.05 + random.random() * 0.5
        cfg.max_resonance_dist = random.randint(100, 800)

        cfg.global_drift_strength = random.random() * 0.2
        cfg.global_drift_momentum = 0.9 + random.random() * 0.099
        cfg.animation_speed = 0.5 + random.random() * 3.0

        bootstrap_liks(self.simulation)
        self.control_panel.refresh()

    def _bootstrap_auto_loop_defaults(self) -> None:
        for attr in ["palette_saturation", "palette_lightness", "rgb_shift_amount", "attraction_strength"]:
            spec = self.control_panel.get_slider_spec(attr)
            if spec:
                self.auto_loop.add_entry_for_range(attr, spec.minimum, spec.maximum)
        self._refresh_loop_checkbox_ui()

    def _refresh_loop_checkbox_ui(self) -> None:
        entries = []
        for attr in LOOPABLE_ATTRIBUTES:
            label = humanize_attr(attr)
            entries.append((attr, label, attr in self.auto_loop.entries))
        self.control_panel.set_loop_parameter_options(entries, self._on_loop_param_toggle)

    def _on_loop_param_toggle(self, attr: str, enabled: bool) -> None:
        if attr in SELECT_ATTRIBUTES:
            combo = self.control_panel.select_widgets.get(attr)
            if combo is None:
                return
            options = [combo.itemData(i) for i in range(combo.count())]
            if enabled:
                self.auto_loop.add_entry_for_select(attr, options, self.simulation.frame_count)
            else:
                self.auto_loop.remove_entry(attr)
        else:
            spec = self.control_panel.get_slider_spec(attr)
            if not spec:
                return
            if enabled:
                self.auto_loop.add_entry_for_range(attr, spec.minimum, spec.maximum)
            else:
                self.auto_loop.remove_entry(attr)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_I:
            self.toggle_controls()
        super().keyPressEvent(event)


def main() -> None:
    app = QtWidgets.QApplication([])
    app.setApplicationName("Protochaos Feld")
    window = MainWindow()
    window.resize(1600, 900)
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover
    main()

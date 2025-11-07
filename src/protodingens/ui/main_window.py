"""Main window wiring together renderer and control panel."""
from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QHBoxLayout, QMainWindow, QShortcut, QWidget

from ..auto_loop import AutoLoopController
from ..config import Config
from ..rendering.canvas import ChaosCanvas
from ..simulation import SimulationState
from .controls_panel import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ProtoDingens - Python")
        self.config = Config()
        self.auto_loop = AutoLoopController(self.config)
        self.auto_loop.build_default_entries()
        self.simulation = SimulationState(self.config, self.auto_loop)

        self.canvas = ChaosCanvas(self.simulation)
        self.control_panel = ControlPanel(self.config, self.auto_loop)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.canvas, stretch=1)
        layout.addWidget(self.control_panel)
        self.setCentralWidget(central)

        self._setup_signals()
        self._setup_shortcuts()

        self.ui_sync_timer = QTimer(self)
        self.ui_sync_timer.setInterval(100)
        self.ui_sync_timer.timeout.connect(self.control_panel.sync_from_config)
        self.ui_sync_timer.start()

    def _setup_signals(self) -> None:
        self.control_panel.config_changed.connect(self._on_config_changed)
        self.control_panel.toggle_pause.connect(self._on_toggle_pause)
        self.control_panel.randomize_all.connect(self._on_randomize_all)
        self.control_panel.toggle_controls_panel.connect(self._on_toggle_controls)
        self.control_panel.randomize_auto_loop.connect(self._on_randomize_auto_loop)
        self.control_panel.auto_loop_toggled.connect(self._on_auto_loop_toggled)

    def _setup_shortcuts(self) -> None:
        pause_shortcut = QShortcut(QKeySequence("P"), self)
        pause_shortcut.activated.connect(self._on_toggle_pause)
        toggle_shortcut = QShortcut(QKeySequence("I"), self)
        toggle_shortcut.activated.connect(self._on_toggle_controls)

    def _on_config_changed(self, key: str, value: object) -> None:
        self.config[key] = value
        if key in {"autoLoopLimes"}:
            self.auto_loop.randomize_targets()

    def _on_auto_loop_toggled(self, key: str, enabled: bool) -> None:
        self.auto_loop.enable_parameter(key, enabled)

    def _on_randomize_auto_loop(self) -> None:
        self.auto_loop.randomize_targets()

    def _on_toggle_pause(self) -> None:
        self.simulation.toggle_pause()

    def _on_randomize_all(self) -> None:
        self.simulation.randomize_all()
        self.control_panel.sync_from_config()

    def _on_toggle_controls(self) -> None:
        current = self.control_panel.isVisible()
        self.control_panel.setVisible(not current)
        self.control_panel.set_collapsed(current)


__all__ = ["MainWindow"]

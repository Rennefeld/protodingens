"""Painter-based renderer approximating the blueprint visuals."""
from __future__ import annotations

import math
import random
from typing import Optional, Tuple

from PySide6.QtCore import QBasicTimer, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget

from ..math_utils.color import clamp
from ..simulation import ResonancePair, SimulationState

COMPOSITION_MAP = {
    "source-over": QPainter.CompositionMode_SourceOver,
    "lighter": QPainter.CompositionMode_Plus,
    "difference": QPainter.CompositionMode_Difference,
    "multiply": QPainter.CompositionMode_Multiply,
    "screen": QPainter.CompositionMode_Screen,
    "overlay": QPainter.CompositionMode_Overlay,
    "hard-light": QPainter.CompositionMode_HardLight,
}


class ChaosCanvas(QWidget):
    """Widget that renders the simulation onto an off-screen buffer."""

    def __init__(self, simulation: SimulationState, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.simulation = simulation
        self.setAttribute(Qt.WA_OpaquePaintEvent)
        self.setAutoFillBackground(False)
        self.buffer = QImage(self.size(), QImage.Format_RGBA8888)
        self.buffer.fill(Qt.black)
        self.timer = QBasicTimer()
        self.timer.start(16, self)

    def timerEvent(self, event) -> None:  # type: ignore[override]
        if event.timerId() != self.timer.timerId():
            return
        dt = 1.0 / 60.0
        self.simulation.step(dt * self.simulation.config["animationSpeed"])
        self._draw_to_buffer()
        self.update()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self.buffer = QImage(self.size(), QImage.Format_RGBA8888)
        self.buffer.fill(Qt.black)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.drawImage(self.rect(), self.buffer)
        painter.end()

    def _draw_to_buffer(self) -> None:
        painter = QPainter(self.buffer)
        painter.setRenderHint(QPainter.Antialiasing, True)
        self._apply_trail(painter)
        self._draw_resonance_lines(painter)
        self._draw_liks(painter)
        painter.end()

    def _apply_trail(self, painter: QPainter) -> None:
        r, g, b, alpha = self.simulation.background_rgba()
        color = QColor(r, g, b, int(clamp(alpha, 0.0, 1.0) * 255))
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        painter.fillRect(self.buffer.rect(), color)

    def _draw_resonance_lines(self, painter: QPainter) -> None:
        config = self.simulation.config
        composition = COMPOSITION_MAP.get(config["compositeOperation"], QPainter.CompositionMode_SourceOver)
        painter.setCompositionMode(composition)
        pulsation = math.sin(self.simulation.frame_count * config["pulsationSpeed"]) * config["maxLineThicknessChaos"]
        for pair in self.simulation.resonance_pairs:
            a = self.simulation.liks[pair.a_index]
            b = self.simulation.liks[pair.b_index]
            proj_a = self._project(a.x, a.y, a.z)
            proj_b = self._project(b.x, b.y, b.z)
            if proj_a is None or proj_b is None:
                continue
            thickness = (config["resonanceThickness"] + pulsation) * pair.similarity
            self._draw_curve(painter, proj_a, proj_b, pair, thickness)

    def _draw_curve(
        self,
        painter: QPainter,
        proj_a: Tuple[float, float, float],
        proj_b: Tuple[float, float, float],
        pair: ResonancePair,
        thickness: float,
    ) -> None:
        config = self.simulation.config
        ax, ay, scale_a = proj_a
        bx, by, scale_b = proj_b
        mid_x = (ax + bx) / 2.0
        mid_y = (ay + by) / 2.0
        wiggle = config["curveWiggleFactor"]
        offset = ((pair.distance or 1.0) * wiggle)
        control1 = QPointF(mid_x + offset, mid_y - offset)
        control2 = QPointF(mid_x - offset, mid_y + offset)
        path = QPainterPath(QPointF(ax, ay))
        path.cubicTo(control1, control2, QPointF(bx, by))
        alpha = clamp(config["resonanceAlpha"] * pair.similarity, 0.0, 1.0)
        base_color = QColor(255, 255, 255, int(alpha * 255))
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.NoBrush)
        shift_amount = config["rgbShiftAmount"]
        if config["rgbShiftLines"] and shift_amount > 0:
            angle = math.radians(config["rgbShiftAngleDeg"])
            jitter = (random.random() - 0.5) * config["rgbShiftJitter"]
            dx = math.cos(angle) * (shift_amount + jitter)
            dy = math.sin(angle) * (shift_amount + jitter)
            self._stroke_path(painter, path.translated(dx, dy), QColor(255, 0, 0, int(alpha * 255)), thickness)
            self._stroke_path(painter, path.translated(-dx, -dy), QColor(0, 0, 255, int(alpha * 255)), thickness)
            self._stroke_path(painter, path, QColor(0, 255, 0, int(alpha * 255)), thickness)
        else:
            self._stroke_path(painter, path, base_color, thickness)

    def _draw_liks(self, painter: QPainter) -> None:
        config = self.simulation.config
        if not config["renderLiks"]:
            return
        composition = COMPOSITION_MAP.get(config["compositeOperation"], QPainter.CompositionMode_SourceOver)
        painter.setCompositionMode(composition)
        for lik in self.simulation.liks:
            proj = self._project(lik.x, lik.y, lik.z)
            if proj is None:
                continue
            x, y, scale = proj
            size = config["likBaseSize"] * scale * 100.0
            size = clamp(size, config["minLikRenderSize"], 100.0)
            rect = QRectF(x - size / 2, y - size / 2, size, size)
            color = QColor(*lik.rgb, 255)
            if config["rgbShiftLiks"] and config["rgbShiftAmount"] > 0:
                angle = math.radians(config["rgbShiftAngleDeg"])
                jitter = (random.random() - 0.5) * config["rgbShiftJitter"]
                dx = math.cos(angle) * (config["rgbShiftAmount"] + jitter)
                dy = math.sin(angle) * (config["rgbShiftAmount"] + jitter)
                painter.fillRect(rect.translated(dx, dy), QColor(255, 0, 0, 200))
                painter.fillRect(rect.translated(-dx, -dy), QColor(0, 0, 255, 200))
            painter.fillRect(rect, color)

    def _stroke_path(self, painter: QPainter, path: QPainterPath, color: QColor, thickness: float) -> None:
        painter.save()
        pen = QPen(color)
        pen.setWidthF(max(1.0, thickness))
        painter.setPen(pen)
        painter.drawPath(path)
        painter.restore()

    def _project(self, x: float, y: float, z: float) -> Optional[Tuple[float, float, float]]:
        width = self.width()
        height = self.height()
        camera_z = -400.0
        fov = 600.0
        depth = z - camera_z
        if depth <= 1.0:
            depth = 1.0
        scale = fov / depth
        screen_x = width / 2 + x * scale
        screen_y = height / 2 + y * scale
        if not (math.isfinite(screen_x) and math.isfinite(screen_y)):
            return None
        return screen_x, screen_y, scale


__all__ = ["ChaosCanvas"]

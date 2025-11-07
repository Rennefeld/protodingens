"""Rendering widget for the Protochaos field."""
from __future__ import annotations

import math
import time
from typing import Tuple

from PySide6 import QtCore, QtGui, QtWidgets

from ..auto_loop import AutoLoopController
from ..config import Config
from ..simulation import Simulation
from ..utils.color import clamp, get_hue_similarity, hsl_to_rgb


COMPOSITION_MAP = {
    "source-over": QtGui.QPainter.CompositionMode_SourceOver,
    "lighter": QtGui.QPainter.CompositionMode_Plus,
    "difference": QtGui.QPainter.CompositionMode_Difference,
    "multiply": QtGui.QPainter.CompositionMode_Multiply,
    "screen": QtGui.QPainter.CompositionMode_Screen,
    "overlay": QtGui.QPainter.CompositionMode_Overlay,
    "hard-light": QtGui.QPainter.CompositionMode_HardLight,
}


class ChaosCanvas(QtWidgets.QWidget):
    """Widget responsible for real-time rendering."""

    def __init__(self, simulation: Simulation, auto_loop: AutoLoopController, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.simulation = simulation
        self.auto_loop = auto_loop
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.last_time = time.perf_counter()
        self.buffer = QtGui.QImage(self.size(), QtGui.QImage.Format.Format_ARGB32_Premultiplied)
        self.buffer.fill(QtGui.QColor("black"))
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._on_tick)
        self.timer.start(16)

    def sizeHint(self) -> QtCore.QSize:  # pragma: no cover - UI hint
        return QtCore.QSize(1280, 720)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self.buffer = QtGui.QImage(self.size(), QtGui.QImage.Format.Format_ARGB32_Premultiplied)
        self.buffer.fill(QtGui.QColor("black"))

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.drawImage(0, 0, self.buffer)
        painter.end()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = event.key()
        self._set_key_state(key, True)
        if key in (QtCore.Qt.Key.Key_P, QtCore.Qt.Key.Key_Escape):
            self.simulation.paused = not self.simulation.paused
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QtGui.QKeyEvent) -> None:
        self._set_key_state(event.key(), False)
        super().keyReleaseEvent(event)

    def _set_key_state(self, qt_key: int, state: bool) -> None:
        key_map = {
            QtCore.Qt.Key.Key_W: "w",
            QtCore.Qt.Key.Key_A: "a",
            QtCore.Qt.Key.Key_S: "s",
            QtCore.Qt.Key.Key_D: "d",
            QtCore.Qt.Key.Key_Space: " ",
            QtCore.Qt.Key.Key_Control: "control",
            QtCore.Qt.Key.Key_Shift: "shift",
            QtCore.Qt.Key.Key_Left: "arrowleft",
            QtCore.Qt.Key.Key_Right: "arrowright",
            QtCore.Qt.Key.Key_Up: "arrowup",
            QtCore.Qt.Key.Key_Down: "arrowdown",
        }
        if qt_key in key_map:
            self.simulation.keys[key_map[qt_key]] = state

    def _on_tick(self) -> None:
        now = time.perf_counter()
        delta = now - self.last_time
        self.last_time = now
        dt = min(0.05, delta) * 60.0 * self.simulation.config.animation_speed
        self.auto_loop.step(dt, self.simulation.frame_count)
        self.simulation.step(dt)
        self._render_to_buffer()
        self.update()

    def _render_to_buffer(self) -> None:
        if self.buffer.isNull():
            return
        painter = QtGui.QPainter(self.buffer)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        r, g, b, alpha = self.simulation.background_rgba()
        color = QtGui.QColor(r, g, b)
        color.setAlphaF(alpha)
        painter.fillRect(self.buffer.rect(), color)

        painter.setCompositionMode(COMPOSITION_MAP.get(self.simulation.config.composite_operation, QtGui.QPainter.CompositionMode_SourceOver))
        self._draw_resonance_lines(painter)
        self._draw_liks(painter)
        painter.end()

    def _draw_resonance_lines(self, painter: QtGui.QPainter) -> None:
        config = self.simulation.config
        width = self.buffer.width()
        height = self.buffer.height()
        max_dist_sq = config.max_resonance_dist * config.max_resonance_dist
        sample_count = config.line_draw_sample_count
        pulsation = math.sin(self.simulation.frame_count * config.pulsation_speed) * config.max_line_thickness_chaos
        target_pull = config.line_target_pull

        for lik_a, lik_b in self.simulation.lik_pairs_cache:
            dx = lik_b.x - lik_a.x
            dy = lik_b.y - lik_a.y
            dz = lik_b.z - lik_a.z
            dist_sq = dx * dx + dy * dy + dz * dz
            if dist_sq > max_dist_sq:
                continue
            similarity = get_hue_similarity(lik_a.hue, lik_b.hue)
            if similarity < config.resonance_threshold:
                continue
            ax, ay, az, ascale = self.simulation.project_to_canvas(lik_a.x, lik_a.y, lik_a.z, width, height)
            bx, by, bz, bscale = self.simulation.project_to_canvas(lik_b.x, lik_b.y, lik_b.z, width, height)
            if az < -900 or bz < -900:
                continue
            avg_hue = (lik_a.hue + lik_b.hue) / 2.0
            if abs(lik_a.hue - lik_b.hue) > 180:
                avg_hue = (max(lik_a.hue, lik_b.hue) + 360 + min(lik_a.hue, lik_b.hue)) / 2.0
            avg_hue %= 360
            r, g, b = hsl_to_rgb(avg_hue, config.palette_saturation, config.palette_lightness)

            def draw_curve(color: QtGui.QColor) -> None:
                path = QtGui.QPainterPath(QtCore.QPointF(ax, ay))
                for i in range(1, sample_count + 1):
                    t = i / sample_count
                    mid_x = lik_a.x + dx * t
                    mid_y = lik_a.y + dy * t
                    mid_z = lik_a.z + dz * t
                    wiggle_amt = math.sin(t * math.pi) * config.curve_wiggle_factor * math.sqrt(dist_sq)
                    wiggle_angle = math.sin(t * 10 + self.simulation.frame_count * 0.1) * math.tau
                    perp_x = math.cos(wiggle_angle) * wiggle_amt
                    perp_y = math.sin(wiggle_angle) * wiggle_amt
                    mid_x += perp_x
                    mid_y += perp_y
                    mid_z += math.cos(self.simulation.frame_count * 0.05) * wiggle_amt * 0.1
                    pull = t * (1 - t) * target_pull
                    mid_x = mid_x * (1 - pull) + self.simulation.camera.x * pull
                    mid_y = mid_y * (1 - pull) + self.simulation.camera.y * pull
                    mid_z = mid_z * (1 - pull) + self.simulation.camera.z * pull
                    px, py, pz, pscale = self.simulation.project_to_canvas(mid_x, mid_y, mid_z, width, height)
                    if pz < -900:
                        continue
                    path.lineTo(px, py)
                path.lineTo(bx, by)
                thickness = (config.resonance_thickness + pulsation) * similarity * max(ascale, bscale)
                thickness = clamp(thickness, 0.1, 10.0)
                pen = QtGui.QPen(color, thickness, QtCore.Qt.PenStyle.SolidLine, QtCore.Qt.PenCapStyle.RoundCap, QtCore.Qt.PenJoinStyle.RoundJoin)
                painter.setPen(pen)
                painter.drawPath(path)

            base_alpha = max(0.0, min(1.0, config.resonance_alpha))
            if config.rgb_shift_lines and config.rgb_shift_amount > 0:
                angle = math.radians(config.rgb_shift_angle_deg)
                shift = config.rgb_shift_amount
                jitter = (config.rgb_shift_jitter * (math.sin(self.simulation.frame_count * 0.1) - 0.5))
                dx_shift = math.cos(angle) * (shift + jitter)
                dy_shift = math.sin(angle) * (shift + jitter)
                for color, sx, sy in [
                    (QtGui.QColor(r, 0, 0, int(base_alpha * 255)), dx_shift, dy_shift),
                    (QtGui.QColor(0, g, 0, int(base_alpha * 255)), 0.0, 0.0),
                    (QtGui.QColor(0, 0, b, int(base_alpha * 255)), -dx_shift, -dy_shift),
                ]:
                    painter.save()
                    painter.translate(sx, sy)
                    draw_curve(color)
                    painter.restore()
            else:
                draw_curve(QtGui.QColor(r, g, b, int(base_alpha * 255)))

    def _draw_liks(self, painter: QtGui.QPainter) -> None:
        config = self.simulation.config
        if not config.render_liks:
            return
        width = self.buffer.width()
        height = self.buffer.height()
        base_alpha = 255
        for lik in self.simulation.liks:
            px, py, pz, scale = self.simulation.project_to_canvas(lik.x, lik.y, lik.z, width, height)
            if pz < -900:
                continue
            size = config.lik_base_size * scale
            render_size = clamp(size, config.min_lik_render_size, 50.0)
            if render_size < 0.5:
                continue

            def draw_circle(color: QtGui.QColor, offset: Tuple[float, float] = (0.0, 0.0)) -> None:
                painter.setBrush(QtGui.QBrush(color))
                painter.setPen(QtCore.Qt.PenStyle.NoPen)
                painter.drawEllipse(QtCore.QPointF(px + offset[0], py + offset[1]), render_size, render_size)

            if config.rgb_shift_liks and config.rgb_shift_amount > 0:
                angle = math.radians(config.rgb_shift_angle_deg)
                jitter = (config.rgb_shift_jitter * (math.sin(self.simulation.frame_count * 0.05) - 0.5))
                shift = config.rgb_shift_amount + jitter
                dx_shift = math.cos(angle) * shift
                dy_shift = math.sin(angle) * shift
                draw_circle(QtGui.QColor(lik.rgb[0], 0, 0, base_alpha), (dx_shift, dy_shift))
                draw_circle(QtGui.QColor(0, lik.rgb[1], 0, base_alpha), (0.0, 0.0))
                draw_circle(QtGui.QColor(0, 0, lik.rgb[2], base_alpha), (-dx_shift, -dy_shift))
            else:
                draw_circle(QtGui.QColor(*lik.rgb, base_alpha))

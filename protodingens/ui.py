"""Tkinter based user interface for the Protochaos control center."""
from __future__ import annotations

import random
import time
import tkinter as tk
from tkinter import colorchooser
from typing import Dict, List, Tuple

from .autoloop import AutoLoopController
from .config import Config, get_config_value, set_config_value
from .renderer import Renderer
from .simulation import Simulation


class ProtochaosApp:
    """Encapsulates the entire Tk UI and simulation lifecycle."""

    def __init__(self) -> None:
        self.config = Config()
        self.root = tk.Tk()
        self.root.title("Protochaos Feld V18: Sättigung & Resonanz")
        self.root.configure(bg="#000000")
        self.root.geometry("1600x900")
        self.paused = False
        self.simulation = Simulation(self.config)
        self.auto_loop = AutoLoopController(self.config)

        self._build_layout()
        self._build_controls()
        self._build_auto_loop_panel()

        self.root.bind("<Key-p>", lambda _: self._toggle_pause())
        self.root.bind("<Key-P>", lambda _: self._toggle_pause())

        self.renderer = Renderer(self.canvas, self.config)

        self.last_update = time.perf_counter()
        self.root.after(16, self._tick)

    def _build_layout(self) -> None:
        self.canvas = tk.Canvas(self.root, bg="#000000", highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.controls_frame = tk.Frame(
            self.root,
            width=320,
            bg="#001F26",
            highlightbackground="#00FFFF",
            highlightcolor="#00FFFF",
            highlightthickness=2,
        )
        self.controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        self.controls_frame.pack_propagate(False)

        self.toggle_controls_button = tk.Button(
            self.root,
            text="Steuerung Ausblenden",
            command=self._toggle_controls,
            bg="#00FFFF",
            fg="#000000",
            activebackground="#84FFFF",
            relief=tk.FLAT,
            font=("Inter", 10, "bold"),
        )
        self.toggle_controls_button.place(x=340, y=10)

    def _build_controls(self) -> None:
        self.control_vars: Dict[str, tk.Variable] = {}
        self.value_labels: Dict[str, tk.Label] = {}
        self.scales: Dict[str, tk.Scale] = {}
        self.option_menus: Dict[str, tk.Menubutton] = {}
        self.select_display_to_value: Dict[str, Dict[str, str]] = {}
        self.select_value_to_display: Dict[str, Dict[str, str]] = {}

        top_frame = tk.Frame(self.controls_frame, bg="#001F26")
        top_frame.pack(fill=tk.X)

        pause_button = tk.Button(
            top_frame,
            text="Pausieren (P)",
            command=self._toggle_pause,
            bg="#FF416C",
            fg="#FFFFFF",
            activebackground="#00FF00",
            relief=tk.FLAT,
            font=("Inter", 10, "bold"),
        )
        pause_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))
        self.pause_button = pause_button

        randomize_button = tk.Button(
            top_frame,
            text="Zufall (Alle)",
            command=self._randomize_all,
            bg="#00FFFF",
            fg="#000000",
            activebackground="#84FFFF",
            relief=tk.FLAT,
            font=("Inter", 10, "bold"),
        )
        randomize_button.pack(side=tk.LEFT, expand=True, fill=tk.X)

        self.sections: Dict[str, tk.Frame] = {}
        for title in [
            "Canvas",
            "Feld-Geometrie",
            "Schwarm-Verhalten",
            "Interaktion",
            "Resonanzlinien",
            "Linien-Verzerrung",
            "Feld-Farbe",
            "LIK Rendering",
            "RGB Farbverschiebung",
            "Auto Loop",
            "Loop-Parameter Auswahl",
        ]:
            section = tk.Frame(self.controls_frame, bg="#001F26")
            section.pack(fill=tk.X, pady=(8, 2))
            label = tk.Label(
                section,
                text=title,
                bg="#001F26",
                fg="#84FFFF",
                font=("Inter", 11, "bold"),
            )
            label.pack(anchor=tk.W, pady=(4, 4))
            content = tk.Frame(section, bg="#001F26")
            content.pack(fill=tk.X)
            self.sections[title] = content

        self._build_canvas_controls()
        self._build_field_geometry_controls()
        self._build_swarm_controls()
        self._build_interaction_controls()
        self._build_resonance_controls()
        self._build_distortion_controls()
        self._build_palette_controls()
        self._build_render_controls()
        self._build_rgb_shift_controls()
        self._build_auto_loop_controls()

    def _build_canvas_controls(self) -> None:
        frame = self.sections["Canvas"]
        # Background color
        color_frame = tk.Frame(frame, bg="#001F26")
        color_frame.pack(fill=tk.X, pady=2)
        tk.Label(color_frame, text="Hintergrundfarbe", bg="#001F26", fg="#E0F7FA").pack(side=tk.LEFT)
        button = tk.Button(
            color_frame,
            text=self.config.canvas.background_color,
            command=self._pick_background_color,
            relief=tk.FLAT,
        )
        button.pack(side=tk.RIGHT)
        self.background_button = button
        self._update_background_button_style(self.config.canvas.background_color)

        # Composite operation select
        options = [
            ("Normal", "source-over"),
            ("Lighter (Additiv)", "lighter"),
            ("Difference (Invert)", "difference"),
            ("Multiply (Dunkler)", "multiply"),
            ("Screen (Heller)", "screen"),
            ("Overlay", "overlay"),
            ("Hard Light", "hard-light"),
        ]
        self._create_select(
            frame,
            "Render Modus",
            "compositeOperation",
            options,
        )

    def _build_field_geometry_controls(self) -> None:
        frame = self.sections["Feld-Geometrie"]
        specs = [
            ("Max. LIKs", "maxLikCount", 50, 1000, 50, "{:.0f}"),
            ("Min. LIKs", "minLikCount", 10, 500, 10, "{:.0f}"),
            ("Max. Lebensdauer (Frames)", "maxLikLifespan", 100, 5000, 100, "{:.0f}"),
            ("Universum-Radius", "universeRadius", 100, 2000, 50, "{:.0f}"),
        ]
        for label, key, min_, max_, step, fmt in specs:
            self._create_slider(frame, label, key, min_, max_, step, fmt)

    def _build_swarm_controls(self) -> None:
        frame = self.sections["Schwarm-Verhalten"]
        specs = [
            ("Anziehungs-Stärke", "attractionStrength", 0.0001, 0.01, 0.0001, "{:.4f}"),
            ("Farb-Ähnlichkeits-Schwelle", "attractionSimilarityThreshold", 0.0, 1.0, 0.01, "{:.2f}"),
            ("Abstoßungs-Stärke", "repulsionStrength", 0.0001, 0.02, 0.0001, "{:.4f}"),
            ("Basis-Wander-Geschw.", "baseMigrationSpeed", 0.0001, 0.01, 0.0001, "{:.4f}"),
            ("Pers. Bereich Radius", "personalSpaceRadius", 10, 500, 10, "{:.0f}"),
            ("Pers. Bereich Abstoßung", "personalSpaceRepulsion", 0.01, 1.0, 0.01, "{:.2f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)

    def _build_interaction_controls(self) -> None:
        frame = self.sections["Interaktion"]
        specs = [
            ("Globale Drift Stärke", "globalDriftStrength", 0.0, 0.5, 0.01, "{:.2f}"),
            ("Globale Drift Impuls", "globalDriftMomentum", 0.8, 0.999, 0.001, "{:.3f}"),
            ("Animations-Geschw.", "animationSpeed", 0.1, 5.0, 0.1, "{:.1f}"),
            ("Kamera-Geschw.", "cameraMovementSpeed", 1.0, 20.0, 1.0, "{:.0f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)

    def _build_resonance_controls(self) -> None:
        frame = self.sections["Resonanzlinien"]
        specs = [
            ("Linien Zeichnung Sample", "lineDrawSampleCount", 1, 100, 1, "{:.0f}"),
            ("Resonanz Dicke", "resonanceThickness", 0.1, 5.0, 0.1, "{:.1f}"),
            ("Max. Dicke Chaos", "maxLineThicknessChaos", 0.0, 1.0, 0.01, "{:.2f}"),
            ("Resonanz Alpha", "resonanceAlpha", 0.01, 1.0, 0.01, "{:.2f}"),
            ("Max. Resonanz Dist.", "maxResonanceDist", 50, 1000, 10, "{:.0f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)

    def _build_distortion_controls(self) -> None:
        frame = self.sections["Linien-Verzerrung"]
        specs = [
            ("Kurven-Wiggle-Faktor", "curveWiggleFactor", 0.0, 1.0, 0.01, "{:.2f}"),
            ("Pulsations-Geschw.", "pulsationSpeed", 0.01, 1.0, 0.01, "{:.2f}"),
            ("Linien-Ziel-Zug", "lineTargetPull", 0.01, 1.0, 0.01, "{:.2f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)

    def _build_palette_controls(self) -> None:
        frame = self.sections["Feld-Farbe"]
        specs = [
            ("LIK Sättigung", "paletteSaturation", 0, 100, 1, "{:.0f}"),
            ("LIK Helligkeit", "paletteLightness", 0, 100, 1, "{:.0f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)

    def _build_render_controls(self) -> None:
        frame = self.sections["LIK Rendering"]
        self._create_checkbox(frame, "LIKs rendern", "renderLiks")
        specs = [
            ("Basisgröße LIK", "likBaseSize", 1.0, 15.0, 0.1, "{:.1f}"),
            ("Min. Rendergröße", "minLikRenderSize", 0.1, 5.0, 0.1, "{:.1f}"),
            ("Spur Alpha", "trailAlpha", 0.0, 1.0, 0.01, "{:.2f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)

    def _build_rgb_shift_controls(self) -> None:
        frame = self.sections["RGB Farbverschiebung"]
        self._create_checkbox(frame, "RGB Shift auf LIKs", "rgbShiftLiks")
        self._create_checkbox(frame, "RGB Shift auf Linien", "rgbShiftLines")
        specs = [
            ("Shift Stärke (px)", "rgbShiftAmount", 0.0, 15.0, 0.1, "{:.1f}"),
            ("Shift Winkel (Grad)", "rgbShiftAngle", 0, 360, 1, "{:.0f}"),
            ("Shift Jitter", "rgbShiftJitter", 0.0, 1.0, 0.01, "{:.2f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)
        options = [("Additiv", "add"), ("Subtraktiv", "subtract")]
        self._create_select(frame, "Shift Modus", "rgbShiftMode", options)

    def _build_auto_loop_controls(self) -> None:
        frame = self.sections["Auto Loop"]
        self._create_checkbox(frame, "Auto Loop Aktiviert", "autoLoopEnabled")
        specs = [
            ("Loop Geschwindigkeit", "autoLoopSpeed", 0.1, 5.0, 0.1, "{:.1f}"),
            ("Loop Bereich (Limes)", "autoLoopLimes", 0.0, 0.5, 0.01, "{:.2f}"),
            ("Loop Jitter", "autoLoopJitter", 0.0, 0.5, 0.01, "{:.2f}"),
        ]
        for spec in specs:
            self._create_slider(frame, *spec)
        randomize = tk.Button(
            frame,
            text="Zufällige Loop Parameter",
            command=self._randomize_loop,
            bg="#00FFFF",
            fg="#000000",
            activebackground="#84FFFF",
            relief=tk.FLAT,
        )
        randomize.pack(fill=tk.X, pady=(6, 0))

    def _build_auto_loop_panel(self) -> None:
        frame = self.sections["Loop-Parameter Auswahl"]
        self.loop_checkboxes: Dict[str, tk.IntVar] = {}
        for key in AutoLoopController.LOOPABLE_KEYS:
            if key not in self.auto_loop.entries:
                continue
            container = tk.Frame(frame, bg="#001F26")
            container.pack(fill=tk.X, pady=1)
            var = tk.IntVar(value=0)
            cb = tk.Checkbutton(
                container,
                text=self._format_loop_label(key),
                variable=var,
                bg="#001F26",
                fg="#E0F7FA",
                selectcolor="#00363F",
                activebackground="#001F26",
                command=lambda k=key, v=var: self._toggle_loop_param(k, v),
            )
            cb.pack(anchor=tk.W)
            self.loop_checkboxes[key] = var

    def _build_auto_loop_panel_refresh(self) -> None:
        frame = self.sections["Loop-Parameter Auswahl"]
        for child in frame.winfo_children():
            child.destroy()
        self._build_auto_loop_panel()

    def _create_slider(
        self,
        parent: tk.Frame,
        label: str,
        key: str,
        minimum: float,
        maximum: float,
        step: float,
        fmt: str,
    ) -> None:
        row = tk.Frame(parent, bg="#001F26")
        row.pack(fill=tk.X, pady=2)
        lbl = tk.Label(row, text=label, bg="#001F26", fg="#E0F7FA")
        lbl.pack(side=tk.LEFT, anchor=tk.W)
        value_label = tk.Label(row, text="", bg="#001F26", fg="#00FFFF", font=("Inter", 9, "normal"))
        value_label.pack(side=tk.RIGHT)
        var = tk.DoubleVar()
        var.set(get_config_value(self.config, key))
        step_value = float(step)
        scale = tk.Scale(
            parent,
            from_=minimum,
            to=maximum,
            orient=tk.HORIZONTAL,
            resolution=step_value,
            showvalue=False,
            bg="#001F26",
            troughcolor="#00363F",
            highlightthickness=0,
            sliderrelief=tk.FLAT,
            variable=var,
        )
        scale.pack(fill=tk.X)

        def update_value(*_: str) -> None:
            value = var.get()
            if step_value.is_integer():
                value = int(round(value))
            set_config_value(self.config, key, value)
            value_label.configure(text=fmt.format(value))

        var.trace_add("write", update_value)
        update_value()

        self.control_vars[key] = var
        self.value_labels[key] = value_label
        self.scales[key] = scale

        if key in AutoLoopController.LOOPABLE_KEYS:
            self.auto_loop.register_slider(
                key,
                getter=lambda v=var: v.get(),
                setter=lambda value, v=var: v.set(value),
                minimum=minimum,
                maximum=maximum,
            )

    def _create_checkbox(self, parent: tk.Frame, label: str, key: str) -> None:
        var = tk.IntVar(value=1 if get_config_value(self.config, key) else 0)
        cb = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            bg="#001F26",
            fg="#E0F7FA",
            selectcolor="#00363F",
            activebackground="#001F26",
        )
        cb.pack(anchor=tk.W, pady=2)

        def toggle() -> None:
            set_config_value(self.config, key, bool(var.get()))

        var.trace_add("write", lambda *_: toggle())
        self.control_vars[key] = var

    def _create_select(
        self,
        parent: tk.Frame,
        label: str,
        key: str,
        options: List[Tuple[str, str]],
    ) -> None:
        row = tk.Frame(parent, bg="#001F26")
        row.pack(fill=tk.X, pady=2)
        tk.Label(row, text=label, bg="#001F26", fg="#E0F7FA").pack(anchor=tk.W)
        display_to_value = {display: value for display, value in options}
        value_to_display = {value: display for display, value in options}
        current_value = get_config_value(self.config, key)
        current_display = value_to_display.get(current_value, next(iter(display_to_value)))
        var = tk.StringVar(value=current_display)
        option_menu = tk.OptionMenu(
            parent,
            var,
            *display_to_value.keys(),
        )
        option_menu.configure(bg="#001F26", fg="#84FFFF", highlightthickness=0, relief=tk.FLAT)
        option_menu.pack(fill=tk.X)
        self.option_menus[key] = option_menu
        self.select_display_to_value[key] = display_to_value
        self.select_value_to_display[key] = value_to_display

        def on_change(*_: str) -> None:
            selected = var.get()
            set_config_value(self.config, key, display_to_value[selected])

        var.trace_add("write", on_change)
        self.control_vars[key] = var

        if key in AutoLoopController.LOOPABLE_KEYS:
            self.auto_loop.register_select(
                key,
                getter=lambda v=var, mapping=display_to_value: mapping[v.get()],
                setter=lambda value, v=var, reverse=value_to_display: v.set(
                    reverse.get(value, list(reverse.values())[0] if reverse else "")
                ),
                options=[value for _, value in options],
            )

    def _format_loop_label(self, key: str) -> str:
        readable = "".join(" " + ch if ch.isupper() else ch for ch in key).strip()
        readable = readable.replace("Lik", "LIK").replace("Rgb", "RGB")
        return readable.capitalize()

    def _toggle_controls(self) -> None:
        if self.controls_frame.winfo_viewable():
            self.controls_frame.pack_forget()
            self.toggle_controls_button.configure(text="Steuerung Einblenden")
        else:
            self.controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
            self.toggle_controls_button.configure(text="Steuerung Ausblenden")

    def _toggle_pause(self) -> None:
        self.paused = not self.paused
        if self.paused:
            self.pause_button.configure(text="Fortsetzen", bg="#00FF00")
        else:
            self.pause_button.configure(text="Pausieren (P)", bg="#FF416C")

    def _randomize_all(self) -> None:
        bg_color = f"#{random.randint(0, 0xFFFFFF):06X}"
        set_config_value(self.config, "backgroundColor", bg_color)
        self._update_background_button_style(bg_color)
        for key, var in self.control_vars.items():
            if isinstance(var, tk.DoubleVar) and key in self.scales:
                scale = self.scales[key]
                minimum = float(scale.cget("from"))
                maximum = float(scale.cget("to"))
                resolution = float(scale.cget("resolution"))
                value = random.uniform(minimum, maximum)
                if resolution.is_integer():
                    value = int(round(value))
                var.set(value)
            elif isinstance(var, tk.IntVar):
                var.set(random.choice([0, 1]))
            elif isinstance(var, tk.StringVar) and key in self.select_display_to_value:
                choices = list(self.select_display_to_value[key].keys())
                if choices:
                    var.set(random.choice(choices))
        self.simulation.rebuild_population()

    def _randomize_loop(self) -> None:
        self.auto_loop.randomize_targets()

    def _toggle_loop_param(self, key: str, var: tk.IntVar) -> None:
        active = bool(var.get())
        self.auto_loop.toggle_parameter(key, active)
        if active:
            entry = self.auto_loop.entries[key]
            if not entry.is_select:
                entry.reset_range(self.config)

    def _pick_background_color(self) -> None:
        color = colorchooser.askcolor(color=self.config.canvas.background_color)
        if color and color[1]:
            set_config_value(self.config, "backgroundColor", color[1])
            self._update_background_button_style(color[1])

    def _update_background_button_style(self, hex_color: str) -> None:
        try:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
        except (ValueError, TypeError):
            r = g = b = 0
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        text_color = "#000000" if luminance > 0.5 else "#FFFFFF"
        self.background_button.configure(
            text=hex_color,
            bg=hex_color,
            activebackground=hex_color,
            fg=text_color,
        )

    def _tick(self) -> None:
        now = time.perf_counter()
        elapsed = now - self.last_update
        self.last_update = now
        self.auto_loop.set_enabled(self.config.auto_loop.auto_loop_enabled)
        if not self.paused:
            steps = max(1, int(elapsed * 60 * self.config.interaction.animation_speed))
            for _ in range(steps):
                self.simulation.step()
            self.auto_loop.update(steps, self.simulation.state.frame)
            self.renderer.render(self.simulation.state)
        else:
            self.renderer.render(self.simulation.state)
        self.root.after(16, self._tick)

    def run(self) -> None:
        self.root.mainloop()


def launch() -> None:
    app = ProtochaosApp()
    app.run()

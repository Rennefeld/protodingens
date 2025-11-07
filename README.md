# ProtoDingens Python Port

This repository contains a modular PySide6 implementation of the ProtoDingens neon swarm blueprint. The application mirrors the HTML blueprint's functionality with a native desktop stack that combines a painter-based renderer with a fully data-bound control panel.

## Running the application

```bash
pip install -e .
python -m protodingens
```

Oder starte das installierte Konsolenskript:

```bash
protodingens
```

> **Note:** The runtime requires PySide6. Install it before launching the application.

## Project structure

- `src/protodingens/config.py` – declarative configuration schema shared between UI and simulation.
- `src/protodingens/models/lik.py` – particle domain model that implements the swarm behaviour.
- `src/protodingens/auto_loop.py` – Auto-Loop engine that animates parameters just like the web version.
- `src/protodingens/simulation.py` – orchestrates LIK lifecycle management, resonance pairing, and background drift.
- `src/protodingens/rendering/canvas.py` – painter-based renderer that mimics the neon canvas with RGB shift.
- `src/protodingens/ui/controls_panel.py` – dynamic control panel matching the HTML sections.
- `src/protodingens/ui/main_window.py` – wires the renderer with the control panel inside a Qt window.
- `src/protodingens/app.py` – entry point that bootstraps the Qt application.

## Design notes

The codebase follows SOLID and KISS principles:

- The `Config` dataclass is the single source of truth, enforcing consistent validation for every UI control.
- Rendering, simulation, and UI live in separate modules to avoid monoliths and ease future extensions (e.g., shader-based renderers).
- Signals/slots, auto-loop controllers, and particle logic are fully decoupled for testability and experimentation.

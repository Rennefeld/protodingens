"""Module entry point to allow ``python -m protodingens``."""
from __future__ import annotations

from .app import main


if __name__ == "__main__":  # pragma: no cover - thin module wrapper
    raise SystemExit(main())

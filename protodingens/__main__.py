"""Module runner shim for ``python -m protodingens`` when using the src layout."""
from __future__ import annotations

from .app import main

if __name__ == "__main__":  # pragma: no cover - module CLI entry point
    raise SystemExit(main())

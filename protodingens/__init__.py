"""Bootstrap package to support ``python -m protodingens`` without installation."""
from __future__ import annotations

from importlib import util
from importlib.machinery import ModuleSpec
from pathlib import Path
import runpy
import sys

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_SRC_ROOT = _PROJECT_ROOT / "src"
_SRC_PKG_DIR = _SRC_ROOT / "protodingens"
_SRC_INIT = _SRC_PKG_DIR / "__init__.py"

if not _SRC_INIT.exists():  # pragma: no cover - defensive guard for corrupted installs
    raise ImportError(
        "Could not locate the source package. Ensure the 'src' layout is intact."
    )

if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

__path__ = [str(_SRC_PKG_DIR)]

_spec: ModuleSpec | None = util.spec_from_file_location(__name__, _SRC_INIT)
if _spec is not None:
    __spec__ = _spec  # type: ignore[assignment]

_namespace = runpy.run_path(
    str(_SRC_INIT),
    init_globals={
        "__name__": __name__,
        "__package__": __name__,
        "__doc__": __doc__,
        "__spec__": __spec__,
        "__path__": __path__,
    },
)

globals().update({k: v for k, v in _namespace.items() if k not in {"__name__", "__package__", "__spec__"}})


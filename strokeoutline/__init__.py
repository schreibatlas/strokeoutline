"""Deterministic variable-width stroke outlining for planar centerlines."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from planarcurve import CubicBezier, CubicPath, Point2D, QuadraticBezier

from .core import (
    DEFAULT_OUTLINE_CONFIG,
    CapStyle,
    Contour,
    DegeneratePathError,
    InvalidWidthError,
    OutlineConfig,
    OutlineError,
    OutlineResult,
    SubdivisionLimitError,
    WidthProfile,
    combine_outlines,
    expand_tap,
    outline,
    outline_disc,
    signed_area,
    winding,
)
from .model import (
    Line,
    Path2D,
    Segment,
    Subpath,
    path_from_cubic_path,
    path_from_polyline,
)

try:
    __version__ = version("strokeoutline")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "DEFAULT_OUTLINE_CONFIG",
    "CapStyle",
    "Contour",
    "CubicBezier",
    "CubicPath",
    "DegeneratePathError",
    "InvalidWidthError",
    "Line",
    "OutlineConfig",
    "OutlineError",
    "OutlineResult",
    "Path2D",
    "Point2D",
    "QuadraticBezier",
    "Segment",
    "Subpath",
    "SubdivisionLimitError",
    "WidthProfile",
    "__version__",
    "combine_outlines",
    "expand_tap",
    "outline",
    "outline_disc",
    "path_from_cubic_path",
    "path_from_polyline",
    "signed_area",
    "winding",
]

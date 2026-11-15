"""Optional SVG path adapter based on FontTools.

The core package does not require FontTools. This adapter intentionally owns
only the compatibility bridge needed for the initial InkGrammar extraction.
A future planarcurve public parsed-path API can replace this parser without
changing the core outlining API.
"""

from __future__ import annotations

try:
    from fontTools.pens.recordingPen import RecordingPen
    from fontTools.svgLib.path import parse_path
except ImportError as exc:  # pragma: no cover
    raise ImportError("strokeoutline.svg requires FontTools; install strokeoutline[svg]") from exc

from planarcurve import CubicBezier, QuadraticBezier

from .core import (
    DEFAULT_OUTLINE_CONFIG,
    OutlineConfig,
    OutlineResult,
    WidthParameterization,
    WidthProfile,
    outline,
)
from .model import Line, Path2D, Subpath


def path_from_svg(path: str) -> Path2D:
    """Parse SVG path data into StrokeOutline's neutral path model.

    Parameters
    ----------
    path : str
        SVG path data to parse.

    Returns
    -------
    Path2D
        The parsed line, quadratic, and cubic subpaths.

    Raises
    ------
    ValueError
        If the data contains no drawable segments or an unsupported/invalid
        path operation.

    Notes
    -----
    This function requires FontTools from the optional ``svg`` extra. It parses
    path geometry only; it does not render SVG/CSS strokes.
    """
    pen = RecordingPen()
    parse_path(path, pen)
    if not pen.value:
        raise ValueError("path produced no operations")

    subpaths: list[Subpath] = []
    segments = []
    current = None
    start = None

    def finish(*, closed: bool) -> None:
        nonlocal segments
        if segments:
            subpaths.append(Subpath(tuple(segments), closed=closed))
        segments = []

    for operator, args in pen.value:
        if operator == "moveTo":
            finish(closed=False)
            current = start = tuple(map(float, args[0]))
        elif operator == "lineTo":
            if current is None:
                raise ValueError("outline path draws before moveTo")
            end = tuple(map(float, args[0]))
            segments.append(Line(current, end))
            current = end
        elif operator == "curveTo":
            if current is None or len(args) != 3:
                raise ValueError("outline path has an invalid cubic segment")
            c1, c2, end = (tuple(map(float, value)) for value in args)
            segments.append(CubicBezier(current, c1, c2, end))
            current = end
        elif operator == "qCurveTo":
            if current is None or len(args) != 2 or args[-1] is None:
                raise ValueError("outline path has an invalid quadratic segment")
            control, end = (tuple(map(float, value)) for value in args)
            segments.append(QuadraticBezier(current, control, end))
            current = end
        elif operator == "closePath":
            if current is None or start is None:
                raise ValueError("outline path closes before moveTo")
            finish(closed=True)
            current = start = None
        elif operator == "endPath":
            finish(closed=False)
            current = start = None
        else:
            raise ValueError(f"unsupported outline path operation: {operator}")

    finish(closed=False)
    if not subpaths:
        raise ValueError("outline path has no drawable segments")
    return Path2D(tuple(subpaths))


def outline_svg_path(
    path: str,
    width: WidthProfile,
    *,
    config: OutlineConfig = DEFAULT_OUTLINE_CONFIG,
    width_parameterization: WidthParameterization | None = None,
) -> OutlineResult:
    """Parse and expand SVG path data into closed sampled contours.

    Parameters
    ----------
    path : str
        SVG path data to parse.
    width : WidthProfile
        Constant, piecewise-linear, or callable full-diameter width profile.
    config : OutlineConfig, optional
        Adaptive sampling tolerances and open-path cap selection.
    width_parameterization : WidthParameterization, optional
        Width progress domain. When omitted, uses ``config.width_parameterization``,
        which defaults to ``"segment"``.

    Returns
    -------
    OutlineResult
        Closed contour tuples and aggregate bounds.

    Raises
    ------
    ValueError
        If SVG path data cannot be converted to the supported neutral model.
    InvalidWidthError
        If the width profile is invalid.
    DegeneratePathError
        If the parsed centerline contains degenerate geometry.
    SubdivisionLimitError
        If adaptive sampling cannot meet the configured tolerances.

    Notes
    -----
    Importing this module requires FontTools from the optional ``svg`` extra.
    The adapter parses path geometry; it is not a complete SVG/CSS stroker.
    """
    return outline(
        path_from_svg(path),
        width,
        config=config,
        width_parameterization=width_parameterization,
    )


# Compatibility name matching InkGrammar's previous generic entry point.
expand_path = outline_svg_path

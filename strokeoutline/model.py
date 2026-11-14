from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypeAlias

from planarcurve import CubicBezier, CubicPath, Point2D, QuadraticBezier

from ._validation import normalize_point


@dataclass(frozen=True)
class Line:
    """Finite straight segment between two 2D endpoints.

    Parameters
    ----------
    p0 : Point2D
        Start coordinate.
    p1 : Point2D
        End coordinate.

    Both endpoints must contain exactly two finite coordinates. A zero-length
    line can be constructed, but ``outline()`` rejects it as degenerate.
    """

    p0: Point2D
    p1: Point2D

    def __post_init__(self) -> None:
        object.__setattr__(self, "p0", normalize_point(self.p0, name="p0"))
        object.__setattr__(self, "p1", normalize_point(self.p1, name="p1"))


Segment: TypeAlias = Line | QuadraticBezier | CubicBezier


def segment_start(segment: Segment) -> Point2D:
    return segment.p0


def segment_end(segment: Segment) -> Point2D:
    if isinstance(segment, Line):
        return segment.p1
    if isinstance(segment, QuadraticBezier):
        return segment.p2
    return segment.p3


@dataclass(frozen=True)
class Subpath:
    """One ordered, connected centerline subpath.

    Parameters
    ----------
    segments : Sequence[Segment]
        Non-empty ordered sequence of ``Line``, ``QuadraticBezier``, or
        ``CubicBezier`` segments. Adjacent endpoints must compare exactly equal.
    closed : bool, optional
        If true, add an implicit closing ``Line`` during outlining when the
        final endpoint differs from the first start point.

    Raises
    ------
    ValueError
        If no segments are provided or adjacent segments are disconnected.
    TypeError
        If a segment has an unsupported type.

    Notes
    -----
    Repeating the start point with an explicit segment is not required for a
    closed subpath. Outlining a zero-length segment raises
    ``DegeneratePathError``.
    """

    segments: Sequence[Segment]
    closed: bool = False

    def __post_init__(self) -> None:
        segments = tuple(self.segments)
        if not segments:
            raise ValueError("subpath requires at least one segment")
        allowed = (Line, QuadraticBezier, CubicBezier)
        if not all(isinstance(segment, allowed) for segment in segments):
            raise TypeError("segments must contain Line, QuadraticBezier, or CubicBezier values")
        for left, right in zip(segments, segments[1:], strict=False):
            if segment_end(left) != segment_start(right):
                raise ValueError("subpath segments must be connected in order")
        object.__setattr__(self, "segments", segments)

    def outlining_segments(self) -> tuple[Segment, ...]:
        segments = tuple(self.segments)
        if self.closed:
            start = segment_start(segments[0])
            end = segment_end(segments[-1])
            if end != start:
                segments = (*segments, Line(end, start))
        return segments


@dataclass(frozen=True)
class Path2D:
    """A path containing one or more independent centerline subpaths.

    Parameters
    ----------
    subpaths : Sequence[Subpath]
        Non-empty sequence of subpaths to outline independently.

    Raises
    ------
    ValueError
        If no subpaths are provided.
    TypeError
        If an element is not a ``Subpath``.

    Notes
    -----
    Each subpath receives a separate outline, and normalized width progress
    restarts at zero for each one.
    """

    subpaths: Sequence[Subpath]

    def __post_init__(self) -> None:
        subpaths = tuple(self.subpaths)
        if not subpaths:
            raise ValueError("path requires at least one subpath")
        if not all(isinstance(subpath, Subpath) for subpath in subpaths):
            raise TypeError("subpaths must contain Subpath values")
        object.__setattr__(self, "subpaths", subpaths)


def path_from_cubic_path(path: CubicPath, *, closed: bool = False) -> Path2D:
    """Adapt a :class:`planarcurve.CubicPath` into a ``Path2D``.

    Parameters
    ----------
    path : planarcurve.CubicPath
        Cubic path to adapt.
    closed : bool, optional
        Whether the adapted subpath should be implicitly closed during outlining.

    Returns
    -------
    Path2D
        A path containing one subpath with the cubic path's Bézier segments.

    Raises
    ------
    ValueError
        If the cubic path contains no segments.
    """
    beziers = path.to_beziers()
    if not beziers:
        raise ValueError("cubic path requires at least one segment")
    return Path2D((Subpath(beziers, closed=closed),))


def path_from_polyline(points: Sequence[Sequence[float]], *, closed: bool = False) -> Path2D:
    """Build a path from ordered finite 2D points.

    Parameters
    ----------
    points : Sequence[Sequence[float]]
        At least two finite ``(x, y)`` coordinates, in path order.
    closed : bool, optional
        If true, close the path implicitly during outlining; the first point
        need not be repeated.

    Returns
    -------
    Path2D
        A path containing one subpath made from consecutive line segments.

    Raises
    ------
    ValueError
        If fewer than two points are supplied or a point is not a finite pair.

    Notes
    -----
    Repeated adjacent points are retained. Outlining a resulting zero-length
    segment raises ``DegeneratePathError``.
    """
    finite_points = tuple(
        normalize_point(point, name=f"points[{index}]") for index, point in enumerate(points)
    )
    if len(finite_points) < 2:
        raise ValueError("polyline requires at least two points")
    segments = tuple(
        Line(start, end) for start, end in zip(finite_points, finite_points[1:], strict=False)
    )
    return Path2D((Subpath(segments, closed=closed),))

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite
from typing import TypeAlias

from planarcurve import CubicBezier, CubicPath, Point2D, QuadraticBezier


def _point(value: Sequence[float], *, name: str) -> Point2D:
    if len(value) != 2:
        raise ValueError(f"{name} must have exactly two coordinates")
    point = (float(value[0]), float(value[1]))
    if not all(isfinite(component) for component in point):
        raise ValueError(f"{name} must contain finite coordinates")
    return point


@dataclass(frozen=True)
class Line:
    """Finite straight line segment."""

    p0: Point2D
    p1: Point2D

    def __post_init__(self) -> None:
        object.__setattr__(self, "p0", _point(self.p0, name="p0"))
        object.__setattr__(self, "p1", _point(self.p1, name="p1"))


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
    """One connected centerline subpath.

    When ``closed=True`` and the final endpoint differs from the first start,
    outlining adds the implicit closing line before sampling. This matches SVG
    ``closePath`` behavior and the InkGrammar implementation this package was
    extracted from.
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
    """A path made from one or more independent centerline subpaths."""

    subpaths: Sequence[Subpath]

    def __post_init__(self) -> None:
        subpaths = tuple(self.subpaths)
        if not subpaths:
            raise ValueError("path requires at least one subpath")
        if not all(isinstance(subpath, Subpath) for subpath in subpaths):
            raise TypeError("subpaths must contain Subpath values")
        object.__setattr__(self, "subpaths", subpaths)


def path_from_cubic_path(path: CubicPath, *, closed: bool = False) -> Path2D:
    """Adapt :class:`planarcurve.CubicPath` into a strokeoutline path."""
    beziers = path.to_beziers()
    if not beziers:
        raise ValueError("cubic path requires at least one segment")
    return Path2D((Subpath(beziers, closed=closed),))

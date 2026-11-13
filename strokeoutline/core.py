from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from math import acos, atan2, ceil, cos, degrees, hypot, isfinite, pi, sin
from typing import Literal, TypeAlias

from planarcurve import CubicBezier, CubicPath, Point2D, QuadraticBezier

from .model import Line, Path2D, Segment, Subpath, path_from_cubic_path

WidthProfile: TypeAlias = float | Sequence[tuple[float, float]] | Callable[[float], float]
Contour: TypeAlias = tuple[Point2D, ...]
CapStyle: TypeAlias = Literal["round", "square"]


class OutlineError(ValueError):
    """Base class for geometric outlining failures."""


class InvalidWidthError(OutlineError):
    """Raised when a width profile is malformed or non-positive."""


class DegeneratePathError(OutlineError):
    """Raised when a centerline contains degenerate geometry."""


class SubdivisionLimitError(OutlineError):
    """Raised when adaptive sampling cannot satisfy configured tolerances."""


@dataclass(frozen=True)
class OutlineConfig:
    """Adaptive sampling and cap configuration."""

    max_centerline_error: float = 0.25
    max_width_error: float = 0.25
    max_normal_angle_degrees: float = 3.0
    cap: CapStyle = "round"
    max_subdivision_depth: int = 18

    def __post_init__(self) -> None:
        tolerances = (
            self.max_centerline_error,
            self.max_width_error,
            self.max_normal_angle_degrees,
        )
        if any(not isfinite(value) or value <= 0 for value in tolerances):
            raise ValueError("outline tolerances must be positive and finite")
        if self.max_normal_angle_degrees >= 180:
            raise ValueError("normal angle tolerance must be less than 180 degrees")
        if self.cap not in {"round", "square"}:
            raise ValueError("cap must be 'round' or 'square'")
        if (
            isinstance(self.max_subdivision_depth, bool)
            or not isinstance(self.max_subdivision_depth, int)
            or self.max_subdivision_depth < 1
        ):
            raise ValueError("maximum subdivision depth must be a positive integer")


DEFAULT_OUTLINE_CONFIG = OutlineConfig()


@dataclass(frozen=True)
class OutlineResult:
    contours: tuple[Contour, ...]
    bounds: tuple[float, float, float, float] | None


def _lerp(a: Point2D, b: Point2D, t: float) -> Point2D:
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _point_on(segment: Segment, t: float) -> Point2D:
    if isinstance(segment, Line):
        return _lerp(segment.p0, segment.p1, t)
    if isinstance(segment, QuadraticBezier):
        return _lerp(_lerp(segment.p0, segment.p1, t), _lerp(segment.p1, segment.p2, t), t)
    a = _lerp(segment.p0, segment.p1, t)
    b = _lerp(segment.p1, segment.p2, t)
    c = _lerp(segment.p2, segment.p3, t)
    return _lerp(_lerp(a, b, t), _lerp(b, c, t), t)


def _tangent(segment: Segment, t: float) -> Point2D:
    if isinstance(segment, Line):
        return (segment.p1[0] - segment.p0[0], segment.p1[1] - segment.p0[1])
    if isinstance(segment, QuadraticBezier):
        return (
            2 * ((1 - t) * (segment.p1[0] - segment.p0[0]) + t * (segment.p2[0] - segment.p1[0])),
            2 * ((1 - t) * (segment.p1[1] - segment.p0[1]) + t * (segment.p2[1] - segment.p1[1])),
        )
    u = 1 - t
    return (
        3
        * (
            u * u * (segment.p1[0] - segment.p0[0])
            + 2 * u * t * (segment.p2[0] - segment.p1[0])
            + t * t * (segment.p3[0] - segment.p2[0])
        ),
        3
        * (
            u * u * (segment.p1[1] - segment.p0[1])
            + 2 * u * t * (segment.p2[1] - segment.p1[1])
            + t * t * (segment.p3[1] - segment.p2[1])
        ),
    )


def _width_function(profile: WidthProfile) -> Callable[[float], float]:
    if callable(profile):
        function = profile
    elif isinstance(profile, (int, float)) and not isinstance(profile, bool):
        constant = float(profile)

        def constant_width(_u: float) -> float:
            return constant

        function = constant_width
    else:
        try:
            knots = tuple((float(position), float(width)) for position, width in profile)
        except (TypeError, ValueError) as exc:
            raise InvalidWidthError(
                "width must be a positive number, knot sequence, or callable"
            ) from exc
        if any(
            not isfinite(position) or not isfinite(width) or width <= 0 for position, width in knots
        ):
            raise InvalidWidthError("width profile knots must be finite with positive widths")
        if len(knots) < 2:
            raise InvalidWidthError("width profile requires at least two knots")
        if knots[0][0] != 0 or knots[-1][0] != 1:
            raise InvalidWidthError("width profile must span parameter values 0 through 1")
        if any(b[0] <= a[0] for a, b in zip(knots, knots[1:], strict=False)):
            raise InvalidWidthError("width profile parameters must increase")

        def function(u: float) -> float:
            for (u0, w0), (u1, w1) in zip(knots, knots[1:], strict=False):
                if u <= u1:
                    return w0 + (w1 - w0) * (u - u0) / (u1 - u0)
            return knots[-1][1]

    try:
        probes = (float(function(0.0)), float(function(0.5)), float(function(1.0)))
    except (TypeError, ValueError) as exc:
        raise InvalidWidthError("width callable must return numeric values") from exc
    if any(not isfinite(value) or value <= 0 for value in probes):
        raise InvalidWidthError("outline widths must be finite and positive")
    return function


def _unit(vector: Point2D) -> Point2D:
    length = hypot(*vector)
    if length <= 1e-12:
        raise DegeneratePathError("outline contains a zero-length tangent")
    return (vector[0] / length, vector[1] / length)


def _shift(point: Point2D, direction: Point2D, distance: float) -> Point2D:
    return (point[0] + direction[0] * distance, point[1] + direction[1] * distance)


def _distance_to_chord(point: Point2D, start: Point2D, end: Point2D) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length2 = dx * dx + dy * dy
    if length2 <= 1e-24:
        return hypot(point[0] - start[0], point[1] - start[1])
    u = max(0.0, min(1.0, ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length2))
    projection = (start[0] + u * dx, start[1] + u * dy)
    return hypot(point[0] - projection[0], point[1] - projection[1])


def _angle_between(left: Point2D, right: Point2D) -> float:
    a, b = _unit(left), _unit(right)
    return degrees(acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1]))))


def _flatten_segment(
    segment: Segment,
    segment_index: int,
    segment_count: int,
    width_at: Callable[[float], float],
    config: OutlineConfig,
) -> list[tuple[float, Point2D]]:
    def subdivide(t0: float, t1: float, depth: int) -> list[tuple[float, Point2D]]:
        p0, p1 = _point_on(segment, t0), _point_on(segment, t1)
        span = t1 - t0
        probes = [_point_on(segment, t0 + span * fraction) for fraction in (0.25, 0.5, 0.75)]
        chord_error = max(_distance_to_chord(point, p0, p1) for point in probes)
        tangent0 = _tangent(segment, t0)
        tangent1 = _tangent(segment, t1)
        tangent_mid = _tangent(segment, (t0 + t1) / 2)
        chord = (p1[0] - p0[0], p1[1] - p0[1])
        if hypot(*tangent0) <= 1e-12:
            tangent0 = chord
        if hypot(*tangent1) <= 1e-12:
            tangent1 = chord
        if hypot(*tangent_mid) <= 1e-12:
            tangent_mid = chord
        normal_change = max(
            _angle_between(tangent0, tangent_mid),
            _angle_between(tangent_mid, tangent1),
        )
        u0 = (segment_index + t0) / segment_count
        u1 = (segment_index + t1) / segment_count
        widths = (width_at(u0), width_at(u1))
        width_error = max(
            abs(
                width_at(u0 + fraction * (u1 - u0))
                - (widths[0] + fraction * (widths[1] - widths[0]))
            )
            for fraction in (0.25, 0.5, 0.75)
        )
        acceptable = (
            chord_error <= config.max_centerline_error
            and normal_change <= config.max_normal_angle_degrees
            and width_error <= config.max_width_error
        )
        if acceptable:
            return [(t0, p0), (t1, p1)]
        if depth >= config.max_subdivision_depth:
            raise SubdivisionLimitError("adaptive outline subdivision exceeded its depth limit")
        middle = (t0 + t1) / 2
        left = subdivide(t0, middle, depth + 1)
        right = subdivide(middle, t1, depth + 1)
        return left[:-1] + right

    return subdivide(0.0, 1.0, 0)


def _profile_points(
    segments: Sequence[Segment], width_at: Callable[[float], float], config: OutlineConfig
) -> tuple[list[Point2D], list[float]]:
    sampled: list[Point2D] = []
    widths: list[float] = []
    count = len(segments)
    for index, segment in enumerate(segments):
        samples = _flatten_segment(segment, index, count, width_at, config)
        for sample_index, (t, point) in enumerate(samples):
            if index and sample_index == 0:
                continue
            u = (index + t) / count
            current_width = float(width_at(u))
            if not isfinite(current_width) or current_width <= 0:
                raise InvalidWidthError("outline widths must be finite and positive")
            sampled.append(point)
            widths.append(current_width)
    return sampled, widths


def _normals(points: list[Point2D], closed: bool) -> list[Point2D]:
    result = []
    count = len(points)
    for index, point in enumerate(points):
        if closed:
            previous = points[(index - 1) % count]
            following = points[(index + 1) % count]
        else:
            previous = points[max(0, index - 1)]
            following = points[min(count - 1, index + 1)]
        tangent = (following[0] - previous[0], following[1] - previous[1])
        if hypot(*tangent) <= 1e-12:
            following = points[min(index + 1, count - 1)]
            tangent = (following[0] - point[0], following[1] - point[1])
        tx, ty = _unit(tangent)
        result.append((-ty, tx))
    return result


def _offset(points: list[Point2D], widths: list[float], closed: bool, side: float) -> list[Point2D]:
    normals = _normals(points, closed)
    offsets = []
    count = len(points)
    for index, (point, normal) in enumerate(zip(points, normals, strict=True)):
        radius = widths[index] / 2
        if closed or 0 < index < count - 1:
            before = normals[(index - 1) % count]
            after = normals[(index + 1) % count]
            bisector = (before[0] + after[0], before[1] + after[1])
            if hypot(*bisector) > 1e-12:
                bisector = _unit(bisector)
                denominator = bisector[0] * normal[0] + bisector[1] * normal[1]
                scale = min(widths[index] / 2 / max(denominator, 0.25), widths[index] * 2)
                normal = (bisector[0] * scale / radius, bisector[1] * scale / radius)
        offsets.append((point[0] + side * radius * normal[0], point[1] + side * radius * normal[1]))
    return offsets


def _arc_points(
    center: Point2D, radius: float, start_angle: float, sweep: float, tolerance: float
) -> list[Point2D]:
    if radius <= 0:
        return [center]
    ratio = max(-1.0, min(1.0, 1 - tolerance / radius))
    max_angle = 2 * acos(ratio)
    steps = max(2, ceil(abs(sweep) / max(max_angle, 1e-6)))
    if steps % 2:
        steps += 1
    return [
        (
            center[0] + radius * cos(start_angle + sweep * index / steps),
            center[1] + radius * sin(start_angle + sweep * index / steps),
        )
        for index in range(steps + 1)
    ]


def signed_area(points: Sequence[Point2D]) -> float:
    """Return signed polygon area; the repeated closing point is optional."""
    if len(points) < 3:
        return 0.0
    return (
        sum(
            first[0] * second[1] - second[0] * first[1]
            for first, second in zip(points, (*points[1:], points[0]), strict=False)
        )
        / 2
    )


def winding(points: Sequence[Point2D]) -> Literal["ccw", "cw", "degenerate"]:
    """Return contour winding from signed area."""
    area = signed_area(points)
    if area > 0:
        return "ccw"
    if area < 0:
        return "cw"
    return "degenerate"


def _close(points: list[Point2D]) -> Contour:
    if not points:
        return ()
    if points[-1] != points[0]:
        points.append(points[0])
    if not all(isfinite(value) for point in points for value in point):
        raise OutlineError("outline produced non-finite coordinates")
    return tuple(points)


def _expand_subpath(
    subpath: Subpath,
    width_at: Callable[[float], float],
    config: OutlineConfig,
) -> tuple[Contour, ...]:
    segments = subpath.outlining_segments()
    points, widths = _profile_points(segments, width_at, config)
    if len(points) < 2 or any(
        hypot(b[0] - a[0], b[1] - a[1]) <= 1e-12 for a, b in zip(points, points[1:], strict=False)
    ):
        raise DegeneratePathError("outline path contains a zero-length segment")
    if subpath.closed and points[-1] == points[0]:
        points.pop()
        widths.pop()
    left = _offset(points, widths, subpath.closed, 1.0)
    right = _offset(points, widths, subpath.closed, -1.0)
    if subpath.closed:
        left_contour = list(left)
        right_contour = list(right)
        if signed_area(left_contour) * signed_area(right_contour) > 0:
            right_contour.reverse()
        return (_close(left_contour), _close(right_contour))
    if config.cap == "round":
        start_tangent = _unit((points[1][0] - points[0][0], points[1][1] - points[0][1]))
        end_tangent = _unit((points[-1][0] - points[-2][0], points[-1][1] - points[-2][1]))
        end_angle = atan2(end_tangent[1], end_tangent[0])
        start_angle = atan2(start_tangent[1], start_tangent[0])
        end_cap = _arc_points(
            points[-1], widths[-1] / 2, end_angle + pi / 2, -pi, config.max_centerline_error
        )
        start_cap = _arc_points(
            points[0], widths[0] / 2, start_angle - pi / 2, -pi, config.max_centerline_error
        )
        contour = left + end_cap[1:] + list(reversed(right))[1:] + start_cap[1:]
    else:
        start_tangent = _unit((points[1][0] - points[0][0], points[1][1] - points[0][1]))
        end_tangent = _unit((points[-1][0] - points[-2][0], points[-1][1] - points[-2][1]))
        start_extension, end_extension = widths[0] / 2, widths[-1] / 2
        left[0] = _shift(left[0], start_tangent, -start_extension)
        right[0] = _shift(right[0], start_tangent, -start_extension)
        left[-1] = _shift(left[-1], end_tangent, end_extension)
        right[-1] = _shift(right[-1], end_tangent, end_extension)
        contour = left + list(reversed(right))
    return (_close(contour),)


def _result(contours: Sequence[Contour]) -> OutlineResult:
    nonempty = tuple(contour for contour in contours if contour)
    if not nonempty:
        return OutlineResult((), None)
    points = [point for contour in nonempty for point in contour]
    return OutlineResult(
        nonempty,
        (
            min(point[0] for point in points),
            min(point[1] for point in points),
            max(point[0] for point in points),
            max(point[1] for point in points),
        ),
    )


def outline(
    path: Path2D | CubicPath,
    width: WidthProfile,
    *,
    config: OutlineConfig = DEFAULT_OUTLINE_CONFIG,
) -> OutlineResult:
    """Expand centerlines into closed contours.

    Width is the full stroke diameter. For compatibility with the extracted
    InkGrammar algorithm, normalized width progress is based on segment index
    plus local segment parameter, not physical arc length, and restarts for
    each independent subpath.
    """
    if isinstance(path, CubicPath):
        path = path_from_cubic_path(path)
    if not isinstance(path, Path2D):
        raise TypeError("path must be Path2D or planarcurve.CubicPath")
    width_at = _width_function(width)
    contours = [
        contour
        for subpath in path.subpaths
        for contour in _expand_subpath(subpath, width_at, config)
    ]
    return _result(contours)


def outline_disc(
    center: Point2D,
    diameter: float,
    *,
    config: OutlineConfig = DEFAULT_OUTLINE_CONFIG,
) -> OutlineResult:
    """Create a deterministic circular contour for a point stroke."""
    width_at = _width_function(diameter)
    diameter_value = width_at(0.5)
    radius = diameter_value / 2
    max_angle = 2 * acos(max(-1.0, 1 - config.max_centerline_error / radius))
    steps = max(8, ceil(2 * pi / max(max_angle, 1e-6)))
    steps = ceil(steps / 4) * 4
    contour = _close(
        [
            (
                center[0] + radius * cos(2 * pi * index / steps),
                center[1] + radius * sin(2 * pi * index / steps),
            )
            for index in range(steps)
        ]
    )
    return _result((contour,))


# Migration-friendly alias for InkGrammar terminology.
expand_tap = outline_disc

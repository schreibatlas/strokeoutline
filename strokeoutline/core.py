from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from math import acos, atan2, ceil, cos, degrees, hypot, isclose, isfinite, pi, sin, ulp
from numbers import Real
from typing import Literal, TypeAlias

from planarcurve import CubicPath, Point2D, QuadraticBezier

from ._validation import normalize_point
from .model import Line, Path2D, Segment, Subpath, path_from_cubic_path

WidthProfile: TypeAlias = Real | Iterable[tuple[Real, Real]] | Callable[[float], Real]
Contour: TypeAlias = tuple[Point2D, ...]
CapStyle: TypeAlias = Literal["round", "square", "butt"]
JoinStyle: TypeAlias = Literal["legacy", "miter", "bevel", "round"]
WidthParameterization: TypeAlias = Literal["segment", "arclength"]


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
    """Controls adaptive sampling, caps, joins, and width progress.

    Parameters
    ----------
    max_centerline_error : float
        Maximum centerline deviation from a straight chord, in input coordinate
        units. Smaller values generally produce more samples.
    max_width_error : float
        Maximum width-profile deviation from linear interpolation, in width
        units. Smaller values sample changing widths more closely.
    max_normal_angle_degrees : float
        Maximum tangent direction change over a sampling interval, in degrees.
        The value must be positive and less than 180.
    cap : CapStyle
        Open-path cap: ``"round"``, ``"square"``, or ``"butt"``. Ignored for
        closed centerlines.
    join : JoinStyle
        Join construction: compatibility-preserving ``"legacy"``, or opt-in
        ``"miter"``, ``"bevel"``, or ``"round"``.
    miter_limit : float
        Maximum miter length divided by half-width. An over-limit miter falls
        back to bevel geometry.
    width_parameterization : WidthParameterization
        ``"segment"`` assigns equal normalized progress to each segment.
        ``"arclength"`` uses normalized physical path length. Progress resets
        for every independent subpath.
    max_subdivision_depth : int
        Maximum adaptive subdivision depth for each interval. The implementation
        uses an explicit stack. Failure to meet tolerances or floating-point
        no-progress raises ``SubdivisionLimitError``.

    Notes
    -----
    The defaults preserve the historical segment-index width progression,
    round caps, and sampled ``"legacy"`` join. Decreasing tolerances generally
    increases contour vertices and work.
    """

    max_centerline_error: float = 0.25
    max_width_error: float = 0.25
    max_normal_angle_degrees: float = 3.0
    cap: CapStyle = "round"
    join: JoinStyle = "legacy"
    miter_limit: float = 4.0
    width_parameterization: WidthParameterization = "segment"
    max_subdivision_depth: int = 18

    def __post_init__(self) -> None:
        tolerances = (
            self.max_centerline_error,
            self.max_width_error,
            self.max_normal_angle_degrees,
        )
        if any(
            isinstance(value, bool) or not isfinite(value) or value <= 0 for value in tolerances
        ):
            raise ValueError("outline tolerances must be positive and finite")
        if self.max_normal_angle_degrees >= 180:
            raise ValueError("normal angle tolerance must be less than 180 degrees")
        if self.cap not in {"round", "square", "butt"}:
            raise ValueError("cap must be 'round', 'square', or 'butt'")
        if self.join not in {"legacy", "miter", "bevel", "round"}:
            raise ValueError("join must be 'legacy', 'miter', 'bevel', or 'round'")
        if self.width_parameterization not in {"segment", "arclength"}:
            raise ValueError("width_parameterization must be 'segment' or 'arclength'")
        if (
            isinstance(self.miter_limit, bool)
            or not isinstance(self.miter_limit, Real)
            or not isfinite(self.miter_limit)
            or self.miter_limit <= 0
        ):
            raise ValueError("miter limit must be positive and finite")
        if (
            isinstance(self.max_subdivision_depth, bool)
            or not isinstance(self.max_subdivision_depth, int)
            or self.max_subdivision_depth < 1
        ):
            raise ValueError("maximum subdivision depth must be a positive integer")


DEFAULT_OUTLINE_CONFIG = OutlineConfig()


@dataclass(frozen=True)
class OutlineResult:
    """Immutable result of a centerline expansion.

    Contours are normalized to tuples of finite points. Every contour must be
    explicitly closed, and aggregate bounds must match the contour coordinates.
    """

    contours: tuple[Contour, ...]
    bounds: tuple[float, float, float, float] | None

    def __post_init__(self) -> None:
        try:
            contours = tuple(
                tuple(normalize_point(point, name="contour point") for point in contour)
                for contour in self.contours
            )
        except TypeError as exc:
            raise ValueError("contours must be an iterable of point iterables") from exc
        if any(not contour or contour[0] != contour[-1] for contour in contours):
            raise ValueError("each contour must be non-empty and explicitly closed")

        if not contours:
            if self.bounds is not None:
                raise ValueError("bounds must be None when contours are empty")
            object.__setattr__(self, "contours", ())
            return

        points = tuple(point for contour in contours for point in contour)
        expected_bounds = (
            min(point[0] for point in points),
            min(point[1] for point in points),
            max(point[0] for point in points),
            max(point[1] for point in points),
        )
        if isinstance(self.bounds, (str, bytes)) or self.bounds is None:
            raise ValueError("bounds must contain four finite values for non-empty contours")
        try:
            bounds = tuple(float(value) for value in self.bounds)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("bounds must contain four finite values") from exc
        if len(bounds) != 4 or not all(isfinite(value) for value in bounds):
            raise ValueError("bounds must contain four finite values")
        if bounds != expected_bounds:
            raise ValueError("bounds must match the contour coordinates")
        object.__setattr__(self, "contours", contours)
        object.__setattr__(self, "bounds", bounds)


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


@dataclass(frozen=True)
class _WidthEvaluator:
    value_at: Callable[[float], float]
    breakpoints: tuple[float, ...] = ()

    def __call__(self, u: float) -> float:
        return self.value_at(u)


def _width_function(profile: WidthProfile) -> _WidthEvaluator:
    breakpoints: tuple[float, ...] = ()
    memoize = callable(profile)

    if memoize:
        raw = profile
    elif isinstance(profile, Real) and not isinstance(profile, bool):
        try:
            constant = float(profile)
        except (TypeError, ValueError, OverflowError) as exc:
            raise InvalidWidthError("outline widths must be finite and positive") from exc

        def raw(_u: float) -> float:
            return constant

    else:
        try:
            raw_knots = tuple(profile)
            if any(
                isinstance(position, bool) or isinstance(width, bool)
                for position, width in raw_knots
            ):
                raise InvalidWidthError("width profile knots must be numeric, not boolean")
            knots = tuple((float(position), float(width)) for position, width in raw_knots)
        except (TypeError, ValueError, OverflowError) as exc:
            if isinstance(exc, InvalidWidthError):
                raise
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
        breakpoints = tuple(position for position, _width in knots[1:-1])

        def raw(u: float) -> float:
            for (u0, w0), (u1, w1) in zip(knots, knots[1:], strict=False):
                if u <= u1:
                    return w0 + (w1 - w0) * (u - u0) / (u1 - u0)
            return knots[-1][1]

    cache: dict[float, float] = {}

    def width_at(u: float) -> float:
        u = float(u)
        if memoize and u in cache:
            return cache[u]
        raw_value = raw(u)
        if isinstance(raw_value, bool):
            raise InvalidWidthError("outline widths must be finite and positive")
        try:
            value = float(raw_value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise InvalidWidthError("width callable must return numeric values") from exc
        if not isfinite(value) or value <= 0:
            raise InvalidWidthError("outline widths must be finite and positive")
        if memoize:
            cache[u] = value
        return value

    return _WidthEvaluator(width_at, breakpoints)


class _SegmentLength:
    def __init__(self, segment: Segment) -> None:
        self.segment = segment
        self.cache = {0.0: 0.0}

    def at(self, t: float) -> float:
        if t in self.cache:
            return self.cache[t]
        if isinstance(self.segment, Line):
            length = (
                hypot(
                    self.segment.p1[0] - self.segment.p0[0],
                    self.segment.p1[1] - self.segment.p0[1],
                )
                * t
            )
            self.cache[t] = length
            return length
        if t == 0:
            return 0.0

        def speed(parameter: float) -> float:
            return hypot(*_tangent(self.segment, parameter))

        start, end = 0.0, t
        middle = (start + end) / 2
        start_speed, middle_speed, end_speed = speed(start), speed(middle), speed(end)
        whole = (end - start) * (start_speed + 4 * middle_speed + end_speed) / 6
        tolerance = max(abs(whole) * 1e-10, ulp(abs(whole)) * 8)
        stack = [(start, end, start_speed, middle_speed, end_speed, whole, tolerance, 0)]
        length = 0.0
        while stack:
            a, b, fa, fm, fb, estimate, allowed_error, depth = stack.pop()
            midpoint = (a + b) / 2
            left_midpoint = (a + midpoint) / 2
            right_midpoint = (midpoint + b) / 2
            flm, frm = speed(left_midpoint), speed(right_midpoint)
            left = (midpoint - a) * (fa + 4 * flm + fm) / 6
            right = (b - midpoint) * (fm + 4 * frm + fb) / 6
            error = left + right - estimate
            if abs(error) <= 15 * allowed_error or depth >= 20:
                length += left + right + error / 15
            else:
                half_error = allowed_error / 2
                stack.append((midpoint, b, fm, frm, fb, right, half_error, depth + 1))
                stack.append((a, midpoint, fa, flm, fm, left, half_error, depth + 1))
        self.cache[t] = length
        return length


class _PathProgress:
    def __init__(
        self,
        segments: Sequence[Segment],
        breakpoints: tuple[float, ...],
        mode: WidthParameterization,
    ) -> None:
        self.count = len(segments)
        self.mode = mode
        self.length_maps = (
            [_SegmentLength(segment) for segment in segments] if mode == "arclength" else []
        )
        self.lengths = [length_map.at(1.0) for length_map in self.length_maps]
        self.total_length = sum(self.lengths)
        self.cumulative = [0.0]
        for length in self.lengths:
            self.cumulative.append(self.cumulative[-1] + length)
        self.knots: list[tuple[tuple[float, float], ...]] = []
        for index in range(self.count):
            segment_knots = []
            for progress in breakpoints:
                parameter = self._parameter_at(index, progress)
                if parameter is not None:
                    segment_knots.append((parameter, progress))
            self.knots.append(tuple(segment_knots))

    def _parameter_at(self, index: int, progress: float) -> float | None:
        if self.mode == "segment" or self.total_length == 0:
            start = index / self.count
            end = (index + 1) / self.count
            if start <= progress <= end:
                return min(1.0, max(0.0, progress * self.count - index))
            return None

        target = progress * self.total_length - self.cumulative[index]
        segment_length = self.lengths[index]
        if isclose(target, 0.0, rel_tol=1e-14, abs_tol=0.0):
            return 0.0
        if isclose(target, segment_length, rel_tol=1e-14, abs_tol=0.0):
            return 1.0
        if not 0 < target < segment_length:
            return None
        low, high = 0.0, 1.0
        length_map = self.length_maps[index]
        for _ in range(64):
            middle = (low + high) / 2
            if not low < middle < high:
                break
            if length_map.at(middle) < target:
                low = middle
            else:
                high = middle
        low_error = abs(length_map.at(low) - target)
        high_error = abs(length_map.at(high) - target)
        return low if low_error <= high_error else high

    def value(self, index: int, t: float) -> float:
        for parameter, progress in self.knots[index]:
            if t == parameter:
                return progress
        if self.mode == "segment" or self.total_length == 0:
            return (index + t) / self.count
        distance = self.cumulative[index] + self.length_maps[index].at(t)
        return min(1.0, max(0.0, distance / self.total_length))


def _unit(vector: Point2D) -> Point2D:
    length = hypot(*vector)
    if length == 0:
        raise DegeneratePathError("outline contains a zero-length tangent")
    return (vector[0] / length, vector[1] / length)


def _shift(point: Point2D, direction: Point2D, distance: float) -> Point2D:
    return (point[0] + direction[0] * distance, point[1] + direction[1] * distance)


def _distance_to_chord(point: Point2D, start: Point2D, end: Point2D) -> float:
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = hypot(dx, dy)
    if length == 0:
        return hypot(point[0] - start[0], point[1] - start[1])
    direction = (dx / length, dy / length)
    offset = (point[0] - start[0], point[1] - start[1])
    projection = (offset[0] / length) * direction[0] + (offset[1] / length) * direction[1]
    u = max(0.0, min(1.0, projection))
    nearest = (start[0] + u * dx, start[1] + u * dy)
    return hypot(point[0] - nearest[0], point[1] - nearest[1])


def _angle_between(left: Point2D, right: Point2D) -> float:
    a, b = _unit(left), _unit(right)
    return degrees(acos(max(-1.0, min(1.0, a[0] * b[0] + a[1] * b[1]))))


def _flatten_segment(
    segment: Segment,
    segment_index: int,
    progress: _PathProgress,
    width_at: _WidthEvaluator,
    config: OutlineConfig,
) -> list[tuple[float, Point2D]]:
    cuts = [0.0, 1.0]
    cuts.extend(
        parameter for parameter, _value in progress.knots[segment_index] if 0 < parameter < 1
    )
    cuts.sort()
    samples: list[tuple[float, Point2D]] = []

    for interval_start, interval_end in zip(cuts, cuts[1:], strict=False):
        stack = [(interval_start, interval_end, 0)]
        while stack:
            t0, t1, depth = stack.pop()
            p0, p1 = _point_on(segment, t0), _point_on(segment, t1)
            span = t1 - t0
            probes = [_point_on(segment, t0 + span * fraction) for fraction in (0.25, 0.5, 0.75)]
            chord_error = max(_distance_to_chord(point, p0, p1) for point in probes)
            tangent0 = _tangent(segment, t0)
            tangent1 = _tangent(segment, t1)
            tangent_mid = _tangent(segment, (t0 + t1) / 2)
            chord = (p1[0] - p0[0], p1[1] - p0[1])
            if hypot(*tangent0) == 0:
                tangent0 = chord
            if hypot(*tangent1) == 0:
                tangent1 = chord
            if hypot(*tangent_mid) == 0:
                tangent_mid = chord
            normal_change = max(
                _angle_between(tangent0, tangent_mid),
                _angle_between(tangent_mid, tangent1),
            )
            u0, u1 = progress.value(segment_index, t0), progress.value(segment_index, t1)
            widths = (width_at(u0), width_at(u1))
            width_error = max(
                abs(
                    width_at(progress.value(segment_index, t0 + span * fraction))
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
                if not samples:
                    samples.append((t0, p0))
                samples.append((t1, p1))
                continue
            if depth >= config.max_subdivision_depth:
                raise SubdivisionLimitError("adaptive outline subdivision exceeded its depth limit")
            middle = (t0 + t1) / 2
            if not t0 < middle < t1:
                raise SubdivisionLimitError(
                    "adaptive outline subdivision made no floating-point progress"
                )
            stack.append((middle, t1, depth + 1))
            stack.append((t0, middle, depth + 1))

    return samples


def _profile_points(
    segments: Sequence[Segment], width_at: _WidthEvaluator, config: OutlineConfig
) -> tuple[list[Point2D], list[float]]:
    sampled: list[Point2D] = []
    widths: list[float] = []
    progress = _PathProgress(segments, width_at.breakpoints, config.width_parameterization)
    for index, segment in enumerate(segments):
        samples = _flatten_segment(segment, index, progress, width_at, config)
        for sample_index, (t, point) in enumerate(samples):
            if index and sample_index == 0:
                continue
            sampled.append(point)
            widths.append(width_at(progress.value(index, t)))
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
        if hypot(*tangent) == 0:
            following = points[min(index + 1, count - 1)]
            tangent = (following[0] - point[0], following[1] - point[1])
        tx, ty = _unit(tangent)
        result.append((-ty, tx))
    return result


def _offset_legacy(
    points: list[Point2D], widths: list[float], closed: bool, side: float
) -> list[Point2D]:
    normals = _normals(points, closed)
    offsets = []
    count = len(points)
    for index, (point, normal) in enumerate(zip(points, normals, strict=True)):
        radius = widths[index] / 2
        if closed or 0 < index < count - 1:
            before = normals[(index - 1) % count]
            after = normals[(index + 1) % count]
            bisector = (before[0] + after[0], before[1] + after[1])
            if hypot(*bisector) > 0:
                bisector = _unit(bisector)
                denominator = bisector[0] * normal[0] + bisector[1] * normal[1]
                scale = min(widths[index] / 2 / max(denominator, 0.25), widths[index] * 2)
                normal = (bisector[0] * scale / radius, bisector[1] * scale / radius)
        offsets.append((point[0] + side * radius * normal[0], point[1] + side * radius * normal[1]))
    return offsets


def _offset(
    points: list[Point2D],
    widths: list[float],
    closed: bool,
    side: float,
    *,
    join: JoinStyle,
    miter_limit: float,
    tolerance: float,
) -> list[Point2D]:
    if join == "legacy":
        return _offset_legacy(points, widths, closed, side)

    normals = _normals(points, closed)
    result: list[Point2D] = []
    count = len(points)
    for index, (point, normal) in enumerate(zip(points, normals, strict=True)):
        radius = widths[index] / 2
        if not closed and index in {0, count - 1}:
            result.append(_shift(point, normal, side * radius))
            continue

        previous = points[(index - 1) % count]
        following = points[(index + 1) % count]
        incoming = _unit((point[0] - previous[0], point[1] - previous[1]))
        outgoing = _unit((following[0] - point[0], following[1] - point[1]))
        cross = incoming[0] * outgoing[1] - incoming[1] * outgoing[0]
        dot = incoming[0] * outgoing[0] + incoming[1] * outgoing[1]
        normal_in = (-incoming[1] * side, incoming[0] * side)
        normal_out = (-outgoing[1] * side, outgoing[0] * side)
        if cross == 0 and dot > 0:
            result.append(_shift(point, normal_out, radius))
            continue

        bisector = (normal_in[0] + normal_out[0], normal_in[1] + normal_out[1])
        bisector_length = hypot(*bisector)
        if bisector_length == 0:
            result.extend((_shift(point, normal_in, radius), _shift(point, normal_out, radius)))
            continue
        miter_direction = (bisector[0] / bisector_length, bisector[1] / bisector_length)
        denominator = miter_direction[0] * normal_out[0] + miter_direction[1] * normal_out[1]
        miter_valid = denominator > 0 and 1 / denominator <= miter_limit
        outer = side * cross < 0

        if join == "round" and outer:
            result.extend(
                _arc_points(
                    point,
                    radius,
                    atan2(normal_in[1], normal_in[0]),
                    atan2(cross, dot),
                    tolerance,
                )
            )
        elif (outer and join == "bevel") or not miter_valid:
            result.extend((_shift(point, normal_in, radius), _shift(point, normal_out, radius)))
        else:
            result.append(_shift(point, miter_direction, radius / denominator))
    return result


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


def _endpoint_tangent(segment: Segment, t: float, fallback: Point2D) -> Point2D:
    tangent = _tangent(segment, t)
    if hypot(*tangent) == 0:
        tangent = fallback
    return _unit(tangent)


def _expand_subpath(
    subpath: Subpath,
    width_at: _WidthEvaluator,
    config: OutlineConfig,
) -> tuple[Contour, ...]:
    segments = subpath.outlining_segments()
    points, widths = _profile_points(segments, width_at, config)
    if len(points) < 2 or any(
        hypot(b[0] - a[0], b[1] - a[1]) == 0 for a, b in zip(points, points[1:], strict=False)
    ):
        raise DegeneratePathError("outline path contains a zero-length segment")
    if subpath.closed and points[-1] == points[0]:
        points.pop()
        widths.pop()
    left = _offset(
        points,
        widths,
        subpath.closed,
        1.0,
        join=config.join,
        miter_limit=config.miter_limit,
        tolerance=config.max_centerline_error,
    )
    right = _offset(
        points,
        widths,
        subpath.closed,
        -1.0,
        join=config.join,
        miter_limit=config.miter_limit,
        tolerance=config.max_centerline_error,
    )
    if subpath.closed:
        left_contour = list(left)
        right_contour = list(right)
        if signed_area(left_contour) * signed_area(right_contour) > 0:
            right_contour.reverse()
        return (_close(left_contour), _close(right_contour))
    if config.cap == "round":
        start_tangent = _endpoint_tangent(
            segments[0], 0.0, (points[1][0] - points[0][0], points[1][1] - points[0][1])
        )
        end_tangent = _endpoint_tangent(
            segments[-1], 1.0, (points[-1][0] - points[-2][0], points[-1][1] - points[-2][1])
        )
        end_angle = atan2(end_tangent[1], end_tangent[0])
        start_angle = atan2(start_tangent[1], start_tangent[0])
        end_cap = _arc_points(
            points[-1], widths[-1] / 2, end_angle + pi / 2, -pi, config.max_centerline_error
        )
        start_cap = _arc_points(
            points[0], widths[0] / 2, start_angle - pi / 2, -pi, config.max_centerline_error
        )
        contour = left + end_cap[1:] + list(reversed(right))[1:] + start_cap[1:]
    elif config.cap == "square":
        start_tangent = _endpoint_tangent(
            segments[0], 0.0, (points[1][0] - points[0][0], points[1][1] - points[0][1])
        )
        end_tangent = _endpoint_tangent(
            segments[-1], 1.0, (points[-1][0] - points[-2][0], points[-1][1] - points[-2][1])
        )
        start_extension, end_extension = widths[0] / 2, widths[-1] / 2
        left[0] = _shift(left[0], start_tangent, -start_extension)
        right[0] = _shift(right[0], start_tangent, -start_extension)
        left[-1] = _shift(left[-1], end_tangent, end_extension)
        right[-1] = _shift(right[-1], end_tangent, end_extension)
        contour = left + list(reversed(right))
    else:
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


def combine_outlines(outlines: Iterable[OutlineResult]) -> OutlineResult:
    """Aggregate outline contours in order without performing a Boolean union."""
    contours = tuple(contour for result in outlines for contour in result.contours)
    return _result(contours)


def outline(
    path: Path2D | CubicPath,
    width: WidthProfile,
    *,
    config: OutlineConfig = DEFAULT_OUTLINE_CONFIG,
) -> OutlineResult:
    """Expand centerlines into deterministic sampled closed contours.

    Parameters
    ----------
    path : Path2D or planarcurve.CubicPath
        One or more centerline subpaths, or a cubic path accepted directly.
    width : WidthProfile
        A positive full diameter, a piecewise-linear knot sequence spanning
        normalized progress from 0 to 1, or a callable from progress to width.
    config : OutlineConfig, optional
        Adaptive sampling tolerances, caps, joins, and width progression.

    Returns
    -------
    OutlineResult
        Closed contour tuples and aggregate bounds in
        ``(min_x, min_y, max_x, max_y)`` order.

    Raises
    ------
    InvalidWidthError
        If the width profile or an evaluated width is invalid.
    DegeneratePathError
        If the centerline contains a zero-length segment or tangent.
    SubdivisionLimitError
        If adaptive sampling cannot meet the configured tolerances within the
        subdivision depth limit.
    TypeError
        If ``path`` is not a ``Path2D`` or ``planarcurve.CubicPath``.

    Notes
    -----
    Width is the full stroke diameter, not the radius. For
    ``width_parameterization="segment"``, normalized progress is
    ``u = (segment_index + local_segment_parameter) / segment_count``.
    ``width_parameterization="arclength"`` instead uses normalized cumulative
    physical path length. Progress restarts from zero for every independent
    ``Subpath``. The configured cap applies only to open paths; joins are
    selected by ``config.join``.
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
    diameter: WidthProfile,
    *,
    config: OutlineConfig = DEFAULT_OUTLINE_CONFIG,
) -> OutlineResult:
    """Create a sampled circular contour from a center and width profile.

    Parameters
    ----------
    center : Point2D
        Center of the disc in the input coordinate system.
    diameter : WidthProfile
        Positive full diameter, width knots, or callable width profile.
    config : OutlineConfig, optional
        Sampling tolerance used to choose the circular contour resolution.

    Returns
    -------
    OutlineResult
        One explicitly closed circular contour and its bounds.

    Raises
    ------
    InvalidWidthError
        If the width profile or its evaluated value is invalid.

    Notes
    -----
    Since a point has no path progression, a width profile is evaluated at
    normalized progress ``u == 0.5``.
    """
    center = normalize_point(center, name="center")
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

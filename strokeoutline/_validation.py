from __future__ import annotations

from collections.abc import Iterable
from math import isfinite

from planarcurve import Point2D


def normalize_point(value: Iterable[float], *, name: str) -> Point2D:
    """Convert a finite two-coordinate iterable to an immutable point."""
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must have exactly two numeric coordinates")
    try:
        coordinates = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must have exactly two numeric coordinates") from exc
    if len(coordinates) != 2:
        raise ValueError(f"{name} must have exactly two coordinates")
    if any(isinstance(component, bool) for component in coordinates):
        raise ValueError(f"{name} coordinates must be numeric and finite")
    try:
        point = (float(coordinates[0]), float(coordinates[1]))
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} coordinates must be numeric and finite") from exc
    if not all(isfinite(component) for component in point):
        raise ValueError(f"{name} must contain finite coordinates")
    return point

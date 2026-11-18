"""Optional Pillow-backed rasterization of StrokeOutline vector contours."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil, floor, isfinite
from numbers import Integral

import numpy as np
from numpy.typing import NDArray
from planarcurve import Affine2D, CubicPath

from .core import (
    DEFAULT_OUTLINE_CONFIG,
    OutlineConfig,
    OutlineResult,
    WidthProfile,
    combine_outlines,
    outline,
    signed_area,
)
from .model import Path2D


@dataclass(frozen=True)
class RasterFrame:
    """Pixel dimensions and explicit model-to-pixel coordinate transform.

    Pixel bounds returned by rasterization are half-open ``(left, top, right,
    bottom)`` coordinates. No axis inversion is applied implicitly.
    """

    width: int
    height: int
    model_to_pixel: Affine2D

    def __post_init__(self) -> None:
        if isinstance(self.width, bool) or not isinstance(self.width, Integral) or self.width <= 0:
            raise ValueError("frame width must be a positive integer")
        if (
            isinstance(self.height, bool)
            or not isinstance(self.height, Integral)
            or self.height <= 0
        ):
            raise ValueError("frame height must be a positive integer")
        if not isinstance(self.model_to_pixel, Affine2D):
            raise TypeError("model_to_pixel must be an Affine2D")
        if not all(isfinite(value) for value in self.model_to_pixel.as_tuple()):
            raise ValueError("model_to_pixel transform values must be finite")
        object.__setattr__(self, "width", int(self.width))
        object.__setattr__(self, "height", int(self.height))


@dataclass(frozen=True)
class RasterConfig:
    """Raster precision controls.

    ``tile_size`` is reserved for tiled raster backends. The current backend
    limits work to the transformed outline bounds and rasterizes that crop.
    """

    supersampling: int = 4
    tile_size: int | None = None

    def __post_init__(self) -> None:
        if (
            isinstance(self.supersampling, bool)
            or not isinstance(self.supersampling, Integral)
            or self.supersampling < 1
        ):
            raise ValueError("supersampling must be a positive integer")
        if self.tile_size is not None and (
            isinstance(self.tile_size, bool)
            or not isinstance(self.tile_size, Integral)
            or self.tile_size < 1
        ):
            raise ValueError("tile_size must be a positive integer or None")
        object.__setattr__(self, "supersampling", int(self.supersampling))
        if self.tile_size is not None:
            object.__setattr__(self, "tile_size", int(self.tile_size))


@dataclass(frozen=True)
class RasterizedOutline:
    """A read-only grayscale coverage mask and its half-open pixel bounds."""

    coverage: NDArray[np.float32]
    bounds_px: tuple[int, int, int, int] | None

    def __post_init__(self) -> None:
        try:
            coverage = np.asarray(self.coverage, dtype=np.float32)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("coverage must be a two-dimensional numeric array") from exc
        if coverage.ndim != 2:
            raise ValueError("coverage must be a two-dimensional array with shape (height, width)")
        if not np.isfinite(coverage).all() or np.any((coverage < 0.0) | (coverage > 1.0)):
            raise ValueError("coverage values must be finite and in [0, 1]")
        coverage = np.array(coverage, dtype=np.float32, copy=True, order="C")
        coverage.setflags(write=False)
        object.__setattr__(self, "coverage", coverage)

        bounds = self.bounds_px
        if bounds is not None:
            if len(bounds) != 4 or any(
                isinstance(value, bool) or not isinstance(value, Integral) for value in bounds
            ):
                raise ValueError("bounds_px must contain four integer pixel coordinates")
            left, top, right, bottom = (int(value) for value in bounds)
            height, width = coverage.shape
            if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                raise ValueError("bounds_px must be a non-empty half-open box within coverage")
            object.__setattr__(self, "bounds_px", (left, top, right, bottom))


def _empty_result(frame: RasterFrame) -> RasterizedOutline:
    return RasterizedOutline(np.zeros((frame.height, frame.width), dtype=np.float32), None)


def rasterize_outline(
    outline: OutlineResult,
    frame: RasterFrame,
    *,
    supersampling: int = 4,
) -> RasterizedOutline:
    """Rasterize outline contours into deterministic anti-aliased coverage.

    Contours are rasterized with a non-zero winding rule, preserving interior
    contours such as the hole in a closed stroke. Supersampled coverage is
    downsampled with Lanczos filtering and clipped to ``[0, 1]``. The returned
    bounds enclose non-zero coverage using half-open pixel coordinates.

    Pillow is imported only when this function is called. Install the optional
    dependency with ``pip install 'strokeoutline[raster]'``.
    """
    if not isinstance(outline, OutlineResult):
        raise TypeError("outline must be an OutlineResult")
    if not isinstance(frame, RasterFrame):
        raise TypeError("frame must be a RasterFrame")
    config = RasterConfig(supersampling=supersampling)

    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise ImportError(
            "rasterize_outline requires Pillow; install strokeoutline[raster]"
        ) from exc

    if not outline.contours:
        return _empty_result(frame)

    points = np.asarray(
        [point for contour in outline.contours for point in contour], dtype=np.float64
    )
    with np.errstate(over="ignore", invalid="ignore"):
        pixel_points = frame.model_to_pixel.apply(points)
    if not np.isfinite(pixel_points).all():
        raise ValueError("transformed outline points must remain finite")

    min_x, min_y = np.min(pixel_points, axis=0)
    max_x, max_y = np.max(pixel_points, axis=0)
    if max_x < 0 or max_y < 0 or min_x >= frame.width or min_y >= frame.height:
        return _empty_result(frame)

    # Keep enough neighboring pixels for the downsampling filter while avoiding
    # allocating a supersampled image for unrelated parts of a larger page.
    padding = 3
    left = max(0, floor(min_x) - padding)
    top = max(0, floor(min_y) - padding)
    right = min(frame.width, ceil(max_x) + padding + 1)
    bottom = min(frame.height, ceil(max_y) + padding + 1)
    crop_width = right - left
    crop_height = bottom - top
    scale = config.supersampling
    high_size = (crop_width * scale, crop_height * scale)
    winding = np.zeros((high_size[1], high_size[0]), dtype=np.int32)

    for contour in outline.contours:
        area = signed_area(contour)
        orientation = 1 if area >= 0 else -1
        contour_pixels = frame.model_to_pixel.apply(np.asarray(contour, dtype=np.float64))
        polygon = [
            (int(round((x - left) * scale)), int(round((y - top) * scale)))
            for x, y in contour_pixels
        ]
        contour_mask = Image.new("1", high_size, 0)
        ImageDraw.Draw(contour_mask).polygon(polygon, fill=1)
        winding += np.asarray(contour_mask, dtype=np.int32) * orientation

    high_mask = Image.fromarray(np.where(winding != 0, 255, 0).astype(np.uint8))
    resized = high_mask.resize((crop_width, crop_height), Image.Resampling.LANCZOS)
    crop_coverage = np.asarray(resized, dtype=np.float32) / np.float32(255.0)
    np.clip(crop_coverage, 0.0, 1.0, out=crop_coverage)

    coverage = np.zeros((frame.height, frame.width), dtype=np.float32)
    coverage[top:bottom, left:right] = crop_coverage
    ys, xs = np.nonzero(coverage)
    bounds = (
        None
        if len(xs) == 0
        else (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    )
    return RasterizedOutline(coverage, bounds)


@dataclass(frozen=True)
class StrokeRender:
    """Vector outline and optional raster coverage for one stroke."""

    outline: OutlineResult
    raster: RasterizedOutline | None


@dataclass(frozen=True)
class StrokeInput:
    """Generic centerline and width input for multi-stroke rendering."""

    id: str
    path: Path2D | CubicPath
    width: WidthProfile
    outline_config: OutlineConfig | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("stroke id must be a non-empty string")
        if not isinstance(self.path, (Path2D, CubicPath)):
            raise TypeError("stroke path must be a Path2D or CubicPath")
        if self.outline_config is not None and not isinstance(self.outline_config, OutlineConfig):
            raise TypeError("outline_config must be an OutlineConfig or None")


@dataclass(frozen=True)
class RenderedStrokeLayer:
    """One identified stroke with its vector outline and optional coverage."""

    id: str
    outline: OutlineResult
    coverage: NDArray[np.float32] | None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("stroke layer id must be a non-empty string")
        if not isinstance(self.outline, OutlineResult):
            raise TypeError("outline must be an OutlineResult")
        if self.coverage is not None:
            frozen = RasterizedOutline(self.coverage, None).coverage
            object.__setattr__(self, "coverage", frozen)


@dataclass(frozen=True)
class MultiStrokeRender:
    """Per-stroke rendering and aggregate vector/raster results."""

    layers: tuple[RenderedStrokeLayer, ...]
    combined_outline: OutlineResult
    combined_coverage: NDArray[np.float32] | None

    def __post_init__(self) -> None:
        layers = tuple(self.layers)
        if not all(isinstance(layer, RenderedStrokeLayer) for layer in layers):
            raise TypeError("layers must contain RenderedStrokeLayer values")
        if not isinstance(self.combined_outline, OutlineResult):
            raise TypeError("combined_outline must be an OutlineResult")
        object.__setattr__(self, "layers", layers)
        if self.combined_coverage is not None:
            frozen = RasterizedOutline(self.combined_coverage, None).coverage
            object.__setattr__(self, "combined_coverage", frozen)


def render_stroke(
    path: Path2D | CubicPath,
    width: WidthProfile,
    *,
    outline_config: OutlineConfig = DEFAULT_OUTLINE_CONFIG,
    raster_frame: RasterFrame | None = None,
    supersampling: int = 4,
) -> StrokeRender:
    """Create one vector outline and optionally rasterize that exact result."""
    if not isinstance(outline_config, OutlineConfig):
        raise TypeError("outline_config must be an OutlineConfig")
    RasterConfig(supersampling=supersampling)
    outline_result = outline(path, width, config=outline_config)
    raster = (
        None
        if raster_frame is None
        else rasterize_outline(outline_result, raster_frame, supersampling=supersampling)
    )
    return StrokeRender(outline_result, raster)


def render_strokes(
    strokes: Sequence[StrokeInput],
    *,
    raster_frame: RasterFrame | None = None,
    supersampling: int = 4,
) -> MultiStrokeRender:
    """Render independent strokes and combine opaque raster layers by maximum."""
    strokes = tuple(strokes)
    RasterConfig(supersampling=supersampling)
    if not all(isinstance(stroke, StrokeInput) for stroke in strokes):
        raise TypeError("strokes must contain StrokeInput values")
    ids = [stroke.id for stroke in strokes]
    if len(ids) != len(set(ids)):
        raise ValueError("stroke ids must be unique")

    layers: list[RenderedStrokeLayer] = []
    for stroke in strokes:
        outline_config = stroke.outline_config or DEFAULT_OUTLINE_CONFIG
        stroke_render = render_stroke(
            stroke.path,
            stroke.width,
            outline_config=outline_config,
            raster_frame=raster_frame,
            supersampling=supersampling,
        )
        coverage = None if stroke_render.raster is None else stroke_render.raster.coverage
        layers.append(RenderedStrokeLayer(stroke.id, stroke_render.outline, coverage))

    combined_outline = combine_outlines(layer.outline for layer in layers)
    if raster_frame is None:
        combined_coverage = None
    elif layers:
        combined_coverage = np.maximum.reduce(
            [layer.coverage for layer in layers if layer.coverage is not None]
        )
    else:
        combined_coverage = np.zeros((raster_frame.height, raster_frame.width), dtype=np.float32)
    return MultiStrokeRender(tuple(layers), combined_outline, combined_coverage)

from __future__ import annotations

from strokeoutline import OutlineConfig, signed_area
from strokeoutline.svg import outline_svg_path, path_from_svg


def test_svg_line_parity_with_inkgrammar_baseline():
    result = outline_svg_path("M 0 0 L 10 0", 2.0)
    assert result.bounds == (-1.0, -1.0, 11.0, 1.0)


def test_svg_variable_width_parity_with_inkgrammar_baseline():
    result = outline_svg_path(
        "M 0 0 L 10 0",
        [(0.0, 2.0), (0.25, 3.0), (1.0, 10.0)],
        config=OutlineConfig(max_width_error=0.05),
    )
    assert result.bounds == (-1.0, -5.0, 15.0, 5.0)
    assert len(result.contours[0]) > 8


def test_svg_closed_loop_winding_parity():
    result = outline_svg_path(
        "M 0 0 C 0 100 100 100 100 0 C 100 -100 0 -100 0 0 Z",
        8.0,
    )
    assert len(result.contours) == 2
    assert signed_area(result.contours[0]) * signed_area(result.contours[1]) < 0


def test_svg_multiple_subpaths_are_preserved():
    path = path_from_svg("M 0 0 L 10 0 M 20 0 L 30 0")
    assert len(path.subpaths) == 2

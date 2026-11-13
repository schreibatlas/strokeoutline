import pytest

from strokeoutline import DegeneratePathError, Line, Path2D, outline, path_from_polyline


def test_path_from_polyline_preserves_point_order():
    points = ((0, 0), (3, 1), (4, 2))

    path = path_from_polyline(points)

    assert isinstance(path, Path2D)
    assert path.subpaths[0].segments == (
        Line((0, 0), (3, 1)),
        Line((3, 1), (4, 2)),
    )
    assert not path.subpaths[0].closed


def test_closed_polyline_adds_implicit_closing_segment():
    path = path_from_polyline(((0, 0), (3, 0), (3, 2)), closed=True)

    assert path.subpaths[0].segments == (
        Line((0, 0), (3, 0)),
        Line((3, 0), (3, 2)),
    )
    assert path.subpaths[0].outlining_segments()[-1] == Line((3, 2), (0, 0))


@pytest.mark.parametrize("points", [(), ((0, 0),)])
def test_polyline_requires_at_least_two_points(points):
    with pytest.raises(ValueError, match="at least two points"):
        path_from_polyline(points)


@pytest.mark.parametrize(
    "points",
    [
        ((0, 0), (1, float("nan"))),
        ((0, 0), (1, float("inf"))),
        ((0, 0), (1, 2, 3)),
    ],
)
def test_polyline_rejects_non_finite_or_non_2d_points(points):
    with pytest.raises(ValueError):
        path_from_polyline(points)


def test_repeated_adjacent_points_are_left_for_outline_to_reject():
    path = path_from_polyline(((0, 0), (0, 0), (1, 0)))

    with pytest.raises(DegeneratePathError):
        outline(path, 2.0)

import math

from strokeoutline import Line, OutlineConfig, Path2D, Subpath, outline


def main():
    path = Path2D((Subpath((Line((0, 0), (100, 0)),)),))
    profile = [(0.0, 2.0), (0.3, 4.0), (0.7, 16.0), (1.0, 6.0)]
    result = outline(path, profile, config=OutlineConfig(max_width_error=0.05))
    constant_width = outline(path, 2.0)

    assert len(result.contours) == 1
    assert result.bounds is not None and constant_width.bounds is not None
    assert result.bounds[3] > constant_width.bounds[3]
    assert math.isclose(result.bounds[3], 8.0)
    assert all(math.isfinite(value) for value in result.bounds)
    print("bounds:", result.bounds)


if __name__ == "__main__":
    main()

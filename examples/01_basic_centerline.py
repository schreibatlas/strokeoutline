import math

from planarcurve import CubicBezier, QuadraticBezier

from strokeoutline import Line, Path2D, Subpath, outline


def main():
    path = Path2D(
        (
            Subpath(
                (
                    Line((0, 0), (25, 0)),
                    QuadraticBezier((25, 0), (40, 25), (55, 0)),
                    CubicBezier((55, 0), (65, -20), (80, 20), (90, 0)),
                )
            ),
        )
    )
    result = outline(path, width=6.0)

    assert len(result.contours) == 1
    assert result.contours[0][0] == result.contours[0][-1]
    assert result.bounds is not None
    assert all(math.isfinite(value) for value in result.bounds)
    print("contours:", len(result.contours))
    print("bounds:", result.bounds)


if __name__ == "__main__":
    main()

from planarcurve import CubicPath, CubicSegment

from strokeoutline import outline, path_from_cubic_path


def main():
    centerline = CubicPath(
        (0, 0),
        (
            CubicSegment((15, 30), (35, 30), (50, 0)),
            CubicSegment((65, -30), (85, -30), (100, 0)),
        ),
    )

    def width(u):
        return 3.0 + 7.0 * u

    direct_result = outline(centerline, width)
    adapted_result = outline(path_from_cubic_path(centerline), width)

    assert direct_result == adapted_result
    assert direct_result.bounds is not None
    print("contours:", len(direct_result.contours))
    print("bounds:", direct_result.bounds)


if __name__ == "__main__":
    main()

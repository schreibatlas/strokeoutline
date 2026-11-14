from strokeoutline import Line, Path2D, Subpath, outline, signed_area, winding


def main():
    path = Path2D(
        (
            Subpath(
                (
                    Line((0, 0), (40, 0)),
                    Line((40, 0), (40, 30)),
                    Line((40, 30), (0, 30)),
                ),
                closed=True,
            ),
        )
    )
    result = outline(path, width=4.0)

    assert len(result.contours) == 2
    assert signed_area(result.contours[0]) * signed_area(result.contours[1]) < 0
    print("windings:", [winding(contour) for contour in result.contours])
    print("bounds:", result.bounds)


if __name__ == "__main__":
    main()

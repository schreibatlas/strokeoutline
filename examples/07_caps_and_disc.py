import math

from strokeoutline import Line, OutlineConfig, Path2D, Subpath, outline, outline_disc


def main():
    path = Path2D((Subpath((Line((0, 0), (10, 0)),)),))
    round_cap = outline(path, 2.0, config=OutlineConfig(cap="round"))
    square_cap = outline(path, 2.0, config=OutlineConfig(cap="square"))
    disc = outline_disc((15, 0), 6.0)

    assert round_cap.contours != square_cap.contours
    assert disc.contours[0][0] == disc.contours[0][-1]
    assert disc.bounds is not None
    assert all(math.isfinite(value) for value in disc.bounds)
    print("cap geometries differ:", round_cap.contours != square_cap.contours)
    print("disc bounds:", disc.bounds)


if __name__ == "__main__":
    main()

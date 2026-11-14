# SVG path adapter

The optional SVG adapter parses path data into StrokeOutline's neutral path model. It is not required for core geometry and is not an SVG renderer.

## Installation

```bash
python -m pip install 'strokeoutline[svg]'
```

## Parse and outline

```python
from strokeoutline.svg import outline_svg_path

result = outline_svg_path(
    "M 0 0 C 0 60 60 60 60 0",
    width=5.0,
)
```

To parse first and then choose how to outline:

```python
from strokeoutline import outline
from strokeoutline.svg import path_from_svg

path = path_from_svg("M 0 0 L 10 0")
result = outline(path, 2.0)
```

The adapter uses FontTools to normalize supported path commands into line, quadratic, and cubic segments. Regression-covered forms include relative coordinates, horizontal and vertical lines, smooth cubic and quadratic commands, arcs converted to cubic segments, close paths, and multiple subpaths. Unsupported operations or data that cannot be represented by the neutral model raise `ValueError`.

This tested set is not an exhaustive SVG compatibility matrix. The adapter parses geometry only. It does not implement SVG transforms, rendering, styles, complete CSS stroke semantics, or polygon cleanup.

## Dependency boundary

FontTools is imported only by `strokeoutline.svg`. Importing the core `strokeoutline` package does not require FontTools. StrokeOutline itself does not import InkGrammar.

## Aliases and migration

`strokeoutline.svg.expand_path` is a compatibility alias for `outline_svg_path`. New code should use the canonical name.

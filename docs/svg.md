# SVG path adapter

The optional SVG adapter parses path data into StrokeOutline's neutral path model. It is not required for core geometry.

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

The adapter supports SVG path operations that it can convert to the neutral line, quadratic, and cubic segment model. This is not a promise of complete SVG/CSS stroke rendering or an exhaustive command compatibility matrix.

## Dependency boundary

FontTools is imported only by `strokeoutline.svg`. Importing the core `strokeoutline` package does not require FontTools. StrokeOutline itself does not import InkGrammar.

## Aliases and migration

`strokeoutline.svg.expand_path` is a compatibility alias for `outline_svg_path`. New code should use the canonical name.

# SVG adapter API

> This module requires the optional `svg` extra and FontTools. Install it with `python -m pip install 'strokeoutline[svg]'`.

The adapter parses SVG path geometry into StrokeOutline's neutral path model, then returns the ordinary immutable `OutlineResult`. It does not render SVG or implement complete SVG/CSS stroke behavior. Regression-covered forms include relative coordinates, horizontal/vertical lines, smooth cubic/quadratic commands, arcs converted to cubic segments, close paths, and multiple subpaths. This is not an exhaustive command compatibility matrix.

`outline_svg_path()` accepts the same `width_parameterization` keyword as `outline()` and forwards it unchanged. The omitted keyword uses `config.width_parameterization`, which defaults to `"segment"`.

```{autofunction} strokeoutline.svg.path_from_svg

```

```{autofunction} strokeoutline.svg.outline_svg_path

```

`expand_path` is a compatibility alias of `outline_svg_path`:

```{autofunction} strokeoutline.svg.expand_path

```

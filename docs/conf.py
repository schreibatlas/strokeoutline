import sys
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent
ROOT = DOCS_DIR.parent
sys.path.insert(0, str(ROOT))

project = "strokeoutline"
author = "Holger Nahrstaedt"
copyright = "2026, Holger Nahrstaedt"
root_doc = "index"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

source_suffix = {".md": "markdown"}
myst_enable_extensions = ["colon_fence"]
myst_heading_anchors = 4

napoleon_google_docstring = False
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = False
napoleon_type_aliases = None
napoleon_attr_annotations = True

autodoc_member_order = "bysource"
autodoc_typehints = "description"
nitpicky = True
nitpick_ignore = [("py:class", "numpy.typing.ArrayLike")]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "README.md"]

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "navigation_depth": 4,
    "titles_only": False,
}

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
}

# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import sys
from pathlib import Path

sys.path.insert(0, (Path('..') / 'src').resolve())
p = Path()
print(f'DEBUG: {p.resolve()}')
print(f'DEBUG: {p.glob('*')}')


project = 'tinyecs'
copyright = '2026, Michael "Dicker Dackel" Lamertz'
author = 'Michael "Dicker Dackel" Lamertz'
release = '0.5.2a'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
html_theme_options = {
    "navigation_with_keys": True,
    "source_repository": "https://github.com/dickerdackel/tinyecs/",
    "source_branch": "main",
    "source_directory": "docs/source",
    "dark_css_variables": {
        "color-api-pre-name": "orange",
        "color-api-name": "orange",
    }
}

nitpicky = False

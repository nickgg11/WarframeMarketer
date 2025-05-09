# Configuration file for the Sphinx documentation builder.
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# -- Project information -----------------------------------------------------
project = 'Warframe Market API'
copyright = '2025, Nicholas Gingras'
author = 'Nicholas Gingras'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
html_theme = 'press'
html_static_path = ['_static']

# -- Extension configuration ------------------------------------------------
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'aiohttp': ('https://docs.aiohttp.org/en/stable/', None),
}

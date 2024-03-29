# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Cosmic View of Life'
copyright = '2023, Brian Abbott'
author = 'Brian Abbott'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import sys, os
sys.path.insert(0, os.path.abspath('../..'))
sys.path.insert(0, os.path.abspath('../../src'))
#sys.path.append(os.path.abspath('sphinxext'))


#extensions = ['myst_parser']
extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc'
]

templates_path = ['_templates']
exclude_patterns = []



# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_static_path = ['_static']

#html_theme = 'alabaster'
#html_permalinks_icon = '<span>#</span>'
html_theme = 'sphinxawesome_theme'
#extensions += ["sphinxawesome_theme.highlighting"]

html_css_files = 'css/custom.css'

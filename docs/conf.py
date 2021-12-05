#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime

import glQiwiApi

project = "glQiwiApi"
author = "GLEF1X"
copyright = f"{datetime.date.today().year}, {author}"
release = glQiwiApi.__version__

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]


html_theme = "furo"
html_logo = "_static/logo.png"
html_static_path = ["_static"]
todo_include_todos = True


extensions = [
    "notfound.extension",
    "sphinx.ext.autodoc",
    "sphinx.ext.autodoc.typehints",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinxcontrib.mermaid",
    'sphinxemoji.sphinxemoji'
]

htmlhelp_basename = project
html_theme_options = {}
html_css_files = [
    "stylesheets/extra.css",
]
highlight_language = 'python3'


rst_prolog = f"""
.. role:: pycode(code)
   :language: python3
"""

language = None
locale_dirs = ["locales"]

exclude_patterns = []
source_suffix = ".rst"
master_doc = "index"

# If true, '()' will be appended to :func: etc. cross-reference text.
add_function_parentheses = True

latex_documents = [
    (master_doc, f"{project}.tex", f"{project} Documentation", author, "manual"),
]

man_pages = [(master_doc, project, f"{project} Documentation", [author], 1)]

texinfo_documents = [
    (
        master_doc,
        project,
        f"{project} Documentation",
        author,
        project,
        "Modern and fully asynchronous framework for Telegram Bot API",
        "Miscellaneous",
    ),
]
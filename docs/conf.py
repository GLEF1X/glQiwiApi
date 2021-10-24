#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys

sys.path.insert(0, os.path.abspath("../."))

import datetime

import glQiwiApi

project = "glQiwiApi"
author = "GLEF1X and Marple"
copyright = f"{datetime.date.today().year}, {author}"
release = glQiwiApi.__version__

templates_path = ["_templates"]
html_theme = "furo"
html_logo = "static/logo.png"
html_static_path = ["static"]
todo_include_todos = True
pygments_style = "sphinx"
htmlhelp_basename = project
html_theme_options = {}
html_css_files = [
    "stylesheets/extra.css",
]
highlight_language = 'python3'

extensions = [
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx.ext.autodoc",
    "sphinx.ext.ifconfig",
    "sphinx.ext.intersphinx",
    "sphinx-prompt",
    "sphinx_substitution_extensions",
    "sphinx_copybutton",
    'sphinxemoji.sphinxemoji'
]

rst_prolog = f"""
.. role:: pycode(code)
   :language: python3
"""

language = None
locale_dirs = ["locales"]

exclude_patterns = []
source_suffix = ".rst"
master_doc = "index"

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
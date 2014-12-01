# -*- coding: utf-8 -*-

import sys
import os

try:
    import sphinx_rtd_theme
    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
except ImportError:
    pass

DOCDIR = os.path.abspath(os.path.dirname(__file__))
SRC_DIR = os.path.dirname(DOCDIR)
sys.path.append(SRC_DIR)

extensions = [
    'sphinx.ext.autodoc'
]

source_suffix = '.rst'

master_doc = 'index'

project = u'State Machine Crawler'
copyright = u'2014, Anton Berezin'

version = '3.0.0'
release = version
exclude_patterns = ['_build']
pygments_style = 'sphinx'
html_static_path = ['_static']
htmlhelp_basename = 'StateMachineCrawlerDoc'

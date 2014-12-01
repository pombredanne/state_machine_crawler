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
CHANGES_FILE = os.path.join(SRC_DIR, "CHANGES")

sys.path.append(SRC_DIR)

extensions = [
    'sphinx.ext.autodoc'
]

source_suffix = '.rst'

master_doc = 'index'

project = u'State Machine Crawler'
copyright = u'2014, Anton Berezin'

with open(CHANGES_FILE) as fil:
    version = fil.readline().split()[0]

release = version
exclude_patterns = ['_build']
pygments_style = 'sphinx'
htmlhelp_basename = 'StateMachineCrawlerDoc'

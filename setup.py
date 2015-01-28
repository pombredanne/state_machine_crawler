#!/usr/bin/python
import os

from setuptools import setup, find_packages

SRC_DIR = os.path.dirname(__file__)
CHANGES_FILE = os.path.join(SRC_DIR, "CHANGES")

with open(CHANGES_FILE) as fil:
    version = fil.readline().split()[0]


setup(
    name="state-machine-crawler",
    description="A library for following automata based programming model.",
    version=version,
    packages=find_packages(),
    setup_requires=["nose"],
    tests_require=["mock", "coverage"],
    install_requires=["werkzeug", "pydot2"],
    test_suite='nose.collector',
    author="Anton Berezin",
    author_email="gurunars@gmail.com",
    data_files=[
        ("/usr/share/state_machine_crawler", ["webview/index.html", "webview/jquery-2.1.3.min.js", "webview/viz.js"])
    ]
)

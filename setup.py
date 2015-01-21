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
    test_suite='nose.collector',
    install_requires=["pydot2"],
    author="Anton Berezin",
    author_email="gurunars@gmail.com"
)

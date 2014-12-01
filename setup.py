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
    author="Anton Berezin",
    author_email="gurunars@gmail.com"
)

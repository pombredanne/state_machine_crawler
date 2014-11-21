#!/bin/bash

version=`cat CHANGES | head -n1 | cut -f 1 -d " "`

sed -i "s/SOURCE_VERSION = .*/SOURCE_VERSION = \"$version\"/g" setup.py

#!/bin/bash


# https://nuitka.net/user-documentation/common-issue-solutions.html#dependency-creep-in-standalone
python -m nuitka \
    --onefile \
    --assume-yes-for-downloads \
    --report="${1%.*}_nuitka.xml" \
    --nofollow-import-to=numpy \
    --nofollow-import-to=pandas \
    --nofollow-import-to=pygments \
    --nofollow-import-to=mypy \
    --nofollow-import-to=rich \
    --nofollow-import-to=pydantic.v1 \
    --noinclude-pytest-mode=nofollow \
    --noinclude-setuptools-mode=nofollow \
    --noinclude-IPython-mode=nofollow \
    --noinclude-numba-mode=nofollow \
    --python-flag=no_asserts \
    --python-flag=no_docstrings \
    "$1"

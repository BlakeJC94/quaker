#!/usr/bin/env bash
# Generate requirements.txt
#
# Usage:
#     $ ./scripts/compile-requirements.sh
#
pip-compile \
    --annotation-style line \
    --extra dev \
    --output-file requirements-dev.txt \
    setup.py

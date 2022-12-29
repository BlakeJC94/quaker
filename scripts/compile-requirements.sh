#!/usr/bin/env bash
# Generate requirements.txt
#
# Usage:
#     $ ./scripts/compile-requirements.sh
#
pip-compile --annotation-style=line

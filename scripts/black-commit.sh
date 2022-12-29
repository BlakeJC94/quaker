#!/usr/bin/env bash
#

black ./**.py
git add .
git commit -m "chore: black"

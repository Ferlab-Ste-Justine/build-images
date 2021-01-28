#!/bin/bash
for FILENAME in $(pwd)/scripts/*.py; do
    if [ -f "$FILENAME" ] ; then
        pylint $FILENAME
    fi
done
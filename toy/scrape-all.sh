#!/bin/bash

# Usage: toy/scrape-all.sh (must be run from the repo's root)

set -eo pipefail

rm -rf out
mkdir out

for PYVER in "3.8" "3.9" "3.10" "3.11" "3.12"
do
    echo "py${PYVER}"
    docker build . -f toy/Dockerfile --build-arg "FROM=python:${PYVER}" -t ${PYVER}
    docker run --rm -it -e I8T_URL=https://api.demin.dev/i8t/toy-${PYVER} -v $PWD/out:/i8t/out ${PYVER}
    mv out/session-00.jsonl out/session-01-py${PYVER}.jsonl
done

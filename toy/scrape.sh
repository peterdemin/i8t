#!/bin/bash

set -eo pipefail

python toy/app.py &

sleep 3

curl 'http://127.0.0.1:5000/example?number=0'
curl 'http://127.0.0.1:5000/example?number=1'
curl 'http://127.0.0.1:5000/example?number=2'
curl 'http://127.0.0.1:5000/example?number=3'
curl 'http://127.0.0.1:5000/example?number=x'
curl 'http://127.0.0.1:5000/example?number=-1'

kill %%

i8t ${I8T_URL} > toy/testdata/session-00.jsonl

#!/bin/bash

set -eo pipefail

curl 'http://127.0.0.1:5000/example?number=0'
curl 'http://127.0.0.1:5000/example?number=1'
curl 'http://127.0.0.1:5000/example?number=2'
curl 'http://127.0.0.1:5000/example?number=3'
curl 'http://127.0.0.1:5000/example?number=x'
curl 'http://127.0.0.1:5000/example?number=-1'

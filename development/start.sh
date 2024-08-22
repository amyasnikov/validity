#!/bin/bash

DEBUG=$1
shift

if [[ $DEBUG == 1 ]]; then
    echo "!!! DEBUGGING IS ENABLED !!!"
    python -m debugpy --listen 0.0.0.0:5678 $@
else
    python $@
fi

#!/bin/bash

if [ ! -d ./venv ]; then
    ./make-venv.sh
fi

rm -f *.whl
./venv/bin/python3 -m pip wheel --no-deps .

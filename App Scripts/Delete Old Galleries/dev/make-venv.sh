#!/bin/bash

python3.9 -m venv ./venv
./venv/bin/pip install --upgrade pip

if [ `uname` == "Darwin" ]; then
    cp -r  /Applications/Baselight/Current/Utilities/Resources/share/flapi/python  /tmp/flapi
else
    cp -r /usr/fl/.current/share/flapi/python /tmp/flapi
fi
    
./venv/bin/pip install /tmp/flapi
rm -rf /tmp/flapi

./venv/bin/pip install .
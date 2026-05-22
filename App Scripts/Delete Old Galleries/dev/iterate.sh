#!/bin/bash

SYSTEM=`uname -s`

if [ -z "$PYINTERP" ]; then
    if [ "$SYSTEM" = "Linux" ]; then
        PYINTERP=`/usr/fl/baselight/bin/flici -e 'prefs=g3prefs.read_prefs(); printf( "%s\n", prefs.flapi_python_path);'`
    elif [ "$SYSTEM" = "Darwin" ]; then
        PYINTERP=`/Applications/Baselight/Current/Utilities/Tools/flici -e 'prefs=g3prefs.read_prefs(); printf( "%s\n", prefs.flapi_python_path);'`
    fi
fi

PYVER=`$PYINTERP -c 'import sys;vi=sys.version_info;print( f"{vi[0]}.{vi[1]}.{vi[2]}" )'`
if [ "$SYSTEM" = "Darwin" ]; then
    PYDIR=/Library/Application\ Support/FilmLight/python/$PYVER-venv
else
    PYVER=$PYVER-$(source /etc/os-release && echo ${ID}-${VERSION_ID})
    PYDIR=/usr/fl/python/$PYVER-venv
fi

echo "Interpreter ${PYINTERP} version ${PYVER}"
echo "Installing into ${PYDIR}"

# Make a new wheel
echo "Make filmlight_delete_old_galleries wheel"

LOG=/tmp/filmlight-delete_old_galleries-make-wheel.log
./make-wheel.sh > $LOG 2>&1 || (cat $LOG; exit 1)

# Uninstall previous version
echo "Uninstall previous filmlight_delete_old_galleries"

"$PYDIR/bin/pip" uninstall -y filmlight_delete_old_galleries

# Force reinstall it
echo "Install filmlight_delete_old_galleries wheel"

LOG=/tmp/filmlight-delete_old_galleries-install-wheel.log
"$PYDIR/bin/pip" install ./filmlight_delete_old_galleries-1.0.0-py3-none-any.whl > $LOG 2>&1 || (cat $LOG; exit 1)

# Ask Baselight to reload its scripts
echo "Reload Baselight scripts"
curl http://localhost:1985/reload-scripts

# Ask flapid to reload its scripts
echo "Reload flapid scripts"
curl http://localhost:1984/reload-scripts

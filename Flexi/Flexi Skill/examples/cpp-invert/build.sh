#!/bin/sh
# Builds ./flexi_invert with the system C++ compiler. On macOS the binary runs on Apple silicon and Intel Macs.
set -e
cd "$(dirname "$0")"

JSON_VERSION=3.11.3
JSON_SHA256=9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6
JSON=third_party/nlohmann/json.hpp
if [ ! -f "$JSON" ]; then
    mkdir -p "$(dirname "$JSON")"
    curl -fsSL -o "$JSON.part" "https://github.com/nlohmann/json/releases/download/v$JSON_VERSION/json.hpp"
    if command -v sha256sum >/dev/null 2>&1; then sum=$(sha256sum "$JSON.part"); else sum=$(shasum -a 256 "$JSON.part"); fi
    if [ "${sum%% *}" != "$JSON_SHA256" ]; then
        rm -f "$JSON.part"
        echo "json.hpp does not match its checksum" >&2
        exit 1
    fi
    mv "$JSON.part" "$JSON"
fi

case "$(uname -s)" in
    Darwin) FLAGS="-arch arm64 -arch x86_64 -mmacosx-version-min=11.0"; LIBS="" ;;
    *)      FLAGS="-static-libstdc++ -static-libgcc"; LIBS="-lrt" ;;
esac
${CXX:-c++} -std=c++17 -O2 -Wall $FLAGS -Ithird_party -o flexi_invert flexi_invert.cpp $LIBS
echo "built $(pwd)/flexi_invert"

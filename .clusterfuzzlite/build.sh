#!/bin/bash -eu

cd "$SRC/mouse-battery-tray"
compile_python_fuzzer fuzzing/packet_fuzzer.py --paths "$SRC/mouse-battery-tray/src"

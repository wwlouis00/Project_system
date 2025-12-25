#!/bin/bash
DIR="$HOME/eggi_release/socket_cam"

if [ ! -d "$DIR" ]; then
    mkdir -p "$DIR"
    echo "[$(date)] Created $DIR"
fi

cd "$DIR" && python3 -u main.pyc >> main.txt 2>&1
python3 -u main.pyc > main.txt

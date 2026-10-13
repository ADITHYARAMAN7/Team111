#!/usr/bin/env bash
# Rebuild the Word version:  bash docs/paper/word/build.sh
set -e
cd "$(dirname "$0")"
python tex2json.py
NODE_PATH="${NODE_PATH:-$(npm root -g)}" node build_docx.js
python finalize.py

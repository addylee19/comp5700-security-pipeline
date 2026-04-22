#!/usr/bin/env bash
set -euo pipefail

python -m PyInstaller --onefile --name comp5700_security_pipeline main.py

echo "Binary created under dist/comp5700_security_pipeline"

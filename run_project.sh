#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: ./run_project.sh <pdf1> <pdf2> [manifest_zip] [output_dir] [prompt_type]"
  exit 1
fi

PDF1="$1"
PDF2="$2"
MANIFEST_ZIP="${3:-project-yamls.zip}"
OUTPUT_DIR="${4:-outputs/manual_run}"
PROMPT_TYPE="${5:-zero-shot}"

python main.py "$PDF1" "$PDF2" --manifest-zip "$MANIFEST_ZIP" --output-dir "$OUTPUT_DIR" --prompt-type "$PROMPT_TYPE"

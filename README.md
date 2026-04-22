# COMP 5700 Security Requirements Project

## Team Information
- Name: Addy Lee
- Email: arl0078@auburn.edu

## LLM Used
- `google/gemma-3-1b-it`

## What the Project Does
This project compares two security requirements PDFs, extracts key data elements (KDEs) using Gemma 3 1B, compares the resulting YAML files, maps differences to Kubescape controls, scans the provided Kubernetes YAML repository, and exports the scan results to CSV.

## Repository Layout
```text
project/
├── extractor.py
├── comparator.py
├── executor.py
├── main.py
├── run_all_pairs.py
├── PROMPT.md
├── requirements.txt
├── build_binary.sh
├── run_project.sh
├── .github/workflows/tests.yml
└── tests/

## Setup
python3 -m venv comp5700-venv
source comp5700-venv/bin/activate
pip install -r requirements.txt

## Example run
python main.py cis-r1.pdf cis-r2.pdf --manifest-zip project-yamls.zip --output-dir outputs/cis-r1_vs_cis-r2 --prompt-type zero-shot

## Run all 9 inputs
python run_all_pairs.py

## Build binary
bash build_binary.sh
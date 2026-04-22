from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Sequence

import pandas as pd


KEYWORD_TO_CONTROL = {
    # Identity / privilege / service accounts
    "secret": "C-0015",
    "credential": "C-0012",
    "password": "C-0012",
    "service account": "C-0260",
    "token": "C-0012",
    "privilege": "C-0189",
    "privileged": "C-0050",
    "root": "C-0013",
    # Images / supply chain
    "image": "C-0001",
    "registry": "C-0001",
    "latest tag": "C-0127",
    # Networking / exposure
    "network": "C-0048",
    "ingress": "C-0041",
    "port": "C-0005",
    # Resources / health
    "limit": "C-0009",
    "memory": "C-0004",
    "cpu": "C-0009",
    "probe": "C-0049",
    # Pods / containers
    "capability": "C-0002",
    "hostpath": "C-0044",
    "host network": "C-0030",
    "readonly": "C-0017",
}


# -----------------------------
# Task 3 Function 1
# -----------------------------
def load_difference_files(name_diff_file: str, requirement_diff_file: str) -> Dict[str, str]:
    return {
        "name_differences": Path(name_diff_file).read_text(encoding="utf-8"),
        "requirement_differences": Path(requirement_diff_file).read_text(encoding="utf-8"),
    }


# -----------------------------
# Task 3 Function 2
# -----------------------------
def map_differences_to_controls(
    name_diff_file: str,
    requirement_diff_file: str,
    output_txt: str,
) -> List[str]:
    diff_data = load_difference_files(name_diff_file, requirement_diff_file)
    merged_text = (diff_data["name_differences"] + "\n" + diff_data["requirement_differences"]).lower()

    no_name_diffs = "NO DIFFERENCES IN REGARDS TO ELEMENT NAMES" in diff_data["name_differences"]
    no_req_diffs = "NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS" in diff_data["requirement_differences"]

    controls: List[str] = []
    if not (no_name_diffs and no_req_diffs):
        for keyword, control in KEYWORD_TO_CONTROL.items():
            if keyword in merged_text and control not in controls:
                controls.append(control)

    out_path = Path(output_txt)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as handle:
        if no_name_diffs and no_req_diffs:
            handle.write("NO DIFFERENCES FOUND\n")
            return []

        if not controls:
            # Fallback when there are differences but no keyword matched.
            controls = ["C-0001", "C-0009", "C-0012", "C-0013"]

        handle.write("\n".join(controls) + "\n")
    return controls


# -----------------------------
# Task 3 Function 3
# -----------------------------
def execute_kubescape_scan(
    controls_txt: str,
    manifest_zip_path: str,
    extracted_dir: str,
    results_json_path: str,
) -> pd.DataFrame:

    controls_text = Path(controls_txt).read_text(encoding="utf-8").strip()

    extract_project_yamls(manifest_zip_path, extracted_dir)

    if not shutil.which("kubescape"):
        raise FileNotFoundError(
            "kubescape CLI was not found in PATH. Install it before running Task 3."
        )

    # Parse controls list
    controls = []
    if controls_text and controls_text != "NO DIFFERENCES FOUND":
        controls = [line.strip() for line in controls_text.splitlines() if line.strip()]

    # Build correct command (NEW Kubescape syntax)
    command = [
        "kubescape",
        "scan",
    ]

    if controls:
        command.extend(["control", ",".join(controls)])

    command.extend([
        extracted_dir,
        "--format", "json",
        "--output", results_json_path,
    ])

    subprocess.run(command, check=True, text=True)

    return kubescape_json_to_dataframe(results_json_path)


def extract_project_yamls(zip_path: str, output_dir: str) -> None:
    out = Path(output_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(out)



def kubescape_json_to_dataframe(results_json_path: str) -> pd.DataFrame:
    """
    Parse Kubescape JSON as defensively as possible because exact nesting can vary.
    """
    data = json.loads(Path(results_json_path).read_text(encoding="utf-8"))

    rows: List[Dict[str, object]] = []

    # v2-style flattened summary if available
    summaries = data.get("summaryDetails") or data.get("results") or []
    if isinstance(summaries, list):
        for item in summaries:
            if not isinstance(item, dict):
                continue
            rows.append(
                {
                    "FilePath": item.get("filePath") or item.get("path") or "N/A",
                    "Severity": item.get("severity") or item.get("scoreFactor") or "Unknown",
                    "Control name": item.get("name") or item.get("controlName") or item.get("controlID") or "Unknown",
                    "Failed resources": item.get("failedResources") or item.get("failedResourcesCount") or 0,
                    "All Resources": item.get("allResources") or item.get("allResourcesCount") or 0,
                    "Compliance score": item.get("complianceScore") or item.get("score") or "N/A",
                }
            )

    # fallback for controlReports / nested structures
    if not rows:
        reports = data.get("controlReports") or data.get("controlSummaries") or []
        for report in reports:
            if not isinstance(report, dict):
                continue
            rows.append(
                {
                    "FilePath": report.get("filePath") or report.get("baseObject", {}).get("path", "N/A"),
                    "Severity": report.get("severity") or "Unknown",
                    "Control name": report.get("name") or report.get("controlName") or report.get("controlID") or "Unknown",
                    "Failed resources": report.get("failedResources") or report.get("failedResourcesCount") or 0,
                    "All Resources": report.get("allResources") or report.get("allResourcesCount") or 0,
                    "Compliance score": report.get("complianceScore") or report.get("score") or "N/A",
                }
            )

    return pd.DataFrame(
        rows,
        columns=[
            "FilePath",
            "Severity",
            "Control name",
            "Failed resources",
            "All Resources",
            "Compliance score",
        ],
    )


# -----------------------------
# Task 3 Function 4
# -----------------------------
def save_scan_results_csv(scan_df: pd.DataFrame, output_csv: str) -> None:
    required_columns = [
        "FilePath",
        "Severity",
        "Control name",
        "Failed resources",
        "All Resources",
        "Compliance score",
    ]
    missing = [col for col in required_columns if col not in scan_df.columns]
    if missing:
        raise ValueError(f"DataFrame is missing required columns: {missing}")
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)
    scan_df.to_csv(output_csv, index=False)

import json
from pathlib import Path

import pandas as pd
import zipfile

from executor import (
    extract_project_yamls,
    kubescape_json_to_dataframe,
    load_difference_files,
    map_differences_to_controls,
    save_scan_results_csv,
)


def test_load_difference_files(tmp_path: Path):
    a = tmp_path / "a.txt"
    b = tmp_path / "b.txt"
    a.write_text("hello", encoding="utf-8")
    b.write_text("world", encoding="utf-8")
    result = load_difference_files(str(a), str(b))
    assert result["name_differences"] == "hello"
    assert result["requirement_differences"] == "world"


def test_map_differences_to_controls(tmp_path: Path):
    names = tmp_path / "names.txt"
    reqs = tmp_path / "reqs.txt"
    out = tmp_path / "controls.txt"
    names.write_text("password\n", encoding="utf-8")
    reqs.write_text("secret\n", encoding="utf-8")
    controls = map_differences_to_controls(str(names), str(reqs), str(out))
    assert controls
    assert out.exists()


def test_kubescape_json_to_dataframe_and_csv(tmp_path: Path):
    json_path = tmp_path / "results.json"
    json_path.write_text(
        json.dumps(
            {
                "summaryDetails": [
                    {
                        "filePath": "demo.yaml",
                        "severity": "High",
                        "name": "Non-root containers",
                        "failedResources": 2,
                        "allResources": 5,
                        "complianceScore": 60,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    df = kubescape_json_to_dataframe(str(json_path))
    assert list(df.columns) == [
        "FilePath",
        "Severity",
        "Control name",
        "Failed resources",
        "All Resources",
        "Compliance score",
    ]
    csv_path = tmp_path / "report.csv"
    save_scan_results_csv(df, str(csv_path))
    assert csv_path.exists()


def test_extract_project_yamls(tmp_path: Path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.yaml").write_text("kind: Pod\n", encoding="utf-8")
    zip_path = tmp_path / "manifests.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(src_dir / "a.yaml", arcname="a.yaml")
    out_dir = tmp_path / "out"
    extract_project_yamls(str(zip_path), str(out_dir))
    assert (out_dir / "a.yaml").exists()

from pathlib import Path

import yaml

from comparator import compare_kde_names, compare_kde_names_and_requirements, load_yaml_files


def _write_yaml(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_load_yaml_files(tmp_path: Path):
    left = tmp_path / "left.yaml"
    right = tmp_path / "right.yaml"
    _write_yaml(left, {"element1": {"name": "password", "requirements": ["req1"]}})
    _write_yaml(right, {"element1": {"name": "token", "requirements": ["req2"]}})
    l, r = load_yaml_files(str(left), str(right))
    assert l["element1"]["name"] == "password"
    assert r["element1"]["name"] == "token"


def test_compare_kde_names(tmp_path: Path):
    left = tmp_path / "left.yaml"
    right = tmp_path / "right.yaml"
    out = tmp_path / "names.txt"
    _write_yaml(left, {"element1": {"name": "password", "requirements": ["req1"]}})
    _write_yaml(right, {"element1": {"name": "token", "requirements": ["req2"]}})
    diffs = compare_kde_names(str(left), str(right), str(out))
    assert "password" in diffs and "token" in diffs
    assert out.exists()


def test_compare_kde_names_and_requirements(tmp_path: Path):
    left = tmp_path / "left.yaml"
    right = tmp_path / "right.yaml"
    out = tmp_path / "reqs.txt"
    _write_yaml(left, {"element1": {"name": "password", "requirements": ["req1", "req2"]}})
    _write_yaml(right, {"element1": {"name": "password", "requirements": ["req2", "req3"]}})
    tuples = compare_kde_names_and_requirements(str(left), str(right), str(out))
    assert any("req1" in line for line in tuples)
    assert any("req3" in line for line in tuples)
    assert out.exists()

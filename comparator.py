from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Set, Tuple

import yaml


# -----------------------------
# Task 2 Function 1
# -----------------------------
def load_yaml_files(file_1: str, file_2: str) -> Tuple[Dict, Dict]:
    with open(file_1, "r", encoding="utf-8") as handle:
        left = yaml.safe_load(handle) or {}
    with open(file_2, "r", encoding="utf-8") as handle:
        right = yaml.safe_load(handle) or {}
    return left, right


# -----------------------------
# Task 2 Function 2
# -----------------------------
def compare_kde_names(file_1: str, file_2: str, output_txt: str) -> List[str]:
    left, right = load_yaml_files(file_1, file_2)
    left_names = _collect_names(left)
    right_names = _collect_names(right)

    differences = sorted((left_names - right_names) | (right_names - left_names))
    out_path = Path(output_txt)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as handle:
        if not differences:
            handle.write("NO DIFFERENCES IN REGARDS TO ELEMENT NAMES\n")
        else:
            handle.write("\n".join(differences) + "\n")
    return differences


# -----------------------------
# Task 2 Function 3
# -----------------------------
def compare_kde_names_and_requirements(
    file_1: str, file_2: str, output_txt: str
) -> List[str]:
    left, right = load_yaml_files(file_1, file_2)

    left_map = _name_to_requirements_map(left)
    right_map = _name_to_requirements_map(right)

    left_filename = Path(file_1).name
    right_filename = Path(file_2).name

    all_names = sorted(set(left_map) | set(right_map))
    tuples: List[str] = []

    for name in all_names:
        in_left = name in left_map
        in_right = name in right_map

        if in_left and not in_right:
            tuples.append(f"{name},PRESENT-IN-{left_filename},ABSENT-IN-{right_filename},NA")
            continue
        if in_right and not in_left:
            tuples.append(f"{name},ABSENT-IN-{left_filename},PRESENT-IN-{right_filename},NA")
            continue

        left_reqs = left_map[name]
        right_reqs = right_map[name]
        for req in sorted(left_reqs - right_reqs):
            tuples.append(
                f"{name},PRESENT-IN-{left_filename},ABSENT-IN-{right_filename},{req}"
            )
        for req in sorted(right_reqs - left_reqs):
            tuples.append(
                f"{name},ABSENT-IN-{left_filename},PRESENT-IN-{right_filename},{req}"
            )

    out_path = Path(output_txt)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as handle:
        if not tuples:
            handle.write("NO DIFFERENCES IN REGARDS TO ELEMENT REQUIREMENTS\n")
        else:
            handle.write("\n".join(tuples) + "\n")
    return tuples



def _collect_names(yaml_data: Dict) -> Set[str]:
    names = set()
    for value in (yaml_data or {}).values():
        if isinstance(value, dict) and value.get("name"):
            names.add(str(value["name"]).strip())
    return names



def _name_to_requirements_map(yaml_data: Dict) -> Dict[str, Set[str]]:
    result: Dict[str, Set[str]] = {}
    for value in (yaml_data or {}).values():
        if isinstance(value, dict) and value.get("name"):
            name = str(value["name"]).strip()
            reqs = {str(req).strip() for req in value.get("requirements", []) if str(req).strip()}
            result[name] = reqs
    return result

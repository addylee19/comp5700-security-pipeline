from __future__ import annotations

import argparse
from pathlib import Path

from comparator import compare_kde_names, compare_kde_names_and_requirements
from executor import execute_kubescape_scan, map_differences_to_controls, save_scan_results_csv
from extractor import identify_key_data_elements, load_documents


DEFAULT_PROMPT_TYPES = ["zero-shot", "few-shot", "chain-of-thought"]


def run_pipeline(
    pdf_1: str,
    pdf_2: str,
    manifest_zip: str,
    output_dir: str,
    prompt_type: str = "zero-shot",
) -> None:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    text_1, text_2 = load_documents(pdf_1, pdf_2)

    base_1 = Path(pdf_1).stem
    base_2 = Path(pdf_2).stem

    llm_log = out / "llm_outputs.txt"
    yaml_1 = out / f"{base_1}-kdes.yaml"
    yaml_2 = out / f"{base_2}-kdes.yaml"

    identify_key_data_elements(text_1, prompt_type, str(yaml_1), str(llm_log))
    identify_key_data_elements(text_2, prompt_type, str(yaml_2), str(llm_log))

    names_txt = out / f"{base_1}_vs_{base_2}_name_differences.txt"
    reqs_txt = out / f"{base_1}_vs_{base_2}_requirement_differences.txt"
    controls_txt = out / f"{base_1}_vs_{base_2}_controls.txt"
    results_json = out / f"{base_1}_vs_{base_2}_kubescape.json"
    results_csv = out / f"{base_1}_vs_{base_2}_kubescape.csv"
    extracted_dir = out / "extracted_yamls"

    compare_kde_names(str(yaml_1), str(yaml_2), str(names_txt))
    compare_kde_names_and_requirements(str(yaml_1), str(yaml_2), str(reqs_txt))
    map_differences_to_controls(str(names_txt), str(reqs_txt), str(controls_txt))
    scan_df = execute_kubescape_scan(str(controls_txt), manifest_zip, str(extracted_dir), str(results_json))
    save_scan_results_csv(scan_df, str(results_csv))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="COMP 5700 security requirements pipeline")
    parser.add_argument("pdf_1", help="Path to first PDF")
    parser.add_argument("pdf_2", help="Path to second PDF")
    parser.add_argument(
        "--manifest-zip",
        default="project-yamls.zip",
        help="Path to project-yamls.zip",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory to store generated files",
    )
    parser.add_argument(
        "--prompt-type",
        choices=DEFAULT_PROMPT_TYPES,
        default="zero-shot",
        help="Prompt type used for KDE extraction",
    )
    args = parser.parse_args()
    run_pipeline(
        args.pdf_1,
        args.pdf_2,
        manifest_zip=args.manifest_zip,
        output_dir=args.output_dir,
        prompt_type=args.prompt_type,
    )

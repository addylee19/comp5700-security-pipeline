from __future__ import annotations

from itertools import combinations_with_replacement
from pathlib import Path

from main import run_pipeline


PDFS = ["cis-r1.pdf", "cis-r2.pdf", "cis-r3.pdf", "cis-r4.pdf"]


def main() -> None:
    manifest_zip = "project-yamls.zip"
    all_pairs = [
        ("cis-r1.pdf", "cis-r1.pdf"),
        ("cis-r1.pdf", "cis-r2.pdf"),
        ("cis-r1.pdf", "cis-r3.pdf"),
        ("cis-r1.pdf", "cis-r4.pdf"),
        ("cis-r2.pdf", "cis-r2.pdf"),
        ("cis-r2.pdf", "cis-r3.pdf"),
        ("cis-r2.pdf", "cis-r4.pdf"),
        ("cis-r3.pdf", "cis-r3.pdf"),
        ("cis-r3.pdf", "cis-r4.pdf"),
    ]

    for left, right in all_pairs:
        pair_name = f"{Path(left).stem}_vs_{Path(right).stem}"
        out_dir = Path("outputs") / pair_name
        run_pipeline(left, right, manifest_zip=manifest_zip, output_dir=str(out_dir))
        print(f"Completed {pair_name}")


if __name__ == "__main__":
    main()

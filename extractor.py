from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Tuple

import yaml

try:
    import requests
except ImportError:  # pragma: no cover
    requests = None

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover
    PdfReader = None

try:
    import torch
    from transformers import pipeline
except ImportError:  # pragma: no cover
    torch = None
    pipeline = None


LLM_NAME = "google/gemma-3-1b-it"


class ExtractionError(Exception):
    """Raised when extraction input or output is invalid."""


_PIPE = None


def get_llm_pipeline(device: str = "cpu"):
    """Create or reuse the Gemma text-generation pipeline lazily."""
    global _PIPE
    if _PIPE is None:
        if pipeline is None or torch is None:
            raise ImportError(
                "transformers and torch must be installed to run Gemma extraction."
            )

        dtype = torch.bfloat16 if device == "cpu" else torch.float16

        _PIPE = pipeline(
            "text-generation",
            model=LLM_NAME,
            device=device,
            torch_dtype=dtype,
        )
    return _PIPE


# -----------------------------
# Task 1 Function 1
# -----------------------------
def load_document_text(document_path_or_url: str) -> str:
    """Validate and load a PDF document from a local path or URL."""
    if not isinstance(document_path_or_url, str) or not document_path_or_url.strip():
        raise ExtractionError("Document path/URL must be a non-empty string.")

    source = document_path_or_url.strip()

    if source.startswith("http://") or source.startswith("https://"):
        if requests is None:
            raise ImportError("requests must be installed to load remote PDFs.")

        response = requests.get(source, timeout=60)
        response.raise_for_status()

        tmp_path = Path("_temp_downloaded_document.pdf")
        tmp_path.write_bytes(response.content)
        try:
            text = _read_pdf_text(tmp_path)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()
        return text

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Document not found: {path}")
    if path.suffix.lower() != ".pdf":
        raise ExtractionError(f"Expected a PDF file, got: {path.name}")

    return _read_pdf_text(path)


def load_documents(document_1: str, document_2: str) -> Tuple[str, str]:
    """Load two PDFs and return their extracted text."""
    return load_document_text(document_1), load_document_text(document_2)


def _read_pdf_text(path: Path) -> str:
    """Read extractable text from a PDF."""
    if PdfReader is None:
        raise ImportError("pypdf must be installed to read PDF files.")

    reader = PdfReader(str(path))
    pages = [page.extract_text() or "" for page in reader.pages]
    text = "\n".join(pages).strip()

    if not text:
        raise ExtractionError(f"No extractable text found in {path.name}")

    return text


# -----------------------------
# Task 1 Functions 2-4
# -----------------------------
def build_zero_shot_prompt(document_text: str) -> str:
    shortened = _prepare_document_text_for_prompt(document_text)
    return f"""
You are a security requirements analyst.

Extract key data elements (KDEs) and their associated requirements.
Return YAML only in this exact structure.

STRICT RULES:
- Output ONLY valid YAML
- Do NOT include explanations
- Do NOT include backticks
- Do NOT include text before or after YAML
- Follow the structure EXACTLY

FORMAT:
element1:
  name: <short name>
  requirements:
    - <requirement sentence>
element2:
  name: <short name>
  requirements:
    - <requirement sentence>

Document:
{shortened}
""".strip()


def build_few_shot_prompt(document_text: str) -> str:
    shortened = _prepare_document_text_for_prompt(document_text)
    return f"""
You are a security requirements analyst.

Extract key data elements (KDEs) and the requirements that mention them.
A KDE can map to more than one requirement.

Example:
Input snippet:
"Passwords must be rotated every 90 days. Password history must be preserved."

Example YAML output:
element1:
  name: password
  requirements:
    - Passwords must be rotated every 90 days.
    - Password history must be preserved.

Now analyze the document below and return YAML only in the same structure.

Document:
{shortened}
""".strip()


def build_chain_of_thought_prompt(document_text: str) -> str:
    shortened = _prepare_document_text_for_prompt(document_text)
    return f"""
You are a security requirements analyst.

Do the reasoning internally to identify:
1. important security entities or data concepts,
2. which requirements mention each concept,
3. whether multiple requirements map to the same KDE.

Do not show your reasoning.
Output ONLY final YAML in this exact structure:
element1:
  name: <kde name>
  requirements:
    - <requirement text>
    - <requirement text>
element2:
  name: <kde name>
  requirements:
    - <requirement text>

Document:
{shortened}
""".strip()


def _prepare_document_text_for_prompt(document_text: str, max_chars: int = 12000) -> str:
    """Trim very long PDFs so CPU inference doesn't crawl forever."""
    text = (document_text or "").strip()
    return text[:max_chars]


# -----------------------------
# Task 1 Functions 5-6
# -----------------------------
def identify_key_data_elements(
    document_text: str,
    prompt_type: str,
    output_yaml_path: str,
    llm_output_log_path: str,
    device: str = "cpu",
) -> Dict[str, Any]:
    """
    Run Gemma with one of the supported prompt types and save the YAML output.
    Always writes the raw LLM output log even if parsing fails.
    """
    prompt_builders = {
        "zero-shot": build_zero_shot_prompt,
        "few-shot": build_few_shot_prompt,
        "chain-of-thought": build_chain_of_thought_prompt,
    }

    if prompt_type not in prompt_builders:
        raise ExtractionError(f"Unsupported prompt type: {prompt_type}")

    prompt = prompt_builders[prompt_type](document_text)
    llm = get_llm_pipeline(device=device)

    raw_output = llm(
        prompt,
        max_new_tokens=250,
        do_sample=False,
    )

    generated_text = _extract_generated_text(raw_output)

    append_llm_output_log(
        llm_name=LLM_NAME,
        prompt_used=prompt,
        prompt_type=prompt_type,
        llm_output=generated_text,
        output_path=llm_output_log_path,
    )

    try:
        parsed = _parse_yaml_like_output(generated_text)
    except Exception as exc:
        parsed = {
            "element1": {
                "name": "PARSE_ERROR",
                "requirements": [f"Parser failure: {exc}"],
            }
        }

    save_yaml(parsed, output_yaml_path)
    return parsed


def save_yaml(data: Dict[str, Any], output_yaml_path: str) -> None:
    """Write KDE dictionary to YAML."""
    out_path = Path(output_yaml_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False, allow_unicode=True)


def append_llm_output_log(
    llm_name: str,
    prompt_used: str,
    prompt_type: str,
    llm_output: str,
    output_path: str,
) -> None:
    """Append one formatted LLM run to the text log."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("a", encoding="utf-8") as handle:
        handle.write("*LLM Name*\n")
        handle.write(f"{llm_name}\n\n")
        handle.write("*Prompt Used*\n")
        handle.write(f"{prompt_used}\n\n")
        handle.write("*Prompt Type*\n")
        handle.write(f"{prompt_type}\n\n")
        handle.write("*LLM Output*\n")
        handle.write(f"{llm_output}\n\n")
        handle.write("=" * 80 + "\n\n")


def _extract_generated_text(raw_output: Any) -> str:
    """Handle common transformers pipeline output shapes."""
    if isinstance(raw_output, list) and raw_output:
        first = raw_output[0]

        if isinstance(first, dict):
            if "generated_text" in first:
                return str(first["generated_text"])
            if "text" in first:
                return str(first["text"])

        if isinstance(first, list) and first:
            inner = first[0]
            if isinstance(inner, dict) and "generated_text" in inner:
                return str(inner["generated_text"])

    return str(raw_output)


def _parse_yaml_like_output(text: str) -> Dict[str, Any]:
    cleaned = (text or "").strip()
    cleaned = re.sub(r"^```(?:yaml)?\\s*", "", cleaned)
    cleaned = re.sub(r"\\s*```$", "", cleaned).strip()

    match = re.search(r"(element1:.*)", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(1).strip()

    parsed = None
    try:
        parsed = yaml.safe_load(cleaned)
    except yaml.YAMLError:
        parsed = None

    if parsed is not None:
        normalized = _normalize_kde_structure(parsed)
        if normalized:
            return normalized

    fallback = _fallback_extract_kdes_from_text(cleaned)
    if fallback:
        return fallback

    return {
    "element1": {
        "name": "security_requirement",
        "requirements": [text[:200]] if text else [],
    }
}

def _fallback_extract_kdes_from_text(text: str) -> Dict[str, Any]:
    lines = [line.strip("-• \t") for line in text.splitlines() if line.strip()]
    req_lines = [
        line for line in lines
        if len(line) > 20 and any(ch.isalpha() for ch in line)
    ]

    if not req_lines:
        return {}

    keywords = [
        "password", "authentication", "authorization", "access control",
        "encryption", "audit", "logging", "network", "container",
        "privilege", "secret", "certificate", "account", "session",
        "backup", "integrity", "availability", "monitoring"
    ]

    result = {}
    idx = 1
    for keyword in keywords:
        matched = [line for line in req_lines if keyword in line.lower()]
        if matched:
            result[f"element{idx}"] = {
                "name": keyword,
                "requirements": matched[:5],
            }
            idx += 1

    if result:
        return result

    return {
        "element1": {
            "name": "security_requirement",
            "requirements": req_lines[:5],
        }
    }

def _normalize_kde_structure(parsed: Any) -> Dict[str, Any]:
    """
    Accept either:
    1) dict keyed by element ids, or
    2) list of single-key dictionaries.
    """
    result: Dict[str, Any] = {}

    if isinstance(parsed, dict):
        for key, value in parsed.items():
            if isinstance(value, dict):
                result[str(key)] = {
                    "name": str(value.get("name", "")).strip(),
                    "requirements": _normalize_requirements(value.get("requirements", [])),
                }
        return result

    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, dict):
                        result[str(key)] = {
                            "name": str(value.get("name", "")).strip(),
                            "requirements": _normalize_requirements(value.get("requirements", [])),
                        }
        return result

    return result


def _normalize_requirements(requirements: Any) -> list[str]:
    """Normalize requirements into a clean list of strings."""
    if requirements is None:
        return []

    if isinstance(requirements, list):
        return [str(req).strip() for req in requirements if str(req).strip()]

    if isinstance(requirements, str):
        return [requirements.strip()] if requirements.strip() else []

    return [str(requirements).strip()]

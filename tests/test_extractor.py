from pathlib import Path

import pytest
import yaml

from extractor import (
    append_llm_output_log,
    build_chain_of_thought_prompt,
    build_few_shot_prompt,
    build_zero_shot_prompt,
    identify_key_data_elements,
    save_yaml,
)


def test_build_zero_shot_prompt_contains_document_text():
    prompt = build_zero_shot_prompt("sample requirement text")
    assert "sample requirement text" in prompt
    assert "Return YAML only" in prompt


def test_build_few_shot_prompt_contains_example():
    prompt = build_few_shot_prompt("abc")
    assert "Example YAML output" in prompt
    assert "abc" in prompt


def test_build_chain_of_thought_prompt_contains_internal_reasoning_instruction():
    prompt = build_chain_of_thought_prompt("xyz")
    assert "Do the reasoning internally" in prompt
    assert "xyz" in prompt


def test_save_yaml_writes_dictionary(tmp_path: Path):
    out = tmp_path / "kdes.yaml"
    data = {"element1": {"name": "password", "requirements": ["req1"]}}
    save_yaml(data, str(out))
    loaded = yaml.safe_load(out.read_text())
    assert loaded["element1"]["name"] == "password"


def test_append_llm_output_log_writes_expected_sections(tmp_path: Path):
    out = tmp_path / "llm.txt"
    append_llm_output_log("gemma", "prompt", "zero-shot", "output", str(out))
    text = out.read_text()
    assert "*LLM Name*" in text
    assert "*Prompt Used*" in text
    assert "*Prompt Type*" in text
    assert "*LLM Output*" in text


def test_identify_key_data_elements_with_mocked_pipeline(monkeypatch, tmp_path: Path):
    yaml_out = tmp_path / "out.yaml"
    log_out = tmp_path / "log.txt"

    class FakePipeline:
        def __call__(self, prompt, max_new_tokens=0, do_sample=False):
            return [{"generated_text": "element1:\n  name: password\n  requirements:\n    - rotate passwords"}]

    monkeypatch.setattr("extractor.get_llm_pipeline", lambda device="cpu": FakePipeline())
    result = identify_key_data_elements(
        "doc text",
        "zero-shot",
        str(yaml_out),
        str(log_out),
    )
    assert result["element1"]["name"] == "password"
    assert yaml_out.exists()
    assert log_out.exists()
